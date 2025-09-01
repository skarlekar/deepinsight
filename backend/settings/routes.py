from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, User, UserSettings
from models.settings import UserSettingsRequest, UserSettingsResponse, UserSettingsUpdate
from auth.security import get_current_user

router = APIRouter()

@router.get("/", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user settings, creating default settings if none exist"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        # Create default settings for the user
        settings = UserSettings(
            user_id=current_user.id,
            default_chunk_size=1000,
            default_overlap_percentage=10,
            email_notifications=True,
            extraction_complete=True,
            ontology_created=True,
            system_updates=False,
            theme="light",
            language="en",
            max_retries=3,
            timeout_seconds=30
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Convert to response model with masked API key
    response_data = {
        "id": settings.id,
        "user_id": settings.user_id,
        "default_chunk_size": settings.default_chunk_size,
        "default_overlap_percentage": settings.default_overlap_percentage,
        "email_notifications": settings.email_notifications,
        "extraction_complete": settings.extraction_complete,
        "ontology_created": settings.ontology_created,
        "system_updates": settings.system_updates,
        "theme": settings.theme,
        "language": settings.language,
        "anthropic_api_key_configured": bool(settings.anthropic_api_key and len(settings.anthropic_api_key.strip()) > 0),
        "max_retries": settings.max_retries,
        "timeout_seconds": settings.timeout_seconds,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at
    }
    
    return UserSettingsResponse(**response_data)

@router.put("/", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        # Create new settings if none exist
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    # Update only provided fields
    update_data = settings_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(settings, field):
            setattr(settings, field, value)
    
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    
    # Convert to response model with masked API key
    response_data = {
        "id": settings.id,
        "user_id": settings.user_id,
        "default_chunk_size": settings.default_chunk_size,
        "default_overlap_percentage": settings.default_overlap_percentage,
        "email_notifications": settings.email_notifications,
        "extraction_complete": settings.extraction_complete,
        "ontology_created": settings.ontology_created,
        "system_updates": settings.system_updates,
        "theme": settings.theme,
        "language": settings.language,
        "anthropic_api_key_configured": bool(settings.anthropic_api_key and len(settings.anthropic_api_key.strip()) > 0),
        "max_retries": settings.max_retries,
        "timeout_seconds": settings.timeout_seconds,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at
    }
    
    return UserSettingsResponse(**response_data)

@router.post("/", response_model=UserSettingsResponse)
async def create_user_settings(
    settings_data: UserSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or replace user settings"""
    # Check if settings already exist
    existing_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if existing_settings:
        # Delete existing settings
        db.delete(existing_settings)
        db.commit()
    
    # Create new settings
    settings = UserSettings(
        user_id=current_user.id,
        **settings_data.model_dump()
    )
    
    db.add(settings)
    db.commit()
    db.refresh(settings)
    
    # Convert to response model with masked API key
    response_data = {
        "id": settings.id,
        "user_id": settings.user_id,
        "default_chunk_size": settings.default_chunk_size,
        "default_overlap_percentage": settings.default_overlap_percentage,
        "email_notifications": settings.email_notifications,
        "extraction_complete": settings.extraction_complete,
        "ontology_created": settings.ontology_created,
        "system_updates": settings.system_updates,
        "theme": settings.theme,
        "language": settings.language,
        "anthropic_api_key_configured": bool(settings.anthropic_api_key and len(settings.anthropic_api_key.strip()) > 0),
        "max_retries": settings.max_retries,
        "timeout_seconds": settings.timeout_seconds,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at
    }
    
    return UserSettingsResponse(**response_data)

@router.delete("/")
async def reset_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset user settings to defaults"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if settings:
        db.delete(settings)
        db.commit()
    
    return {"message": "User settings reset to defaults"}