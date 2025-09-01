from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db, User, Document, Ontology, Extraction, UserSettings
from models.extractions import (
    ExtractionRequest, ExtractionResponse, ExtractionDetailResponse,
    ExtractionStatusResponse, ExtractionResult, ExtractionNode, ExtractionRelationship
)
from auth.security import get_current_user
from utils.ai_agents import extract_data_with_ontology
from utils.file_processor import chunk_text

router = APIRouter()

@router.post("/", response_model=ExtractionResponse)
async def create_extraction(
    extraction_data: ExtractionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate document exists and belongs to user
    document = db.query(Document).filter(
        Document.id == extraction_data.document_id,
        Document.user_id == current_user.id,
        Document.status == "completed"
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or not processed"
        )
    
    # Validate ontology exists and belongs to user
    ontology = db.query(Ontology).filter(
        Ontology.id == extraction_data.ontology_id,
        Ontology.user_id == current_user.id,
        Ontology.status == "active"
    ).first()
    
    if not ontology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ontology not found or not active"
        )
    
    # Get user settings for chunk parameters
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    # Use user settings if available, otherwise use request parameters or defaults
    chunk_size = extraction_data.chunk_size
    overlap_percentage = extraction_data.overlap_percentage
    
    if user_settings:
        # If user has settings and request doesn't specify parameters, use user settings
        if chunk_size is None:
            chunk_size = user_settings.default_chunk_size
        if overlap_percentage is None:
            overlap_percentage = user_settings.default_overlap_percentage
    
    # Apply defaults if still None
    if chunk_size is None:
        chunk_size = 1000
    if overlap_percentage is None:
        overlap_percentage = 10
    
    # Create extraction record with additional instructions in metadata
    metadata = {
        "chunk_size": chunk_size,
        "overlap_percentage": overlap_percentage
    }
    if extraction_data.additional_instructions:
        metadata['additional_instructions'] = extraction_data.additional_instructions
    
    extraction = Extraction(
        user_id=current_user.id,
        document_id=extraction_data.document_id,
        ontology_id=extraction_data.ontology_id,
        status="pending",
        nodes=[],
        relationships=[],
        extraction_metadata=metadata
    )
    
    db.add(extraction)
    db.commit()
    db.refresh(extraction)
    
    # Process extraction in background
    background_tasks.add_task(
        process_data_extraction,
        extraction.id,
        document.content_text,
        ontology.triples,
        chunk_size,
        overlap_percentage,
        current_user.id,
        extraction_data.additional_instructions
    )
    
    return ExtractionResponse.model_validate(extraction)

def process_data_extraction(
    extraction_id: str,
    document_text: str,
    ontology_triples: List,
    chunk_size: int,
    overlap_percentage: int,
    user_id: str,
    additional_instructions: str = None
):
    """Background task to process data extraction"""
    print(f"[EXTRACTION] Starting background processing for extraction {extraction_id}")
    if additional_instructions:
        print(f"[EXTRACTION] Additional instructions provided: {additional_instructions[:100]}...")
    else:
        print(f"[EXTRACTION] No additional instructions provided")
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get extraction record
        extraction = db.query(Extraction).filter(Extraction.id == extraction_id).first()
        if not extraction:
            return
        
        # Update status to processing
        extraction.status = "processing"
        extraction.extraction_metadata = extraction.extraction_metadata or {}
        extraction.extraction_metadata.update({
            "total_chunks": 0,
            "processed_chunks": 0,
            "current_chunk": 0,
            "chunk_progress": []
        })
        db.commit()
        print(f"[EXTRACTION] Updated status to processing for {extraction_id}")
        
        # Chunk the document text
        print(f"[EXTRACTION] Document text length: {len(document_text)} characters")
        print(f"[EXTRACTION] Document text preview: {document_text[:200]}...")
        
        chunks = chunk_text(document_text, chunk_size, overlap_percentage)
        print(f"[EXTRACTION] Created {len(chunks)} chunks for processing")
        
        if len(chunks) == 0:
            extraction.status = "error"
            extraction.extraction_metadata = extraction.extraction_metadata or {}
            extraction.extraction_metadata["error_message"] = "No chunks created - document text may be empty"
            db.commit()
            return
        
        # Update total chunks count - must reassign the entire dict for JSON fields
        metadata = extraction.extraction_metadata.copy()
        metadata["total_chunks"] = len(chunks)
        metadata["chunk_progress"] = [{"status": "pending", "nodes_count": 0, "relationships_count": 0} for _ in range(len(chunks))]
        extraction.extraction_metadata = metadata
        db.commit()
        
        # Initialize enhanced extraction processor
        from utils.enhanced_extraction import EnhancedExtractionProcessor
        enhanced_processor = EnhancedExtractionProcessor()
        all_extracted_relationships = []  # Store for final resolution
        print(f"[EXTRACTION] Using enhanced extraction pipeline with GUID-based deduplication")
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            try:
                # Update current chunk being processed - must reassign for JSON fields
                metadata = extraction.extraction_metadata.copy()
                metadata["current_chunk"] = i + 1
                metadata["chunk_progress"][i]["status"] = "processing"
                extraction.extraction_metadata = metadata
                db.commit()
                
                print(f"[EXTRACTION] Processing chunk {i+1}/{len(chunks)} for extraction {extraction_id}")
                print(f"[EXTRACTION] Chunk {i+1} text length: {len(chunk['text'])}")
                
                # Check if we have Anthropic API key
                import os
                api_key = os.getenv("ANTHROPIC_API_KEY")
                print(f"[EXTRACTION] API key configured: {'Yes' if api_key else 'No'}")
                
                # Extract data from chunk using AI agent
                result = extract_data_with_ontology(
                    chunk["text"],
                    ontology_triples,
                    extraction.document_id,
                    user_id,
                    additional_instructions
                )
                print(f"[EXTRACTION] Chunk {i+1} result: {result['status']}")
                
                if result["status"] == "extraction_completed":
                    # Enhanced extraction: Use EntityRegistry and RelationshipResolver
                    from utils.enhanced_extraction import validate_name_properties
                    
                    # Validate name properties first
                    validation_errors = validate_name_properties(result["extracted_nodes"])
                    if validation_errors:
                        print(f"[EXTRACTION] Validation errors in chunk {i+1}: {validation_errors}")
                        # Continue processing but log errors
                    
                    # Process chunk with enhanced processor
                    chunk_relationships = enhanced_processor.process_chunk_results(i, {
                        "nodes": result["extracted_nodes"],
                        "relationships": result["extracted_relationships"]
                    })
                    
                    # Store relationships for final resolution
                    all_extracted_relationships.extend(chunk_relationships)
                    
                    # Get current entity count for progress tracking
                    chunk_nodes_count = enhanced_processor.entity_registry.get_entity_count()
                    chunk_relationships_count = len(chunk_relationships)
                    
                    print(f"[EXTRACTION] Enhanced processing chunk {i+1}: {chunk_nodes_count} total entities, {chunk_relationships_count} relationships")
                    
                    # Update chunk progress - must reassign for JSON fields
                    metadata = extraction.extraction_metadata.copy()
                    metadata["chunk_progress"][i] = {
                        "status": "completed",
                        "nodes_count": chunk_nodes_count,
                        "relationships_count": chunk_relationships_count
                    }
                    metadata["processed_chunks"] = i + 1
                    extraction.extraction_metadata = metadata
                else:
                    # Update chunk progress - must reassign for JSON fields
                    metadata = extraction.extraction_metadata.copy()
                    metadata["chunk_progress"][i]["status"] = "error"
                    metadata["processed_chunks"] = i + 1
                    extraction.extraction_metadata = metadata
                db.commit()
                
            except Exception as e:
                print(f"[EXTRACTION] Error processing chunk {i+1}: {str(e)}")
                if extraction.extraction_metadata and "chunk_progress" in extraction.extraction_metadata and i < len(extraction.extraction_metadata["chunk_progress"]):
                    # Update chunk progress - must reassign for JSON fields
                    metadata = extraction.extraction_metadata.copy()
                    metadata["chunk_progress"][i]["status"] = "error"
                    metadata["processed_chunks"] = i + 1
                    extraction.extraction_metadata = metadata
                    db.commit()
                continue
        
        # Finalize enhanced extraction
        print(f"[EXTRACTION] Finalizing enhanced extraction...")
        final_results = enhanced_processor.finalize_extraction(all_extracted_relationships)
        
        final_nodes = final_results["nodes"]
        final_relationships = final_results["relationships"]
        enhanced_metadata = final_results["metadata"]
        
        print(f"[EXTRACTION] Enhanced extraction complete: {len(final_nodes)} unique entities, {len(final_relationships)} resolved relationships")
        print(f"[EXTRACTION] Deduplication stats: {enhanced_metadata['entity_stats']}")
        
        # Update extraction with enhanced results
        extraction.nodes = final_nodes
        extraction.relationships = final_relationships
        
        # Enhanced metadata
        extraction.extraction_metadata.update({
            "nodes_count": len(final_nodes),
            "relationships_count": len(final_relationships),
            "chunks_processed": len(chunks),
            "extraction_mode": "enhanced",
            "entity_stats": enhanced_metadata["entity_stats"],
            "relationship_stats": enhanced_metadata["relationship_stats"]
        })
        
        extraction.status = "completed"
        extraction.completed_at = datetime.utcnow()
        
        db.commit()
        
    except Exception as e:
        # Handle any errors
        if extraction:
            extraction.status = "error"
            extraction.extraction_metadata = extraction.extraction_metadata or {}
            extraction.extraction_metadata["error_message"] = str(e)
            db.commit()
    finally:
        db.close()

@router.get("/", response_model=List[ExtractionResponse])
async def list_extractions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    extractions = db.query(Extraction).filter(
        Extraction.user_id == current_user.id
    ).order_by(Extraction.created_at.desc()).all()
    
    return [ExtractionResponse.model_validate(ext) for ext in extractions]

@router.get("/{extraction_id}", response_model=ExtractionDetailResponse)
async def get_extraction(
    extraction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id,
        Extraction.user_id == current_user.id
    ).first()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    # Build detailed response
    response_data = ExtractionResponse.model_validate(extraction).model_dump()
    response_data.update({
        "nodes_count": len(extraction.nodes or []),
        "relationships_count": len(extraction.relationships or []),
        "neo4j_export_available": extraction.status == "completed",
        "neptune_export_available": extraction.status == "completed",
        "error_message": extraction.extraction_metadata.get("error_message") if extraction.extraction_metadata else None
    })
    
    return ExtractionDetailResponse(**response_data)

@router.get("/{extraction_id}/status", response_model=ExtractionStatusResponse)
async def get_extraction_status(
    extraction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id,
        Extraction.user_id == current_user.id
    ).first()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    # Calculate progress
    progress = 0
    if extraction.status == "pending":
        progress = 0
    elif extraction.status == "processing":
        # Calculate progress based on processed chunks
        metadata = extraction.extraction_metadata or {}
        total_chunks = metadata.get("total_chunks", 1)
        processed_chunks = metadata.get("processed_chunks", 0)
        progress = int((processed_chunks / total_chunks) * 100) if total_chunks > 0 else 50
    elif extraction.status == "completed":
        progress = 100
    elif extraction.status == "error":
        progress = 0
    
    return ExtractionStatusResponse(
        extraction_id=extraction.id,
        status=extraction.status,
        progress=progress,
        nodes_count=len(extraction.nodes or []),
        relationships_count=len(extraction.relationships or []),
        error_message=extraction.extraction_metadata.get("error_message") if extraction.extraction_metadata else None
    )

@router.get("/{extraction_id}/progress")
async def get_extraction_progress(
    extraction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id,
        Extraction.user_id == current_user.id
    ).first()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    metadata = extraction.extraction_metadata or {}
    
    return {
        "extraction_id": extraction.id,
        "status": extraction.status,
        "total_chunks": metadata.get("total_chunks", 0),
        "processed_chunks": metadata.get("processed_chunks", 0),
        "current_chunk": metadata.get("current_chunk", 0),
        "chunk_progress": metadata.get("chunk_progress", []),
        "overall_progress": int((metadata.get("processed_chunks", 0) / metadata.get("total_chunks", 1)) * 100) if metadata.get("total_chunks", 0) > 0 else 0,
        "nodes_count": len(extraction.nodes or []),
        "relationships_count": len(extraction.relationships or []),
        "error_message": metadata.get("error_message"),
        "created_at": extraction.created_at,
        "completed_at": extraction.completed_at
    }

@router.get("/{extraction_id}/result", response_model=ExtractionResult)
async def get_extraction_result(
    extraction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id,
        Extraction.user_id == current_user.id,
        Extraction.status == "completed"
    ).first()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found or not completed"
        )
    
    # Convert stored data to Pydantic models
    nodes = []
    for node_data in extraction.nodes or []:
        try:
            node = ExtractionNode(**node_data)
            nodes.append(node)
        except Exception:
            continue
    
    relationships = []
    for rel_data in extraction.relationships or []:
        try:
            rel = ExtractionRelationship(**rel_data)
            relationships.append(rel)
        except Exception:
            continue
    
    return ExtractionResult(
        nodes=nodes,
        relationships=relationships,
        metadata=extraction.extraction_metadata or {}
    )

@router.post("/{extraction_id}/restart")
async def restart_extraction(
    extraction_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id,
        Extraction.user_id == current_user.id
    ).first()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    # Get associated document and ontology
    document = db.query(Document).filter(Document.id == extraction.document_id).first()
    ontology = db.query(Ontology).filter(Ontology.id == extraction.ontology_id).first()
    
    if not document or not ontology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated document or ontology not found"
        )
    
    # Reset extraction status
    extraction.status = "pending"
    extraction.nodes = []
    extraction.relationships = []
    db.commit()
    
    # Restart background processing
    background_tasks.add_task(
        process_data_extraction,
        extraction.id,
        document.content_text,
        ontology.triples,
        extraction.extraction_metadata.get("chunk_size", 1000),
        extraction.extraction_metadata.get("overlap_percentage", 10),
        current_user.id
    )
    
    return {"message": "Extraction restarted"}

@router.delete("/{extraction_id}")
async def delete_extraction(
    extraction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    extraction = db.query(Extraction).filter(
        Extraction.id == extraction_id,
        Extraction.user_id == current_user.id
    ).first()
    
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction not found"
        )
    
    db.delete(extraction)
    db.commit()
    
    return {"message": "Extraction deleted successfully"}

@router.get("/debug-test")
async def debug_test_extraction():
    """Simple debug test without auth"""
    import os
    return {
        "status": "success",
        "message": "Debug endpoint working",
        "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY"))
    }