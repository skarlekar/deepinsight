# DeepInsight Pydantic Models
# Complete request/response validation schemas for FastAPI

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import re

# ============================================================================
# Enums for Status Values
# ============================================================================

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class OntologyStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    ACTIVE = "active"
    ARCHIVED = "archived"

class ExtractionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class PrimitiveType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"

# ============================================================================
# Authentication Models
# ============================================================================

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @field_validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123!"
            }
        }

class UserLoginRequest(BaseModel):
    username: str
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123!"
            }
        }

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserResponse

# ============================================================================
# Document Models
# ============================================================================

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    limit: int

class DocumentStatusResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    progress: int = Field(..., ge=0, le=100)
    error_message: Optional[str] = None

# ============================================================================
# Ontology Models
# ============================================================================

class EntityDefinition(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=100)
    type_variations: List[str] = Field(default_factory=list)
    primitive_type: PrimitiveType
    
    @field_validator('entity_type')
    def validate_entity_type(cls, v):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_\s]*$', v):
            raise ValueError('Entity type must start with a letter and contain only letters, numbers, underscores, and spaces')
        return v.strip()
    
    @field_validator('type_variations')
    def validate_type_variations(cls, v):
        return [var.strip() for var in v if var.strip()]

class RelationshipDefinition(BaseModel):
    relationship_type: str = Field(..., min_length=1, max_length=100)
    type_variations: List[str] = Field(default_factory=list)
    
    @field_validator('relationship_type')
    def validate_relationship_type(cls, v):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_\s]*$', v):
            raise ValueError('Relationship type must start with a letter and contain only letters, numbers, underscores, and spaces')
        return v.strip()
    
    @field_validator('type_variations')
    def validate_type_variations(cls, v):
        return [var.strip() for var in v if var.strip()]

class OntologyTriple(BaseModel):
    subject: EntityDefinition
    relationship: RelationshipDefinition
    object: EntityDefinition
    
    class Config:
        schema_extra = {
            "example": {
                "subject": {
                    "entity_type": "Person",
                    "type_variations": ["Employee", "Individual"],
                    "primitive_type": "string"
                },
                "relationship": {
                    "relationship_type": "works_for",
                    "type_variations": ["is_employed_by", "employed_at"]
                },
                "object": {
                    "entity_type": "Organization",
                    "type_variations": ["Company", "Employer"],
                    "primitive_type": "string"
                }
            }
        }

class OntologyCreateRequest(BaseModel):
    document_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    chunk_size: int = Field(1000, ge=100, le=5000)
    overlap_percentage: int = Field(10, ge=0, le=50)
    
    @field_validator('name')
    def validate_name(cls, v):
        return v.strip()

class OntologyUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    triples: List[OntologyTriple]
    
    @field_validator('name')
    def validate_name(cls, v):
        return v.strip()
    
    @field_validator('triples')
    def validate_triples(cls, v):
        if not v:
            raise ValueError('Ontology must contain at least one triple')
        return v

class OntologyResponse(BaseModel):
    id: str
    user_id: str
    document_id: str
    name: str
    description: Optional[str] = None
    version: int
    status: OntologyStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OntologyDetailResponse(OntologyResponse):
    triples: List[OntologyTriple]

# ============================================================================
# Extraction Models
# ============================================================================

class ExtractionRequest(BaseModel):
    document_id: str
    ontology_id: str
    chunk_size: int = Field(1000, ge=100, le=5000)
    overlap_percentage: int = Field(10, ge=0, le=50)

class ExtractionResponse(BaseModel):
    id: str
    user_id: str
    document_id: str
    ontology_id: str
    status: ExtractionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ExtractionDetailResponse(ExtractionResponse):
    nodes_count: Optional[int] = None
    relationships_count: Optional[int] = None
    neo4j_export_available: bool = False
    neptune_export_available: bool = False
    error_message: Optional[str] = None

class ExtractionStatusResponse(BaseModel):
    extraction_id: str
    status: ExtractionStatus
    progress: int = Field(..., ge=0, le=100)
    nodes_count: Optional[int] = None
    relationships_count: Optional[int] = None
    error_message: Optional[str] = None

class ExtractionNode(BaseModel):
    id: str
    type: str
    properties: Dict[str, Any]
    source_location: Optional[str] = None

class ExtractionRelationship(BaseModel):
    id: str
    type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_location: Optional[str] = None

class ExtractionResult(BaseModel):
    nodes: List[ExtractionNode]
    relationships: List[ExtractionRelationship]
    metadata: Dict[str, Any] = Field(default_factory=dict)

# ============================================================================
# Export Models
# ============================================================================

class ExportResponse(BaseModel):
    nodes_csv_url: Optional[str] = None
    relationships_csv_url: Optional[str] = None
    vertices_csv_url: Optional[str] = None
    edges_csv_url: Optional[str] = None
    download_expires_at: datetime

# ============================================================================
# System Models
# ============================================================================

class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
    database: str = "connected"
    claude_api: str = "available"

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.now)

# ============================================================================
# Internal Processing Models (not exposed in API)
# ============================================================================

class ChunkMetadata(BaseModel):
    chunk_id: str
    start_char: int
    end_char: int
    page_number: Optional[int] = None
    line_number: Optional[int] = None
    paragraph_number: Optional[int] = None

class ProcessedChunk(BaseModel):
    text: str
    metadata: ChunkMetadata

class LLMExtractionRequest(BaseModel):
    text: str
    ontology_triples: List[OntologyTriple]
    chunk_metadata: ChunkMetadata

class LLMExtractionResponse(BaseModel):
    extracted_nodes: List[Dict[str, Any]]
    extracted_relationships: List[Dict[str, Any]]
    confidence_score: Optional[float] = None

# ============================================================================
# Configuration Models
# ============================================================================

class DatabaseConfig(BaseModel):
    database_url: str = "sqlite:///./data/deepinsight.db"
    echo: bool = False

class LLMConfig(BaseModel):
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 60

class SecurityConfig(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    max_login_attempts: int = 5
    password_reset_expire_minutes: int = 30

class FileUploadConfig(BaseModel):
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_mime_types: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown"
    ]
    upload_directory: str = "./data/documents"

class AppConfig(BaseModel):
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    database: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    security: SecurityConfig
    file_upload: FileUploadConfig = FileUploadConfig()

# ============================================================================
# Validation Utilities
# ============================================================================

def validate_file_type(filename: str, mime_type: str) -> bool:
    """Validate file type based on filename and MIME type"""
    allowed_extensions = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown"
    }
    
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    file_ext = f'.{file_ext}'
    
    return file_ext in allowed_extensions and allowed_extensions[file_ext] == mime_type

def validate_file_size(file_size: int, max_size: int = 100 * 1024 * 1024) -> bool:
    """Validate file size (default max: 100MB)"""
    return 0 < file_size <= max_size