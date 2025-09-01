from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserSettingsRequest(BaseModel):
    # Processing preferences
    default_chunk_size: int = Field(default=1000, ge=500, le=2000)
    default_overlap_percentage: int = Field(default=10, ge=0, le=50)
    
    # Notification preferences
    email_notifications: bool = Field(default=True)
    extraction_complete: bool = Field(default=True)
    ontology_created: bool = Field(default=True)
    system_updates: bool = Field(default=False)
    
    # Appearance preferences
    theme: str = Field(default="light", pattern="^(light|dark|auto)$")
    language: str = Field(default="en", pattern="^[a-z]{2}$")
    
    # API configuration
    anthropic_api_key: Optional[str] = Field(default=None, max_length=255)
    max_retries: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=10, le=120)

class UserSettingsResponse(BaseModel):
    id: str
    user_id: str
    
    # Processing preferences
    default_chunk_size: int
    default_overlap_percentage: int
    
    # Notification preferences
    email_notifications: bool
    extraction_complete: bool
    ontology_created: bool
    system_updates: bool
    
    # Appearance preferences
    theme: str
    language: str
    
    # API configuration (masked)
    anthropic_api_key_configured: bool
    max_retries: int
    timeout_seconds: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserSettingsUpdate(BaseModel):
    # Processing preferences
    default_chunk_size: Optional[int] = Field(None, ge=500, le=2000)
    default_overlap_percentage: Optional[int] = Field(None, ge=0, le=50)
    
    # Notification preferences
    email_notifications: Optional[bool] = None
    extraction_complete: Optional[bool] = None
    ontology_created: Optional[bool] = None
    system_updates: Optional[bool] = None
    
    # Appearance preferences
    theme: Optional[str] = Field(None, pattern="^(light|dark|auto)$")
    language: Optional[str] = Field(None, pattern="^[a-z]{2}$")
    
    # API configuration
    anthropic_api_key: Optional[str] = Field(None, max_length=255)
    max_retries: Optional[int] = Field(None, ge=1, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=10, le=120)