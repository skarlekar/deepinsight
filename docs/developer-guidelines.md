# Developer Guidelines

## Overview
Comprehensive development guide for implementing the DeepInsight system based on the technical requirements documentation. This guide provides step-by-step instructions, best practices, and implementation patterns for building the complete system.

## Getting Started

### Prerequisites
Before beginning development, ensure you have reviewed all technical requirements documents:
- [System Design & Architecture](./system-design-architecture.md)
- [Frontend Technical Requirements](./frontend-technical-requirements.md)  
- [Backend Technical Requirements](./backend-technical-requirements.md)
- [Testing Specifications](./testing-specifications.md)
- [Security Requirements](./security-requirements.md)
- [DevOps Requirements](./devops-requirements.md)

### Development Environment Setup

#### 1. Initial Setup
```bash
# Clone the repository
git clone https://github.com/your-org/deepinsight.git
cd deepinsight

# Run the development setup script
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh

# Start the development environment
./scripts/dev-server.sh
```

#### 2. Verify Installation
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database: localhost:5432 (PostgreSQL)
- Cache: localhost:6379 (Redis)

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4)

#### Week 1: Project Structure and Core Setup

##### Backend Foundation
```bash
# Create backend structure
mkdir -p backend/{app,tests,alembic}
cd backend

# Initialize Python environment
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy alembic pydantic python-multipart

# Create core application structure
mkdir -p app/{api,core,models,schemas,services,utils,agents}
touch app/__init__.py app/main.py
```

**Core FastAPI Application (`backend/app/main.py`)**:
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import get_settings
from app.api.v1 import api_router

settings = get_settings()

app = FastAPI(
    title="DeepInsight API",
    description="LLM-based document analysis and ontology extraction",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json" if settings.debug else None
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "deepinsight-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

##### Frontend Foundation
```bash
# Create React application
cd frontend
npx create-vite@latest . --template react-ts
npm install

# Install core dependencies
npm install @mui/material @emotion/react @emotion/styled
npm install @tanstack/react-query axios react-hook-form @hookform/resolvers zod
npm install react-dropzone vis-network

# Install development dependencies  
npm install -D @testing-library/react @testing-library/jest-dom vitest
npm install -D @playwright/test msw
```

**Core React Application (`frontend/src/App.tsx`)**:
```typescript
import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router } from 'react-router-dom';
import { AppRoutes } from './routes/AppRoutes';
import { AuthProvider } from './contexts/AuthContext';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <AppRoutes />
          </Router>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
```

#### Week 2: Authentication and User Management

##### Backend Authentication Implementation
```python
# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

##### Frontend Authentication Context
```typescript
// frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthContextType } from '../types/auth';
import { authService } from '../services/authService';

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      authService.verifyToken(token)
        .then(setUser)
        .catch(() => localStorage.removeItem('access_token'))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authService.login(email, password);
    localStorage.setItem('access_token', response.access_token);
    setUser(response.user);
    return response;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  const value = {
    user,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

#### Week 3: Document Upload System

##### Backend Document Service
```python
# backend/app/services/document_service.py
import aiofiles
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.core.security import get_current_user
from app.utils.file_processing import extract_text_content, validate_file

class DocumentService:
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    async def upload_document(
        self, 
        file: UploadFile, 
        user_id: str, 
        db: AsyncSession
    ) -> Document:
        # Validate file
        validation_result = await validate_file(file)
        if not validation_result.valid:
            raise ValueError(f"File validation failed: {validation_result.errors}")

        # Generate secure filename
        file_extension = Path(file.filename).suffix
        secure_filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = self.upload_dir / secure_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Extract text content
        extracted_text = await extract_text_content(file_path, file.content_type)

        # Create database record
        document = Document(
            filename=file.filename,
            file_path=str(file_path),
            content_type=file.content_type,
            file_size=file.size,
            extracted_content=extracted_text,
            user_id=user_id,
            processing_status="processed"
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document
```

##### Frontend Document Upload Component
```typescript
// frontend/src/components/document/DocumentUpload.tsx
import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Paper, Typography, LinearProgress } from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { documentService } from '../../services/documentService';

interface DocumentUploadProps {
  onUploadSuccess: (document: any) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess }) => {
  const uploadMutation = useMutation({
    mutationFn: documentService.uploadDocument,
    onSuccess: onUploadSuccess,
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach(file => {
      uploadMutation.mutate(file);
    });
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 100 * 1024 * 1024, // 100MB
  });

  return (
    <Paper
      {...getRootProps()}
      sx={{
        p: 4,
        textAlign: 'center',
        border: '2px dashed #ccc',
        cursor: 'pointer',
        '&:hover': { borderColor: 'primary.main' },
      }}
    >
      <input {...getInputProps()} />
      <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
      
      {uploadMutation.isPending ? (
        <Box>
          <Typography variant="body1" gutterBottom>
            Uploading...
          </Typography>
          <LinearProgress />
        </Box>
      ) : (
        <Typography variant="body1">
          {isDragActive
            ? 'Drop the files here...'
            : 'Drag & drop files here, or click to select files'}
        </Typography>
      )}
    </Paper>
  );
};
```

#### Week 4: Database Models and Basic API Endpoints

##### Database Models
```python
# backend/app/models/document.py
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    extracted_content = Column(Text)
    processing_status = Column(String(50), default="uploaded")
    user_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

##### API Endpoints
```python
# backend/app/api/v1/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    document_service: DocumentService = Depends()
):
    """Upload and process a document."""
    try:
        document = await document_service.upload_document(file, current_user.id, db)
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    document_service: DocumentService = Depends()
):
    """Retrieve document information."""
    document = await document_service.get_document(document_id, current_user.id, db)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
```

### Phase 2: AI Integration (Weeks 5-8)

#### Week 5: LLM Service Setup

##### LLM Service Implementation
```python
# backend/app/services/llm_service.py
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import get_settings
from app.prompts import ONTOLOGY_CREATION_PROMPT

class LLMService:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatAnthropic(
            model=settings.llm_model_id,
            api_key=settings.anthropic_api_key,
            temperature=0.1,
            max_tokens=4000
        )

    async def extract_ontology_from_chunk(self, chunk: str) -> dict:
        """Extract entities and relationships from a document chunk."""
        messages = [
            SystemMessage(content=ONTOLOGY_CREATION_PROMPT),
            HumanMessage(content=f"Document chunk: {chunk}")
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_ontology_response(response.content)

    def _parse_ontology_response(self, response: str) -> dict:
        """Parse LLM response into structured ontology format."""
        # Implementation for parsing LLM JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Handle parsing errors with regex or other methods
            return self._fallback_parse(response)
```

##### Prompts Configuration
```python
# backend/app/prompts.py
ONTOLOGY_CREATION_PROMPT = """
You are an expert knowledge engineer extracting structured ontologies from document text.

Your task:
1. Identify entities (nouns representing objects, concepts, people)
2. Identify relationships (verbs/phrases connecting entities)  
3. Create subject-predicate-object triples
4. Use singular forms only, no adjectives
5. Include type variations for flexibility

Output format: JSON array with this structure:
[
  {
    "subject": {
      "entity_type": "Person",
      "type_variations": ["Individual", "Employee"],
      "primitive_type": "string"
    },
    "relationship": {
      "relationship_type": "works_for", 
      "type_variations": ["employed_by", "works_at"]
    },
    "object": {
      "entity_type": "Organization",
      "type_variations": ["Company", "Employer"],
      "primitive_type": "string"
    }
  }
]

Be thorough but precise. Only extract clear, verifiable relationships.
"""

DATA_EXTRACTION_PROMPT = """
Extract specific entity instances and relationships from document text using the provided ontology.

Guidelines:
- Only extract entities/relationships matching the ontology
- Include exact document positions
- Provide confidence scores
- Include supporting text snippets

Output format: JSON with nodes and relationships arrays.
"""
```

#### Week 6: LangGraph Agent Implementation

##### Ontology Creation Agent
```python
# backend/app/agents/ontology_agent.py
from langgraph import StateGraph
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.llm_service import LLMService

class OntologyState(BaseModel):
    document_chunks: List[str]
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    ontology: List[Dict[str, Any]]
    current_chunk: int = 0
    total_chunks: int
    status: str = "processing"

class OntologyCreationAgent:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(OntologyState)
        
        workflow.add_node("process_chunk", self._process_chunk)
        workflow.add_node("extract_entities", self._extract_entities)
        workflow.add_node("deduplicate", self._deduplicate)
        workflow.add_node("build_ontology", self._build_ontology)
        
        workflow.set_entry_point("process_chunk")
        workflow.add_conditional_edges(
            "process_chunk",
            self._should_continue_processing,
            {"continue": "extract_entities", "finish": "deduplicate"}
        )
        
        workflow.add_edge("extract_entities", "process_chunk")
        workflow.add_edge("deduplicate", "build_ontology")
        workflow.add_edge("build_ontology", "__end__")
        
        return workflow.compile()

    async def process_document(self, document_text: str) -> OntologyState:
        """Process entire document to create ontology."""
        chunks = self._chunk_document(document_text)
        
        initial_state = OntologyState(
            document_chunks=chunks,
            entities=[],
            relationships=[],
            ontology=[],
            total_chunks=len(chunks)
        )
        
        result = await self.graph.ainvoke(initial_state)
        return result

    async def _process_chunk(self, state: OntologyState) -> OntologyState:
        """Process current chunk for entity/relationship extraction."""
        if state.current_chunk >= state.total_chunks:
            state.status = "completed"
            return state
            
        chunk = state.document_chunks[state.current_chunk]
        
        # Extract from current chunk
        extraction_result = await self.llm_service.extract_ontology_from_chunk(chunk)
        
        # Add to accumulated results
        state.entities.extend(extraction_result.get("entities", []))
        state.relationships.extend(extraction_result.get("relationships", []))
        state.current_chunk += 1
        
        return state

    def _should_continue_processing(self, state: OntologyState) -> str:
        """Determine if more chunks need processing."""
        return "continue" if state.current_chunk < state.total_chunks else "finish"
```

#### Week 7: Data Extraction Agent

##### Data Extraction Implementation
```python
# backend/app/agents/extraction_agent.py
from langchain_community.graphs import LLMGraphTransformer
from langchain_core.documents import Document
from langgraph import StateGraph
from pydantic import BaseModel
from typing import List, Dict, Any

class ExtractionState(BaseModel):
    document_chunks: List[str]
    ontology: List[Dict[str, Any]]
    extracted_nodes: List[Dict[str, Any]]
    extracted_relationships: List[Dict[str, Any]]
    current_chunk: int = 0
    progress: float = 0.0
    status: str = "processing"

class DataExtractionAgent:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(ExtractionState)
        
        workflow.add_node("extract_from_chunk", self._extract_from_chunk)
        workflow.add_node("map_locations", self._map_document_locations)
        workflow.add_node("deduplicate_results", self._deduplicate_results)
        workflow.add_node("validate_extraction", self._validate_extraction)
        
        workflow.set_entry_point("extract_from_chunk")
        workflow.add_conditional_edges(
            "extract_from_chunk",
            self._should_continue_extraction,
            {"continue": "extract_from_chunk", "process": "map_locations"}
        )
        
        workflow.add_edge("map_locations", "deduplicate_results")
        workflow.add_edge("deduplicate_results", "validate_extraction")
        workflow.add_edge("validate_extraction", "__end__")
        
        return workflow.compile()

    async def extract_data(
        self, 
        document_text: str, 
        ontology: List[Dict[str, Any]]
    ) -> ExtractionState:
        """Extract structured data using provided ontology."""
        chunks = self._chunk_document(document_text)
        
        initial_state = ExtractionState(
            document_chunks=chunks,
            ontology=ontology,
            extracted_nodes=[],
            extracted_relationships=[]
        )
        
        result = await self.graph.ainvoke(initial_state)
        return result

    async def _extract_from_chunk(self, state: ExtractionState) -> ExtractionState:
        """Extract nodes and relationships from current chunk."""
        if state.current_chunk >= len(state.document_chunks):
            state.status = "extraction_complete"
            return state
            
        chunk = state.document_chunks[state.current_chunk]
        
        # Prepare LLMGraphTransformer
        allowed_nodes = self._get_allowed_nodes(state.ontology)
        allowed_relationships = self._get_allowed_relationships(state.ontology)
        
        graph_transformer = LLMGraphTransformer(
            llm=self.llm_service.llm,
            allowed_nodes=allowed_nodes,
            allowed_relationships=allowed_relationships,
            node_properties=True,
            relationship_properties=True
        )
        
        # Extract graph data
        documents = [Document(page_content=chunk)]
        graph_documents = await graph_transformer.aconvert_to_graph_documents(documents)
        
        if graph_documents:
            graph_doc = graph_documents[0]
            state.extracted_nodes.extend(self._format_nodes(graph_doc.nodes))
            state.extracted_relationships.extend(
                self._format_relationships(graph_doc.relationships)
            )
        
        state.current_chunk += 1
        state.progress = state.current_chunk / len(state.document_chunks)
        
        return state
```

#### Week 8: WebSocket Progress Tracking

##### WebSocket Implementation
```python
# backend/app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)

    def disconnect(self, connection_id: str, user_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if user_id in self.user_connections:
            self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections for a user."""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.active_connections:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    connection_id = str(uuid.uuid4())
    await manager.connect(websocket, user_id, connection_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
```

### Phase 3: Advanced Features (Weeks 9-12)

#### Week 9-10: Graph Visualization

##### Frontend Graph Component
```typescript
// frontend/src/components/visualization/NetworkGraph.tsx
import React, { useEffect, useRef } from 'react';
import { Network } from 'vis-network/standalone';
import { DataSet } from 'vis-data/standalone';
import { Box, Paper, Toolbar, IconButton, Typography } from '@mui/material';
import { ZoomIn, ZoomOut, CenterFocusStrong } from '@mui/icons-material';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphEdge {
  id: string;
  from: string;
  to: string;
  label: string;
  type: string;
}

interface NetworkGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeSelect?: (node: GraphNode) => void;
  onEdgeSelect?: (edge: GraphEdge) => void;
}

export const NetworkGraph: React.FC<NetworkGraphProps> = ({
  nodes,
  edges,
  onNodeSelect,
  onEdgeSelect,
}) => {
  const networkRef = useRef<HTMLDivElement>(null);
  const networkInstance = useRef<Network | null>(null);

  useEffect(() => {
    if (!networkRef.current) return;

    // Prepare data for vis.js
    const visNodes = new DataSet(
      nodes.map(node => ({
        id: node.id,
        label: node.label,
        title: `Type: ${node.type}\nProperties: ${JSON.stringify(node.properties)}`,
        color: getNodeColor(node.type),
        shape: 'circle',
        size: 25,
      }))
    );

    const visEdges = new DataSet(
      edges.map(edge => ({
        id: edge.id,
        from: edge.from,
        to: edge.to,
        label: edge.label,
        title: `Type: ${edge.type}`,
        arrows: { to: { enabled: true, scaleFactor: 1 } },
        color: { color: '#848484' },
      }))
    );

    // Network options
    const options = {
      physics: {
        enabled: true,
        stabilization: { iterations: 100 },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 95,
          springConstant: 0.04,
          damping: 0.09,
        },
      },
      interaction: {
        hover: true,
        selectConnectedEdges: false,
      },
      nodes: {
        font: { size: 14, color: '#000000' },
        borderWidth: 2,
        shadow: true,
      },
      edges: {
        font: { size: 12, align: 'middle' },
        smooth: { type: 'continuous' },
      },
    };

    // Create network
    networkInstance.current = new Network(
      networkRef.current,
      { nodes: visNodes, edges: visEdges },
      options
    );

    // Event listeners
    networkInstance.current.on('selectNode', (event) => {
      const nodeId = event.nodes[0];
      const selectedNode = nodes.find(n => n.id === nodeId);
      if (selectedNode && onNodeSelect) {
        onNodeSelect(selectedNode);
      }
    });

    networkInstance.current.on('selectEdge', (event) => {
      const edgeId = event.edges[0];
      const selectedEdge = edges.find(e => e.id === edgeId);
      if (selectedEdge && onEdgeSelect) {
        onEdgeSelect(selectedEdge);
      }
    });

    return () => {
      if (networkInstance.current) {
        networkInstance.current.destroy();
      }
    };
  }, [nodes, edges, onNodeSelect, onEdgeSelect]);

  const handleZoomIn = () => {
    if (networkInstance.current) {
      networkInstance.current.zoom({ scale: 1.2 });
    }
  };

  const handleZoomOut = () => {
    if (networkInstance.current) {
      networkInstance.current.zoom({ scale: 0.8 });
    }
  };

  const handleCenter = () => {
    if (networkInstance.current) {
      networkInstance.current.fit();
    }
  };

  const getNodeColor = (type: string): string => {
    const colors = {
      Person: '#4CAF50',
      Organization: '#2196F3',
      Location: '#FF9800',
      Event: '#9C27B0',
      Concept: '#795548',
    };
    return colors[type as keyof typeof colors] || '#9E9E9E';
  };

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar variant="dense">
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Knowledge Graph
        </Typography>
        <IconButton onClick={handleZoomIn} size="small">
          <ZoomIn />
        </IconButton>
        <IconButton onClick={handleZoomOut} size="small">
          <ZoomOut />
        </IconButton>
        <IconButton onClick={handleCenter} size="small">
          <CenterFocusStrong />
        </IconButton>
      </Toolbar>
      <Box ref={networkRef} sx={{ flexGrow: 1, minHeight: 400 }} />
    </Paper>
  );
};
```

#### Week 11: Database Integrations

##### Neo4j Integration
```python
# backend/app/services/neo4j_service.py
from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any
from app.core.config import get_settings

class Neo4jService:
    def __init__(self):
        settings = get_settings()
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )

    async def create_nodes_and_relationships(
        self, 
        nodes: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ):
        """Import extracted data into Neo4j."""
        async with self.driver.session() as session:
            # Create nodes
            for node in nodes:
                await session.run(
                    f"CREATE (n:{node['type']} {{id: $id, properties: $properties}})",
                    id=node['id'],
                    properties=node['properties']
                )
            
            # Create relationships
            for rel in relationships:
                await session.run(
                    """
                    MATCH (a {id: $source_id}), (b {id: $target_id})
                    CREATE (a)-[r:$relationship_type $properties]->(b)
                    """,
                    source_id=rel['source_id'],
                    target_id=rel['target_id'],
                    relationship_type=rel['type'],
                    properties=rel['properties']
                )

    async def export_to_csv(self) -> Dict[str, str]:
        """Export Neo4j data to CSV format."""
        async with self.driver.session() as session:
            # Export nodes
            nodes_result = await session.run(
                "MATCH (n) RETURN id(n) as id, labels(n) as labels, properties(n) as properties"
            )
            
            # Export relationships
            relationships_result = await session.run(
                """
                MATCH (a)-[r]->(b) 
                RETURN id(a) as source, id(b) as target, type(r) as type, properties(r) as properties
                """
            )
            
            # Convert to CSV format
            return {
                'nodes_csv': self._format_nodes_csv(await nodes_result.data()),
                'relationships_csv': self._format_relationships_csv(await relationships_result.data())
            }
```

##### AWS Neptune Integration
```python
# backend/app/services/neptune_service.py
import boto3
from gremlin_python.driver import client
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

class NeptuneService:
    def __init__(self):
        settings = get_settings()
        self.endpoint = settings.neptune_endpoint
        self.connection = DriverRemoteConnection(
            f'wss://{self.endpoint}:8182/gremlin', 'g'
        )
        self.g = traversal().withRemote(self.connection)

    async def create_vertices_and_edges(
        self, 
        nodes: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ):
        """Import data into Neptune using Gremlin."""
        
        # Create vertices
        for node in nodes:
            traversal = self.g.addV(node['type']).property('id', node['id'])
            
            for key, value in node['properties'].items():
                traversal = traversal.property(key, value)
            
            await traversal.next()
        
        # Create edges
        for rel in relationships:
            traversal = self.g.V().has('id', rel['source_id']).addE(rel['type']).to(
                self.g.V().has('id', rel['target_id'])
            )
            
            for key, value in rel['properties'].items():
                traversal = traversal.property(key, value)
            
            await traversal.next()

    async def export_to_csv(self) -> Dict[str, str]:
        """Export Neptune data to CSV format for bulk loading."""
        # Implement Neptune CSV export format
        vertices = await self.g.V().valueMap(True).toList()
        edges = await self.g.E().valueMap(True).toList()
        
        return {
            'vertices_csv': self._format_neptune_vertices_csv(vertices),
            'edges_csv': self._format_neptune_edges_csv(edges)
        }
```

#### Week 12: Production Optimization

##### Performance Optimization
```python
# backend/app/core/performance.py
from functools import wraps
import time
import asyncio
from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)

def async_timed(func: Callable) -> Callable:
    """Decorator to measure async function execution time."""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result
    
    return wrapper

class BatchProcessor:
    """Process items in batches to optimize performance."""
    
    def __init__(self, batch_size: int = 10, max_concurrent: int = 3):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batches(
        self, 
        items: List[Any], 
        processor: Callable,
        progress_callback: Callable = None
    ):
        """Process items in concurrent batches."""
        batches = [
            items[i:i + self.batch_size] 
            for i in range(0, len(items), self.batch_size)
        ]
        
        async def process_batch(batch, batch_index):
            async with self.semaphore:
                result = await processor(batch)
                if progress_callback:
                    await progress_callback(batch_index, len(batches))
                return result
        
        tasks = [
            process_batch(batch, i) 
            for i, batch in enumerate(batches)
        ]
        
        return await asyncio.gather(*tasks)
```

---

## Development Best Practices

### Code Quality Standards

#### Python Backend Standards
```python
# Use type hints consistently
from typing import List, Dict, Optional, Union

async def process_document(
    document_id: str, 
    user_id: str, 
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process document with proper typing."""
    pass

# Use Pydantic for data validation
from pydantic import BaseModel, Field, validator

class DocumentRequest(BaseModel):
    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., regex=r'^(application|text)/')
    
    @validator('filename')
    def validate_filename(cls, v):
        if '..' in v or '/' in v:
            raise ValueError('Invalid filename')
        return v

# Error handling patterns
from app.core.exceptions import DocumentProcessingError

try:
    result = await process_document(doc_id, user_id)
except DocumentProcessingError as e:
    logger.error(f"Document processing failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

#### React Frontend Standards
```typescript
// Use TypeScript interfaces consistently
interface DocumentUploadProps {
  onSuccess: (document: Document) => void;
  onError: (error: Error) => void;
  maxFileSize?: number;
}

// Custom hooks pattern
const useDocumentUpload = () => {
  const mutation = useMutation({
    mutationFn: documentService.upload,
    onSuccess: (data) => {
      // Handle success
    },
    onError: (error) => {
      // Handle error
    }
  });

  return {
    upload: mutation.mutate,
    isLoading: mutation.isPending,
    error: mutation.error
  };
};

// Component composition
const DocumentManager = () => {
  const { upload, isLoading, error } = useDocumentUpload();
  
  return (
    <Box>
      <DocumentUpload 
        onSuccess={upload}
        disabled={isLoading}
      />
      {error && <ErrorAlert message={error.message} />}
    </Box>
  );
};
```

### Testing Implementation

#### Backend Testing Setup
```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# tests/test_document_service.py
@pytest.mark.asyncio
async def test_document_upload(client, mock_file):
    """Test document upload functionality."""
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": mock_file}
    )
    
    assert response.status_code == 200
    assert "id" in response.json()
```

#### Frontend Testing Setup
```typescript
// tests/test-utils.tsx
import React from 'react';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material';
import { theme } from '../src/theme';

export const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </ThemeProvider>
  );
};

// tests/components/DocumentUpload.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentUpload } from '../../src/components/DocumentUpload';
import { TestWrapper } from '../test-utils';

test('should render upload component', () => {
  render(
    <TestWrapper>
      <DocumentUpload onSuccess={() => {}} />
    </TestWrapper>
  );
  
  expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();
});
```

---

## Deployment Guidelines

### Environment Setup
```bash
# Production environment variables
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://...
export ANTHROPIC_API_KEY=your-api-key
export REDIS_URL=redis://...

# Build and deploy
docker build -t deepinsight-backend backend/
docker build -t deepinsight-frontend frontend/

# Deploy to Heroku
heroku container:push web --app your-app-name
heroku container:release web --app your-app-name
```

### Monitoring Setup
```python
# Production monitoring
import structlog
from prometheus_client import Counter, Histogram

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration')

# Structured logging
logger = structlog.get_logger()

@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    return response
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Backend Issues
1. **Database Connection Errors**
   - Check DATABASE_URL environment variable
   - Verify PostgreSQL is running
   - Run `alembic upgrade head` for migrations

2. **LLM API Errors**
   - Verify API keys are set correctly
   - Check API rate limits
   - Implement proper error handling and retries

3. **File Upload Issues**
   - Check file size limits
   - Verify upload directory permissions
   - Implement proper file validation

#### Frontend Issues
1. **API Connection Errors**
   - Verify backend is running on correct port
   - Check CORS configuration
   - Validate API endpoints

2. **State Management Issues**
   - Use React Query for server state
   - Implement proper error boundaries
   - Debug with React Developer Tools

3. **Performance Issues**
   - Implement code splitting
   - Optimize bundle size
   - Use React.memo for expensive components

This comprehensive development guide provides the foundation for successfully implementing the DeepInsight system according to all technical requirements. Follow the phased approach, maintain quality standards, and refer to the troubleshooting guide for common issues.