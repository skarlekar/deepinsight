from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime

from database import init_database
from config import get_settings
from auth.routes import router as auth_router
from documents.routes import router as documents_router
from ontologies.routes import router as ontologies_router
from extractions.routes import router as extractions_router
from exports.routes import router as exports_router

settings = get_settings()

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
        "timestamp": datetime.now(),
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )