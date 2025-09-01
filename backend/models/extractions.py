from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ExtractionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class ExtractionRequest(BaseModel):
    document_id: str
    ontology_id: str
    additional_instructions: Optional[str] = Field(None, max_length=2000)
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