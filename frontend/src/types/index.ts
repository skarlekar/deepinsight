// Authentication types
export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

// User Settings types
export interface UserSettings {
  id: string;
  user_id: string;
  
  // Processing preferences
  default_chunk_size: number;
  default_overlap_percentage: number;
  
  // Notification preferences
  email_notifications: boolean;
  extraction_complete: boolean;
  ontology_created: boolean;
  system_updates: boolean;
  
  // Appearance preferences
  theme: 'light' | 'dark' | 'auto';
  language: string;
  
  // API configuration
  anthropic_api_key_configured: boolean;
  max_retries: number;
  timeout_seconds: number;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface UserSettingsUpdate {
  // Processing preferences
  default_chunk_size?: number;
  default_overlap_percentage?: number;
  
  // Notification preferences
  email_notifications?: boolean;
  extraction_complete?: boolean;
  ontology_created?: boolean;
  system_updates?: boolean;
  
  // Appearance preferences
  theme?: 'light' | 'dark' | 'auto';
  language?: string;
  
  // API configuration
  anthropic_api_key?: string;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// Document types
export enum DocumentStatus {
  UPLOADED = "uploaded",
  PROCESSING = "processing",
  COMPLETED = "completed",
  ERROR = "error"
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: DocumentStatus;
  created_at: string;
  processed_at?: string;
  error_message?: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  limit: number;
}

// Ontology types
export enum OntologyStatus {
  DRAFT = "draft",
  PROCESSING = "processing",
  ACTIVE = "active",
  ARCHIVED = "archived"
}

export enum PrimitiveType {
  STRING = "string",
  INTEGER = "integer",
  FLOAT = "float",
  BOOLEAN = "boolean"
}

export interface EntityDefinition {
  entity_type: string;
  type_variations: string[];
  primitive_type: PrimitiveType;
}

export interface RelationshipDefinition {
  relationship_type: string;
  type_variations: string[];
}

export interface OntologyTriple {
  subject: EntityDefinition;
  relationship: RelationshipDefinition;
  object: EntityDefinition;
}

export interface Ontology {
  id: string;
  user_id: string;
  document_id: string;
  name: string;
  description?: string;
  additional_instructions?: string;
  version: number;
  status: OntologyStatus;
  created_at: string;
  updated_at: string;
}

export interface OntologyDetail extends Ontology {
  triples: OntologyTriple[];
}

// Extraction types
export enum ExtractionStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  ERROR = "error"
}

export interface Extraction {
  id: string;
  user_id: string;
  document_id: string;
  ontology_id: string;
  status: ExtractionStatus;
  created_at: string;
  completed_at?: string;
}

export interface ExtractionDetail extends Extraction {
  nodes_count?: number;
  relationships_count?: number;
  neo4j_export_available: boolean;
  neptune_export_available: boolean;
  error_message?: string;
}

export interface ExtractionNode {
  id: string;
  type: string;
  properties: Record<string, any>;
  source_location?: string;
}

export interface ExtractionRelationship {
  id: string;
  type: string;
  source_id: string;
  target_id: string;
  properties: Record<string, any>;
  source_location?: string;
}

export interface ExtractionResult {
  nodes: ExtractionNode[];
  relationships: ExtractionRelationship[];
  metadata: Record<string, any>;
}

// Export types
export interface ExportResponse {
  nodes_csv_url?: string;
  relationships_csv_url?: string;
  vertices_csv_url?: string;
  edges_csv_url?: string;
  download_expires_at: string;
}

// API Response types
export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  timestamp: string;
}

export interface ApiSuccess<T = any> {
  success: true;
  data: T;
  message?: string;
  timestamp: string;
}