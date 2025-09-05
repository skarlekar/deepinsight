#!/usr/bin/env python3
"""
Script to create database tables in Railway PostgreSQL database
"""
import sys
import os
import subprocess
from datetime import datetime
import uuid
from passlib.context import CryptContext
from sqlalchemy import create_engine, text, Column, String, Integer, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Define database models directly (without importing config-dependent modules)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

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

class SessionToken(Base):
    __tablename__ = "session_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

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

def create_tables_in_railway():
    """Create all database tables in Railway PostgreSQL"""
    
    # Use the provided PostgreSQL connection URL
    database_url = "postgresql://postgres:GoEDHUqySICBmylmQGBjpyVGNmthlhvD@yamabiko.proxy.rlwy.net:40648/railway"
    print(f"Using PostgreSQL URL: {database_url[:50]}...")
    
    try:
        # Create engine with PostgreSQL URL
        engine = create_engine(database_url, echo=True)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"Connected to PostgreSQL: {version}")
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        
        # Create initial user
        print("Creating initial user...")
        create_initial_user(engine)
        
        return True
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

def create_initial_user(engine):
    """Create initial skarlekar user"""
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if user already exists
        existing_user = session.query(User).filter_by(username='skarlekar').first()
        if existing_user:
            print("User 'skarlekar' already exists")
            return
        
        # Create password hash
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash("Password123!")
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            username='skarlekar',
            email='skarlekar@example.com',
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(user)
        session.commit()
        print("✓ Created initial user 'skarlekar' with password 'Password123!'")
        
    except Exception as e:
        print(f"Error creating initial user: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("Creating tables in Railway PostgreSQL database...")
    success = create_tables_in_railway()
    
    if success:
        print("\n✓ Database setup completed successfully!")
        print("You can now deploy your app to Railway with PostgreSQL support.")
    else:
        print("\n✗ Database setup failed!")
        sys.exit(1)