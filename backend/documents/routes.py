from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from database import get_db, User, Document
from models.documents import DocumentResponse, DocumentListResponse, DocumentStatusResponse, DocumentStatus
from auth.security import get_current_user
from utils.file_processor import (
    DocumentProcessorFactory, validate_file_type, validate_file_size
)
from config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not validate_file_type(file.filename, file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Read file content to get size
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if not validate_file_size(file_size, settings.max_file_size):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
        )
    
    # Create unique filename
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{file_id}{file_extension}"
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_directory, exist_ok=True)
    file_path = os.path.join(settings.upload_directory, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create document record
    document = Document(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        status="uploaded"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document asynchronously (simplified - in production, use background tasks)
    try:
        processor = DocumentProcessorFactory.get_processor(file.content_type)
        text_content = processor.extract_text(file_path)
        metadata = processor.extract_metadata(file_path)
        
        # Update document with extracted content
        document.content_text = text_content
        document.document_metadata = {
            "title": metadata.title,
            "author": metadata.author,
            "word_count": metadata.word_count,
            "character_count": metadata.character_count,
            "page_count": metadata.page_count
        }
        document.status = "completed"
        document.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(document)
        
    except Exception as e:
        document.status = "error"
        document.error_message = str(e)
        db.commit()
    
    return DocumentResponse.from_orm(document)

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    
    # Get documents for current user
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).offset(offset).limit(limit).all()
    
    # Get total count
    total = db.query(Document).filter(
        Document.user_id == current_user.id
    ).count()
    
    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        total=total,
        page=page,
        limit=limit
    )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.from_orm(document)

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Simple progress calculation
    progress = 0
    if document.status == "uploaded":
        progress = 25
    elif document.status == "processing":
        progress = 50
    elif document.status == "completed":
        progress = 100
    elif document.status == "error":
        progress = 0
    
    return DocumentStatusResponse(
        document_id=document.id,
        status=document.status,
        progress=progress,
        error_message=document.error_message
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from filesystem
    file_path = os.path.join(settings.upload_directory, document.filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass  # Continue with database deletion even if file deletion fails
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download original document file"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    file_path = Path(settings.upload_directory) / document.filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on server"
        )
    
    return FileResponse(
        path=str(file_path),
        filename=document.original_filename,
        media_type=document.mime_type
    )