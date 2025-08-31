from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db, User, Document, Ontology
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
    try:
        # Get ontology record
        ontology = db.query(Ontology).filter(Ontology.id == ontology_id).first()
        if not ontology:
            return
        
        # Process with AI agent
        result = create_ontology_from_document(document_text, ontology.document_id, user_id)
        
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
        else:
            ontology.status = "draft"  # Fallback to draft if AI fails
            ontology.triples = []
        
        db.commit()
        
    except Exception as e:
        # Handle any errors
        if ontology:
            ontology.status = "draft"
            db.commit()

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