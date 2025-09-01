from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re

class OntologyStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    ACTIVE = "active"
    ARCHIVED = "archived"

class PrimitiveType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"

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

class OntologyCreateRequest(BaseModel):
    document_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    additional_instructions: Optional[str] = Field(None, max_length=2000)
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
    additional_instructions: Optional[str] = None
    version: int
    status: OntologyStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OntologyDetailResponse(OntologyResponse):
    triples: List[OntologyTriple]