-- DeepInsight SQLite Database Schema
-- MVP version optimized for <5 users

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT username_length CHECK (length(username) >= 3 AND length(username) <= 50),
    CONSTRAINT username_format CHECK (username GLOB '*[a-zA-Z0-9_]*'),
    CONSTRAINT email_format CHECK (email LIKE '%@%'),
    CONSTRAINT password_length CHECK (length(password_hash) >= 60) -- bcrypt hash length
);

-- Documents table
CREATE TABLE documents (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    user_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT status_values CHECK (status IN ('uploaded', 'processing', 'completed', 'error')),
    CONSTRAINT file_size_positive CHECK (file_size > 0),
    CONSTRAINT mime_type_allowed CHECK (mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/markdown'
    ))
);

-- Ontologies table
CREATE TABLE ontologies (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    user_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    json_schema TEXT NOT NULL, -- JSON string containing the ontology triples
    file_path TEXT NOT NULL UNIQUE, -- Path to the JSON file
    version INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT name_length CHECK (length(name) >= 1 AND length(name) <= 255),
    CONSTRAINT description_length CHECK (description IS NULL OR length(description) <= 1000),
    CONSTRAINT version_positive CHECK (version > 0),
    CONSTRAINT status_values CHECK (status IN ('draft', 'processing', 'active', 'archived')),
    CONSTRAINT json_schema_not_empty CHECK (length(json_schema) > 0)
);

-- Extractions table
CREATE TABLE extractions (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    user_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    ontology_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result_json TEXT, -- JSON extraction results
    nodes_count INTEGER,
    relationships_count INTEGER,
    neo4j_nodes_path TEXT,
    neo4j_relationships_path TEXT,
    neptune_vertices_path TEXT,
    neptune_edges_path TEXT,
    error_message TEXT,
    chunk_size INTEGER DEFAULT 1000,
    overlap_percentage INTEGER DEFAULT 10,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    -- Foreign keys
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
    FOREIGN KEY (ontology_id) REFERENCES ontologies (id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT status_values CHECK (status IN ('pending', 'processing', 'completed', 'error')),
    CONSTRAINT chunk_size_valid CHECK (chunk_size >= 100 AND chunk_size <= 5000),
    CONSTRAINT overlap_valid CHECK (overlap_percentage >= 0 AND overlap_percentage <= 50),
    CONSTRAINT counts_positive CHECK (nodes_count IS NULL OR nodes_count >= 0),
    CONSTRAINT relationships_positive CHECK (relationships_count IS NULL OR relationships_count >= 0)
);

-- Session tokens table (for JWT token blacklisting)
CREATE TABLE session_tokens (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    
    -- Constraint
    CONSTRAINT expires_future CHECK (expires_at > created_at)
);

-- Indexes for performance optimization
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);

CREATE INDEX idx_ontologies_user_id ON ontologies(user_id);
CREATE INDEX idx_ontologies_document_id ON ontologies(document_id);
CREATE INDEX idx_ontologies_status ON ontologies(status);
CREATE INDEX idx_ontologies_created_at ON ontologies(created_at);

CREATE INDEX idx_extractions_user_id ON extractions(user_id);
CREATE INDEX idx_extractions_document_id ON extractions(document_id);
CREATE INDEX idx_extractions_ontology_id ON extractions(ontology_id);
CREATE INDEX idx_extractions_status ON extractions(status);
CREATE INDEX idx_extractions_created_at ON extractions(created_at);

CREATE INDEX idx_session_tokens_user_id ON session_tokens(user_id);
CREATE INDEX idx_session_tokens_expires_at ON session_tokens(expires_at);
CREATE INDEX idx_session_tokens_token_hash ON session_tokens(token_hash);

-- Triggers for updating timestamps
CREATE TRIGGER update_users_timestamp 
    AFTER UPDATE ON users
    FOR EACH ROW
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_ontologies_timestamp 
    AFTER UPDATE ON ontologies
    FOR EACH ROW
    BEGIN
        UPDATE ontologies SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Data validation triggers
CREATE TRIGGER validate_document_processing
    BEFORE UPDATE OF status ON documents
    FOR EACH ROW
    WHEN NEW.status = 'completed' AND NEW.processed_at IS NULL
    BEGIN
        UPDATE documents SET processed_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER validate_extraction_completion
    BEFORE UPDATE OF status ON extractions
    FOR EACH ROW
    WHEN NEW.status = 'completed' AND NEW.completed_at IS NULL
    BEGIN
        UPDATE extractions SET completed_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Clean up expired session tokens
CREATE TRIGGER cleanup_expired_tokens
    AFTER INSERT ON session_tokens
    FOR EACH ROW
    BEGIN
        DELETE FROM session_tokens WHERE expires_at < CURRENT_TIMESTAMP;
    END;

-- Initial data setup
-- Create default admin user (password: admin123!)
-- Note: In production, this should be done via proper registration
INSERT INTO users (id, username, email, password_hash) VALUES 
('admin-user-id-1234567890', 'admin', 'admin@deepinsight.local', 
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeILc.GE7D8.XcR2m');

-- File storage directory structure (to be created by application)
-- data/
-- ├── database.sqlite (this file)
-- ├── documents/
-- │   └── user_{user_id}/
-- │       ├── uploads/           # Original uploaded files
-- │       ├── ontologies/        # Generated ontology JSON files  
-- │       └── extractions/       # Extraction results and CSV exports
-- │           ├── results/       # JSON extraction results
-- │           ├── neo4j/         # Neo4j CSV files
-- │           └── neptune/       # Neptune CSV files
-- └── backups/                   # Database backups