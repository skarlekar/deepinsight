from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
from datetime import datetime

from database import init_database
from config import get_settings
from auth.routes import router as auth_router
from documents.routes import router as documents_router
from ontologies.routes import router as ontologies_router
from extractions.routes import router as extractions_router
from exports.routes import router as exports_router
from settings.routes import router as settings_router

settings = get_settings()

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/backend.log"),
        logging.StreamHandler()  # Keep console output too
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="DeepInsight API",
    description="MVP API for document ontology extraction and graph database export",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": "connected",
        "claude_api": "available"
    }


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(documents_router, prefix="/documents", tags=["Documents"])
app.include_router(ontologies_router, prefix="/ontologies", tags=["Ontologies"])
app.include_router(extractions_router, prefix="/extractions", tags=["Extractions"])
app.include_router(exports_router, prefix="/exports", tags=["Exports"])
app.include_router(settings_router, prefix="/settings", tags=["Settings"])

# Test endpoints for debugging
@app.get("/test/ontology-retrieval")
async def test_ontology_retrieval():
    from database import get_db, Ontology
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from config import get_settings
    
    settings = get_settings()
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get first ontology
        ontology = db.query(Ontology).first()
        if not ontology:
            return {"status": "no_ontologies", "message": "No ontologies found in database"}
        
        return {
            "status": "success",
            "ontology_id": ontology.id,
            "ontology_name": ontology.name,
            "ontology_status": ontology.status,
            "triples_count": len(ontology.triples) if ontology.triples else 0,
            "triples_preview": str(ontology.triples)[:200] if ontology.triples else "No triples"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

@app.get("/test/real-extraction")
async def test_real_extraction():
    from database import get_db, Ontology, Document
    from utils.ai_agents import extract_data_with_ontology
    from utils.file_processor import chunk_text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from config import get_settings
    
    settings = get_settings()
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get real document and ontology
        document = db.query(Document).first()
        ontology = db.query(Ontology).first()
        
        if not document or not ontology:
            return {"status": "error", "error": "No document or ontology found"}
        
        # Test chunking with real document
        chunks = chunk_text(document.content_text, chunk_size=1000, overlap_percentage=10)
        
        if not chunks:
            return {"status": "error", "error": "No chunks created"}
        
        # Test AI extraction on first chunk with real ontology
        result = extract_data_with_ontology(
            chunks[0]["text"], 
            ontology.triples, 
            document.id, 
            document.user_id
        )
        
        return {
            "status": "success",
            "document_id": document.id,
            "document_length": len(document.content_text),
            "ontology_id": ontology.id,
            "ontology_triples_count": len(ontology.triples),
            "chunks_created": len(chunks),
            "first_chunk_length": len(chunks[0]["text"]),
            "first_chunk_preview": chunks[0]["text"][:200],
            "extraction_result": {
                "status": result.get("status"),
                "nodes_count": len(result.get("extracted_nodes", [])),
                "relationships_count": len(result.get("extracted_relationships", [])),
                "error": result.get("error_message"),
                "sample_nodes": result.get("extracted_nodes", [])[:2]
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

@app.get("/test/chunking-isolated")
async def test_chunking_isolated():
    from utils.file_processor import chunk_text
    
    # Test with simple text first
    test_text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four. This is sentence five."
    
    try:
        chunks = chunk_text(test_text, chunk_size=50, overlap_percentage=20)
        
        return {
            "status": "success",
            "input_length": len(test_text),
            "chunks_created": len(chunks),
            "chunks": chunks
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/test/chunking-real-doc")
async def test_chunking_real_doc():
    from utils.file_processor import chunk_text
    from database import get_db, Document
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from config import get_settings
    
    settings = get_settings()
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        document = db.query(Document).first()
        if not document:
            return {"status": "error", "error": "No document found"}
        
        chunks = chunk_text(document.content_text, chunk_size=1000, overlap_percentage=10)
        
        return {
            "status": "success",
            "document_id": document.id,
            "document_length": len(document.content_text),
            "chunks_created": len(chunks),
            "first_chunk_preview": chunks[0]["text"][:200] if chunks else "No chunks",
            "chunk_details": [{"id": c["chunk_id"], "size": c["size"], "start": c["start_char"], "end": c["end_char"]} for c in chunks]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

@app.get("/test/background-task")  
async def test_background_task():
    import asyncio
    
    async def dummy_task():
        await asyncio.sleep(2)
        return "Task completed"
    
    try:
        result = await dummy_task()
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/test/ai-agent")
async def test_ai_agent():
    from utils.ai_agents import extract_data_with_ontology
    
    # Simple test data
    test_text = "John works at Microsoft. Sarah is the CEO of Apple."
    test_ontology_triples = [
        {
            "subject": {"entity_type": "Person", "primitive_type": "string"},
            "relationship": {"relationship_type": "works_at"},
            "object": {"entity_type": "Company", "primitive_type": "string"}
        }
    ]
    
    try:
        # Test AI extraction
        result = extract_data_with_ontology(test_text, test_ontology_triples, "test_doc", "test_user")
        
        return {
            "status": "success", 
            "test_text": test_text,
            "extraction_result": {
                "nodes_extracted": len(result.get("extracted_nodes", [])),
                "relationships_extracted": len(result.get("extracted_relationships", [])),
                "nodes": result.get("extracted_nodes", [])[:3],
                "relationships": result.get("extracted_relationships", [])[:3],
                "status": result.get("status"),
                "error": result.get("error_message")
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )