from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db, User, Document, Ontology, UserSettings
from models.ontologies import (
    OntologyCreateRequest, OntologyUpdateRequest, OntologyResponse, 
    OntologyDetailResponse, OntologyTriple
)
from auth.security import get_current_user
from utils.ai_agents import create_ontology_from_document

router = APIRouter()

@router.post("/", response_model=OntologyResponse)
async def create_ontology(
    ontology_data: OntologyCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if document exists and belongs to user
    document = db.query(Document).filter(
        Document.id == ontology_data.document_id,
        Document.user_id == current_user.id,
        Document.status == "completed"
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not processed yet"
        )
    
    # Create ontology record
    ontology = Ontology(
        user_id=current_user.id,
        document_id=ontology_data.document_id,
        name=ontology_data.name,
        description=ontology_data.description,
        status="processing",
        triples=[]
    )
    
    db.add(ontology)
    db.commit()
    db.refresh(ontology)
    
    # Process ontology creation in background
    background_tasks.add_task(
        process_ontology_creation,
        ontology.id,
        document.content_text,
        current_user.id,
        db
    )
    
    return OntologyResponse.model_validate(ontology)

def process_ontology_creation(ontology_id: str, document_text: str, user_id: str, db: Session):
    """Background task to process ontology creation with AI"""
    print(f"[ONTOLOGY] Starting background processing for ontology {ontology_id}")
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get ontology record
        ontology = db.query(Ontology).filter(Ontology.id == ontology_id).first()
        if not ontology:
            return
        
        # Initialize progress tracking
        ontology.status = "processing"
        ontology.ontology_metadata = {
            "total_chunks": 1,
            "processed_chunks": 0,
            "current_chunk": 0,
            "chunk_progress": [],
            "document_length": len(document_text),
            "processing_mode": "standard"
        }
        db.commit()
        print(f"[ONTOLOGY] Updated status to processing for {ontology_id}")
        
        # Determine if chunked processing is needed
        from config import get_settings
        settings = get_settings()
        
        if len(document_text) > 8000:
            # Get user settings for chunk parameters
            user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            chunk_size = user_settings.default_chunk_size if user_settings else 1000
            overlap_percentage = user_settings.default_overlap_percentage if user_settings else 10
            
            # Calculate number of chunks for progress tracking
            from utils.file_processor import chunk_text
            chunks = chunk_text(document_text, chunk_size, overlap_percentage)
            
            # Update metadata for chunked processing
            metadata = ontology.ontology_metadata.copy()
            metadata.update({
                "total_chunks": len(chunks),
                "chunk_progress": [{"status": "pending"} for _ in range(len(chunks))],
                "processing_mode": "chunked"
            })
            ontology.ontology_metadata = metadata
            db.commit()
            print(f"[ONTOLOGY] Using chunked processing with {len(chunks)} chunks")
        
        # Process with AI agent
        from utils.ai_agents import OntologyCreationAgent
        from config import get_settings
        settings = get_settings()
        agent = OntologyCreationAgent()
        
        # Use chunked processing with database tracking for large documents
        if len(document_text) > 8000:
            # Get user settings for chunk parameters
            user_settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
            chunk_size = user_settings.default_chunk_size if user_settings else 1000
            overlap_percentage = user_settings.default_overlap_percentage if user_settings else 10
            
            result = agent.process_chunked_ontology(document_text, ontology.document_id, user_id, 
                                                  chunk_size=chunk_size, overlap_percentage=overlap_percentage,
                                                  db_session=db, ontology_id=ontology_id)
        else:
            result = agent.process(document_text, ontology.document_id, user_id)
        
        if result["status"] == "ontology_created":
            # Convert AI result to OntologyTriple format
            triples_data = []
            for triple in result["ontology_triples"]:
                triples_data.append({
                    "subject": triple["subject"],
                    "relationship": triple["relationship"],
                    "object": triple["object"]
                })
            
            ontology.triples = triples_data
            ontology.status = "active"
            ontology.updated_at = datetime.utcnow()
            
            # Update metadata with completion info
            if ontology.ontology_metadata:
                metadata = ontology.ontology_metadata.copy()
                metadata.update({
                    "processed_chunks": metadata.get("total_chunks", 1),
                    "triples_count": len(triples_data),
                    "entities_count": len(result.get("extracted_entities", [])),
                    "completion_status": "success"
                })
                ontology.ontology_metadata = metadata
            
            print(f"[ONTOLOGY] Ontology creation completed: {len(triples_data)} triples, {len(result.get('extracted_entities', []))} entity types")
        else:
            ontology.status = "draft"  # Fallback to draft if AI fails
            ontology.triples = []
            
            # Update metadata with error info
            if ontology.ontology_metadata:
                metadata = ontology.ontology_metadata.copy()
                metadata.update({
                    "completion_status": "error",
                    "error_message": result.get("error_message", "Unknown error")
                })
                ontology.ontology_metadata = metadata
            
            print(f"[ONTOLOGY] Ontology creation failed: {result.get('error_message', 'Unknown error')}")
        
        db.commit()
        
    except Exception as e:
        # Handle any errors
        print(f"[ONTOLOGY] Exception during ontology creation: {str(e)}")
        try:
            ontology = db.query(Ontology).filter(Ontology.id == ontology_id).first()
            if ontology:
                ontology.status = "draft"
                if ontology.ontology_metadata:
                    metadata = ontology.ontology_metadata.copy()
                    metadata.update({
                        "completion_status": "error",
                        "error_message": str(e)
                    })
                    ontology.ontology_metadata = metadata
                db.commit()
        except Exception as commit_error:
            print(f"[ONTOLOGY] Error updating ontology status: {str(commit_error)}")
    finally:
        db.close()

@router.get("/", response_model=List[OntologyResponse])
async def list_ontologies(
    document_id: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Ontology).filter(Ontology.user_id == current_user.id)
    
    if document_id:
        query = query.filter(Ontology.document_id == document_id)
    
    ontologies = query.all()
    return [OntologyResponse.model_validate(ont) for ont in ontologies]

@router.get("/{ontology_id}", response_model=OntologyDetailResponse)
async def get_ontology(
    ontology_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ontology = db.query(Ontology).filter(
        Ontology.id == ontology_id,
        Ontology.user_id == current_user.id
    ).first()
    
    if not ontology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ontology not found"
        )
    
    # Convert stored triples to Pydantic models
    triples = []
    for triple_data in ontology.triples or []:
        try:
            triple = OntologyTriple(**triple_data)
            triples.append(triple)
        except Exception:
            continue  # Skip invalid triples
    
    response_data = OntologyResponse.model_validate(ontology).model_dump()
    response_data["triples"] = triples
    
    return OntologyDetailResponse(**response_data)

@router.put("/{ontology_id}", response_model=OntologyResponse)
async def update_ontology(
    ontology_id: str,
    ontology_data: OntologyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ontology = db.query(Ontology).filter(
        Ontology.id == ontology_id,
        Ontology.user_id == current_user.id
    ).first()
    
    if not ontology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ontology not found"
        )
    
    # Update ontology
    ontology.name = ontology_data.name
    ontology.description = ontology_data.description
    ontology.triples = [triple.model_dump() for triple in ontology_data.triples]
    ontology.version += 1
    ontology.status = "active"
    ontology.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ontology)
    
    return OntologyResponse.model_validate(ontology)

@router.post("/{ontology_id}/reprocess")
async def reprocess_ontology(
    ontology_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ontology = db.query(Ontology).filter(
        Ontology.id == ontology_id,
        Ontology.user_id == current_user.id
    ).first()
    
    if not ontology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ontology not found"
        )
    
    # Get the associated document
    document = db.query(Document).filter(
        Document.id == ontology.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated document not found"
        )
    
    # Reset status to processing
    ontology.status = "processing"
    db.commit()
    
    # Process ontology creation in background
    background_tasks.add_task(
        process_ontology_creation,
        ontology.id,
        document.content_text,
        current_user.id,
        db
    )
    
    return {"message": "Ontology reprocessing started"}

@router.get("/{ontology_id}/progress")
async def get_ontology_progress(
    ontology_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the progress of ontology generation"""
    ontology = db.query(Ontology).filter(
        Ontology.id == ontology_id,
        Ontology.user_id == current_user.id
    ).first()
    
    if not ontology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ontology not found"
        )
    
    # Prepare progress response
    progress_data = {
        "id": ontology.id,
        "status": ontology.status,
        "metadata": ontology.ontology_metadata or {},
        "created_at": ontology.created_at.isoformat() if ontology.created_at else None,
        "updated_at": ontology.updated_at.isoformat() if ontology.updated_at else None
    }
    
    # Calculate progress percentage
    if ontology.ontology_metadata:
        metadata = ontology.ontology_metadata
        total_chunks = metadata.get("total_chunks", 1)
        processed_chunks = metadata.get("processed_chunks", 0)
        progress_data["progress_percentage"] = int((processed_chunks / total_chunks) * 100) if total_chunks > 0 else 0
    else:
        progress_data["progress_percentage"] = 0 if ontology.status == "processing" else 100
    
    return progress_data

@router.delete("/{ontology_id}")
async def delete_ontology(
    ontology_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ontology = db.query(Ontology).filter(
        Ontology.id == ontology_id,
        Ontology.user_id == current_user.id
    ).first()
    
    if not ontology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ontology not found"
        )
    
    # Check if ontology is used in any extractions
    from database import Extraction
    extraction_count = db.query(Extraction).filter(
        Extraction.ontology_id == ontology_id
    ).count()
    
    if extraction_count > 0:
        # Archive instead of delete if used in extractions
        ontology.status = "archived"
        ontology.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Ontology archived (was used in extractions)"}
    else:
        # Safe to delete
        db.delete(ontology)
        db.commit()
        return {"message": "Ontology deleted successfully"}