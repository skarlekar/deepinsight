from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
from pathlib import Path

from database import get_db, User, Extraction
from models.exports import ExportResponse
from auth.security import get_current_user
from utils.csv_exporters import get_export_manager
from config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/{extraction_id}/neo4j", response_model=ExportResponse)
async def export_neo4j(
    extraction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get extraction
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
    
    if not extraction.nodes and not extraction.relationships:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data available for export"
        )
    
    try:
        # Export data
        export_manager = get_export_manager(settings.export_directory)
        export_urls = export_manager.export_for_neo4j(
            extraction.nodes or [],
            extraction.relationships or []
        )
        
        # Set expiration time (24 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        return ExportResponse(
            nodes_csv_url=export_urls['nodes_csv_url'],
            relationships_csv_url=export_urls['relationships_csv_url'],
            download_expires_at=expires_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.post("/{extraction_id}/neptune", response_model=ExportResponse)
async def export_neptune(
    extraction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get extraction
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
    
    if not extraction.nodes and not extraction.relationships:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data available for export"
        )
    
    try:
        # Export data
        export_manager = get_export_manager(settings.export_directory)
        export_urls = export_manager.export_for_neptune(
            extraction.nodes or [],
            extraction.relationships or []
        )
        
        # Set expiration time (24 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        return ExportResponse(
            vertices_csv_url=export_urls['vertices_csv_url'],
            edges_csv_url=export_urls['edges_csv_url'],
            download_expires_at=expires_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/download/{filename}")
async def download_export_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download exported CSV file"""
    file_path = Path(settings.export_directory) / filename
    
    # Security: ensure file exists and is a CSV
    if not file_path.exists() or not filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Security: ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/csv'
    )