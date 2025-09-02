from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from config import get_settings

settings = get_settings()

# Database setup
connect_args = {}
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    ontologies = relationship("Ontology", back_populates="user")
    extractions = relationship("Extraction", back_populates="user")
    session_tokens = relationship("SessionToken", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="uploaded")
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)
    document_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    ontologies = relationship("Ontology", back_populates="document")
    extractions = relationship("Extraction", back_populates="document")

class Ontology(Base):
    __tablename__ = "ontologies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="draft")
    triples = Column(JSON, nullable=False, default=list)
    ontology_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # Relationships
    user = relationship("User", back_populates="ontologies")
    document = relationship("Document", back_populates="ontologies")
    extractions = relationship("Extraction", back_populates="ontology")

class Extraction(Base):
    __tablename__ = "extractions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    ontology_id = Column(String, ForeignKey("ontologies.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")
    nodes = Column(JSON, nullable=True)
    relationships = Column(JSON, nullable=True)
    extraction_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="extractions")
    document = relationship("Document", back_populates="extractions")
    ontology = relationship("Ontology", back_populates="extractions")

class SessionToken(Base):
    __tablename__ = "session_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="session_tokens")

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Processing preferences
    default_chunk_size = Column(Integer, nullable=False, default=1000)
    default_overlap_percentage = Column(Integer, nullable=False, default=10)
    
    # Notification preferences
    email_notifications = Column(Boolean, nullable=False, default=True)
    extraction_complete = Column(Boolean, nullable=False, default=True)
    ontology_created = Column(Boolean, nullable=False, default=True)
    system_updates = Column(Boolean, nullable=False, default=False)
    
    # Appearance preferences
    theme = Column(String(20), nullable=False, default="light")
    language = Column(String(10), nullable=False, default="en")
    
    # API configuration
    anthropic_api_key = Column(String(255), nullable=True)
    max_retries = Column(Integer, nullable=False, default=3)
    timeout_seconds = Column(Integer, nullable=False, default=30)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())
    
    # Relationships
    user = relationship("User", back_populates="settings")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
async def init_database():
    import os
    try:
        # Ensure database directory exists
        db_path = settings.database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise