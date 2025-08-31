# Testing Specifications

## Overview
Comprehensive testing strategy for the DeepInsight system covering frontend React application and backend FastAPI services. This document outlines testing frameworks, methodologies, mock requirements, and test coverage expectations.

## Testing Philosophy

### Test Pyramid Approach
1. **Unit Tests (70%)**: Fast, isolated, comprehensive coverage
2. **Integration Tests (20%)**: Component interactions, API endpoints
3. **End-to-End Tests (10%)**: Critical user journeys, system validation

### Quality Gates
- **Minimum Coverage**: 80% for backend, 75% for frontend
- **Performance**: All tests complete within 10 minutes
- **Reliability**: Test flakiness rate < 1%
- **Documentation**: All test scenarios documented

---

## Frontend Testing Specifications

### Technology Stack
- **Test Runner**: Vitest 1.0+
- **Testing Library**: React Testing Library 14+
- **E2E Framework**: Playwright 1.40+
- **Mocking**: MSW (Mock Service Worker) 2.0+
- **Coverage**: c8 (built into Vitest)

### Project Structure
```
frontend/tests/
├── __mocks__/
│   ├── api/
│   ├── files/
│   └── websocket/
├── fixtures/
│   ├── documents/
│   ├── ontologies/
│   └── extractions/
├── unit/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   └── utils/
├── integration/
│   ├── api/
│   ├── workflows/
│   └── websocket/
├── e2e/
│   ├── document-upload.spec.ts
│   ├── ontology-creation.spec.ts
│   ├── data-extraction.spec.ts
│   └── visualization.spec.ts
├── setup.ts
└── test-utils.tsx
```

### Unit Testing Requirements

#### Component Testing
```typescript
// Example: Document Upload Component Test
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { DocumentUpload } from '@/components/document/DocumentUpload';
import { TestWrapper } from '../test-utils';

describe('DocumentUpload', () => {
  const mockOnUploadSuccess = vi.fn();
  const mockOnUploadError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render upload zone with drag and drop functionality', () => {
    render(
      <TestWrapper>
        <DocumentUpload
          onUploadSuccess={mockOnUploadSuccess}
          onUploadError={mockOnUploadError}
          maxFileSize={100 * 1024 * 1024}
          acceptedTypes={['application/pdf', 'text/plain']}
          multiple={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /browse files/i })).toBeInTheDocument();
  });

  it('should validate file types and reject invalid files', async () => {
    const invalidFile = new File(['content'], 'test.exe', { type: 'application/x-msdownload' });
    
    render(
      <TestWrapper>
        <DocumentUpload
          onUploadSuccess={mockOnUploadSuccess}
          onUploadError={mockOnUploadError}
          maxFileSize={100 * 1024 * 1024}
          acceptedTypes={['application/pdf']}
          multiple={false}
        />
      </TestWrapper>
    );

    const input = screen.getByLabelText(/file upload/i);
    fireEvent.change(input, { target: { files: [invalidFile] } });

    await waitFor(() => {
      expect(mockOnUploadError).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'INVALID_FILE_TYPE',
          message: expect.stringContaining('exe')
        })
      );
    });
  });

  it('should show upload progress and handle completion', async () => {
    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    
    render(
      <TestWrapper>
        <DocumentUpload
          onUploadSuccess={mockOnUploadSuccess}
          onUploadError={mockOnUploadError}
          maxFileSize={100 * 1024 * 1024}
          acceptedTypes={['application/pdf']}
          multiple={false}
        />
      </TestWrapper>
    );

    const input = screen.getByLabelText(/file upload/i);
    fireEvent.change(input, { target: { files: [validFile] } });

    // Verify progress indicator appears
    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    // Verify success callback is called
    await waitFor(() => {
      expect(mockOnUploadSuccess).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'test.pdf',
            type: 'application/pdf'
          })
        ])
      );
    }, { timeout: 5000 });
  });
});
```

#### Hook Testing
```typescript
// Example: Custom Hook Test
import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useWebSocket } from '@/hooks/useWebSocket';
import { TestWrapper } from '../test-utils';

describe('useWebSocket', () => {
  it('should establish connection and handle messages', async () => {
    const mockWebSocket = vi.fn().mockImplementation(() => ({
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      send: vi.fn(),
      close: vi.fn(),
      readyState: WebSocket.CONNECTING
    }));
    
    vi.stubGlobal('WebSocket', mockWebSocket);

    const { result } = renderHook(
      () => useWebSocket('ws://localhost:8000/ws'),
      { wrapper: TestWrapper }
    );

    expect(result.current.connectionStatus).toBe('connecting');
    
    // Simulate connection open
    act(() => {
      const ws = mockWebSocket.mock.results[0].value;
      ws.readyState = WebSocket.OPEN;
      ws.addEventListener.mock.calls
        .find(([event]) => event === 'open')[1]();
    });

    expect(result.current.connectionStatus).toBe('connected');
  });
});
```

#### Service Testing
```typescript
// Example: API Service Test
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { DocumentService } from '@/services/documentService';

const server = setupServer(
  rest.post('http://localhost:8000/api/v1/documents/upload', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: 'doc-123',
        filename: 'test.pdf',
        status: 'uploaded',
        created_at: '2025-01-01T00:00:00Z'
      })
    );
  })
);

describe('DocumentService', () => {
  beforeEach(() => server.listen());
  afterEach(() => server.resetHandlers());

  it('should upload document successfully', async () => {
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const service = new DocumentService();

    const result = await service.uploadDocument(file);

    expect(result).toEqual({
      id: 'doc-123',
      filename: 'test.pdf',
      status: 'uploaded',
      created_at: '2025-01-01T00:00:00Z'
    });
  });

  it('should handle upload errors gracefully', async () => {
    server.use(
      rest.post('http://localhost:8000/api/v1/documents/upload', (req, res, ctx) => {
        return res(ctx.status(400), ctx.json({ detail: 'File too large' }));
      })
    );

    const file = new File(['x'.repeat(200 * 1024 * 1024)], 'large.pdf');
    const service = new DocumentService();

    await expect(service.uploadDocument(file)).rejects.toThrow('File too large');
  });
});
```

### Integration Testing

#### API Integration Tests
```typescript
// Example: Full workflow integration test
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { App } from '@/App';
import { setupServer } from 'msw/node';
import { documentHandlers, ontologyHandlers, extractionHandlers } from '../__mocks__/api';

const server = setupServer(...documentHandlers, ...ontologyHandlers, ...extractionHandlers);

describe('Document to Extraction Workflow', () => {
  beforeAll(() => server.listen());
  afterAll(() => server.close());

  it('should complete full workflow from document upload to data extraction', async () => {
    render(<App />);

    // Step 1: Upload document
    const file = new File(['Sample document content'], 'test.pdf', { type: 'application/pdf' });
    const uploadInput = screen.getByLabelText(/upload/i);
    fireEvent.change(uploadInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
    });

    // Step 2: Generate ontology
    const generateBtn = screen.getByRole('button', { name: /generate ontology/i });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(screen.getByText(/ontology generated/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // Step 3: Review and edit ontology
    const ontologyTable = screen.getByRole('table');
    expect(ontologyTable).toBeInTheDocument();
    
    const approveBtn = screen.getByRole('button', { name: /approve ontology/i });
    fireEvent.click(approveBtn);

    // Step 4: Start data extraction
    const extractBtn = screen.getByRole('button', { name: /extract data/i });
    fireEvent.click(extractBtn);

    await waitFor(() => {
      expect(screen.getByText(/extraction complete/i)).toBeInTheDocument();
    }, { timeout: 15000 });

    // Step 5: View results
    const resultsSection = screen.getByTestId('extraction-results');
    expect(resultsSection).toBeInTheDocument();
    expect(screen.getByText(/nodes:/i)).toBeInTheDocument();
    expect(screen.getByText(/relationships:/i)).toBeInTheDocument();
  });
});
```

### End-to-End Testing

#### Critical User Journeys
```typescript
// e2e/document-upload.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Document Upload Flow', () => {
  test('should upload PDF document and show processing status', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/sample.pdf');

    // Verify upload progress
    await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();

    // Wait for processing completion
    await expect(page.locator('[data-testid="processing-complete"]')).toBeVisible({
      timeout: 30000
    });

    // Verify document appears in list
    await expect(page.locator('[data-testid="document-list"]')).toContainText('sample.pdf');
  });

  test('should handle upload errors gracefully', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Try to upload unsupported file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/unsupported.exe');

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText(
      'Unsupported file type'
    );
  });
});

// e2e/ontology-creation.spec.ts
test.describe('Ontology Creation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: Upload a document first
    await page.goto('http://localhost:3000');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/sample.pdf');
    await expect(page.locator('[data-testid="processing-complete"]')).toBeVisible();
  });

  test('should generate ontology from uploaded document', async ({ page }) => {
    // Start ontology generation
    await page.click('[data-testid="generate-ontology-btn"]');

    // Wait for generation to complete
    await expect(page.locator('[data-testid="ontology-table"]')).toBeVisible({
      timeout: 60000
    });

    // Verify ontology entries
    const ontologyRows = page.locator('[data-testid="ontology-row"]');
    await expect(ontologyRows).toHaveCount.greaterThan(0);

    // Test editing functionality
    await page.click('[data-testid="edit-ontology-btn"]');
    await page.fill('[data-testid="entity-type-input"]', 'UpdatedEntity');
    await page.click('[data-testid="save-changes-btn"]');

    // Verify changes saved
    await expect(page.locator('text=UpdatedEntity')).toBeVisible();
  });
});
```

### Mock Service Worker Setup

#### API Mocks
```typescript
// __mocks__/api/documentHandlers.ts
import { rest } from 'msw';

export const documentHandlers = [
  rest.post('http://localhost:8000/api/v1/documents/upload', async (req, res, ctx) => {
    const formData = await req.formData();
    const file = formData.get('file') as File;
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return res(
      ctx.status(200),
      ctx.json({
        id: 'doc-' + Date.now(),
        filename: file.name,
        size: file.size,
        type: file.type,
        status: 'processed',
        created_at: new Date().toISOString()
      })
    );
  }),

  rest.get('http://localhost:8000/api/v1/documents/:id', (req, res, ctx) => {
    const { id } = req.params;
    
    return res(
      ctx.status(200),
      ctx.json({
        id,
        filename: 'sample.pdf',
        size: 1024000,
        type: 'application/pdf',
        status: 'processed',
        processed_content: 'Sample document content for testing...',
        created_at: '2025-01-01T00:00:00Z'
      })
    );
  })
];

// __mocks__/api/ontologyHandlers.ts
export const ontologyHandlers = [
  rest.post('http://localhost:8000/api/v1/ontologies/generate', (req, res, ctx) => {
    // Simulate long-running ontology generation
    return res(
      ctx.status(200),
      ctx.json({
        id: 'onto-123',
        status: 'processing',
        document_id: 'doc-123',
        progress: 0,
        created_at: new Date().toISOString()
      })
    );
  }),

  rest.get('http://localhost:8000/api/v1/ontologies/:id/status', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: req.params.id,
        status: 'completed',
        progress: 100,
        ontology: [
          {
            id: '1',
            subject: {
              entity_type: 'Person',
              type_variations: ['Individual', 'Employee'],
              primitive_type: 'string'
            },
            relationship: {
              relationship_type: 'works_for',
              type_variations: ['employed_by', 'works_at']
            },
            object: {
              entity_type: 'Organization',
              type_variations: ['Company', 'Employer'],
              primitive_type: 'string'
            }
          }
        ]
      })
    );
  })
];
```

### Test Data Fixtures

#### Sample Documents
```typescript
// fixtures/documents.ts
export const sampleDocuments = {
  pdf: {
    name: 'employee-handbook.pdf',
    type: 'application/pdf',
    content: `
      EMPLOYEE HANDBOOK
      
      John Smith works for TechCorp as a Software Engineer.
      He earns $120,000 annually and reports to Sarah Johnson.
      
      The company is located in San Francisco, California.
      TechCorp was founded in 2010 and has 500 employees.
    `
  },
  
  text: {
    name: 'research-paper.txt',
    type: 'text/plain',
    content: `
      Title: AI in Healthcare
      Author: Dr. Jane Doe
      Institution: Medical University
      
      Artificial Intelligence is revolutionizing healthcare.
      Machine learning algorithms can diagnose diseases.
      Natural language processing helps analyze medical records.
    `
  }
};

export const expectedOntologies = {
  employeeHandbook: [
    {
      subject: { entity_type: 'Person', type_variations: ['Employee'], primitive_type: 'string' },
      relationship: { relationship_type: 'works_for', type_variations: ['employed_by'] },
      object: { entity_type: 'Organization', type_variations: ['Company'], primitive_type: 'string' }
    },
    {
      subject: { entity_type: 'Person', type_variations: ['Employee'], primitive_type: 'string' },
      relationship: { relationship_type: 'earns', type_variations: ['salaried_at'] },
      object: { entity_type: 'Salary', type_variations: ['Compensation'], primitive_type: 'float' }
    }
  ]
};
```

---

## Backend Testing Specifications

### Technology Stack
- **Test Framework**: pytest 7.4+
- **Async Testing**: pytest-asyncio 0.21+
- **API Testing**: httpx 0.25+
- **Database Testing**: pytest-postgresql, SQLAlchemy factories
- **Mocking**: pytest-mock, responses
- **Coverage**: pytest-cov

### Project Structure
```
backend/tests/
├── conftest.py
├── fixtures/
│   ├── documents/
│   ├── ontologies/
│   └── database/
├── mocks/
│   ├── llm_responses/
│   ├── graph_data/
│   └── database_data/
├── unit/
│   ├── agents/
│   ├── services/
│   ├── models/
│   └── utils/
├── integration/
│   ├── api/
│   ├── database/
│   └── llm/
├── e2e/
│   ├── workflows/
│   └── performance/
└── load/
    ├── stress_tests/
    └── performance_benchmarks/
```

### Unit Testing Requirements

#### Agent Testing
```python
# tests/unit/agents/test_ontology_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.ontology_agent import OntologyCreationAgent, OntologyState
from app.services.llm_service import LLMService

@pytest.fixture
def mock_llm_service():
    llm_service = MagicMock(spec=LLMService)
    llm_service.extract_ontology_from_chunk = AsyncMock()
    return llm_service

@pytest.fixture
def ontology_agent(mock_llm_service):
    return OntologyCreationAgent(mock_llm_service)

@pytest.mark.asyncio
async def test_ontology_creation_single_chunk(ontology_agent, mock_llm_service):
    """Test ontology creation from a single document chunk."""
    
    # Setup
    mock_llm_service.extract_ontology_from_chunk.return_value = {
        "entities": [
            {"type": "Person", "variations": ["Individual"], "primitive_type": "string"},
            {"type": "Company", "variations": ["Organization"], "primitive_type": "string"}
        ],
        "relationships": [
            {"type": "works_for", "variations": ["employed_by"]}
        ]
    }
    
    initial_state = OntologyState(
        document_chunks=["John Smith works for TechCorp as a developer."],
        entities=[],
        relationships=[],
        ontology=[],
        current_chunk=0,
        total_chunks=1
    )
    
    # Execute
    result = await ontology_agent.process_document(initial_state)
    
    # Verify
    assert result.status == "completed"
    assert len(result.ontology) > 0
    assert any(entry["subject"]["entity_type"] == "Person" for entry in result.ontology)
    assert any(entry["object"]["entity_type"] == "Company" for entry in result.ontology)
    mock_llm_service.extract_ontology_from_chunk.assert_called_once()

@pytest.mark.asyncio
async def test_ontology_deduplication(ontology_agent, mock_llm_service):
    """Test that duplicate entities and relationships are properly deduplicated."""
    
    # Setup with duplicate responses
    mock_llm_service.extract_ontology_from_chunk.side_effect = [
        {
            "entities": [{"type": "Person", "variations": ["Individual"], "primitive_type": "string"}],
            "relationships": [{"type": "works_for", "variations": ["employed_by"]}]
        },
        {
            "entities": [{"type": "Person", "variations": ["Employee"], "primitive_type": "string"}],
            "relationships": [{"type": "works_for", "variations": ["works_at"]}]
        }
    ]
    
    initial_state = OntologyState(
        document_chunks=["Chunk 1", "Chunk 2"],
        entities=[],
        relationships=[],
        ontology=[],
        current_chunk=0,
        total_chunks=2
    )
    
    # Execute
    result = await ontology_agent.process_document(initial_state)
    
    # Verify deduplication
    person_entities = [e for e in result.entities if e["type"] == "Person"]
    assert len(person_entities) == 1
    assert set(person_entities[0]["variations"]) == {"Individual", "Employee"}
    
    works_for_relationships = [r for r in result.relationships if r["type"] == "works_for"]
    assert len(works_for_relationships) == 1
    assert set(works_for_relationships[0]["variations"]) == {"employed_by", "works_at"}
```

#### Service Testing
```python
# tests/unit/services/test_document_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.document_service import DocumentService
from app.models.document import Document

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=AsyncSession)

@pytest.fixture
def document_service():
    return DocumentService()

@pytest.mark.asyncio
async def test_upload_document_success(document_service, mock_db_session):
    """Test successful document upload."""
    
    # Setup
    file_content = b"Sample PDF content"
    upload_file = MagicMock(spec=UploadFile)
    upload_file.filename = "test.pdf"
    upload_file.content_type = "application/pdf"
    upload_file.size = len(file_content)
    upload_file.read = AsyncMock(return_value=file_content)
    
    # Mock database operations
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()
    
    # Execute
    result = await document_service.upload_document(upload_file, "user-123", mock_db_session)
    
    # Verify
    assert result.filename == "test.pdf"
    assert result.content_type == "application/pdf"
    assert result.processing_status == "uploaded"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_upload_document_invalid_type(document_service, mock_db_session):
    """Test document upload with invalid file type."""
    
    # Setup
    upload_file = MagicMock(spec=UploadFile)
    upload_file.filename = "malware.exe"
    upload_file.content_type = "application/x-executable"
    
    # Execute & Verify
    with pytest.raises(ValueError, match="Unsupported file type"):
        await document_service.upload_document(upload_file, "user-123", mock_db_session)

@pytest.mark.asyncio
async def test_process_document_content(document_service):
    """Test document content processing."""
    
    # Setup
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nSample text content"
    
    # Execute
    processed_text = await document_service.extract_text_from_pdf(pdf_content)
    
    # Verify
    assert isinstance(processed_text, str)
    assert len(processed_text) > 0
```

#### API Testing
```python
# tests/integration/api/test_documents_api.py
import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from tests.fixtures.auth import create_test_user, get_auth_headers

@pytest.mark.asyncio
async def test_upload_document_api(async_client: AsyncClient, test_user, auth_headers):
    """Test document upload API endpoint."""
    
    # Prepare test file
    file_content = b"Sample document content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    # Make request
    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        headers=auth_headers
    )
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["content_type"] == "application/pdf"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_document_api(async_client: AsyncClient, test_user, auth_headers, sample_document):
    """Test retrieve document API endpoint."""
    
    # Make request
    response = await async_client.get(
        f"/api/v1/documents/{sample_document.id}",
        headers=auth_headers
    )
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(sample_document.id)
    assert data["filename"] == sample_document.filename

@pytest.mark.asyncio
async def test_upload_document_unauthorized(async_client: AsyncClient):
    """Test document upload without authentication."""
    
    file_content = b"Sample document content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    
    # Make request without auth headers
    response = await async_client.post("/api/v1/documents/upload", files=files)
    
    # Verify unauthorized response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

### Mock LLM Responses

#### LLM Response Fixtures
```python
# tests/mocks/llm_responses.py
SAMPLE_ONTOLOGY_RESPONSE = {
    "entities": [
        {
            "type": "Person", 
            "variations": ["Individual", "Employee", "Worker"],
            "primitive_type": "string"
        },
        {
            "type": "Organization",
            "variations": ["Company", "Corporation", "Business"],
            "primitive_type": "string"
        },
        {
            "type": "Salary",
            "variations": ["Compensation", "Pay", "Wages"],
            "primitive_type": "float"
        },
        {
            "type": "Location",
            "variations": ["Place", "Address", "City"],
            "primitive_type": "string"
        }
    ],
    "relationships": [
        {
            "type": "works_for",
            "variations": ["employed_by", "works_at", "hired_by"]
        },
        {
            "type": "earns",
            "variations": ["paid", "receives", "compensated_with"]
        },
        {
            "type": "located_in",
            "variations": ["based_in", "situated_in", "found_in"]
        }
    ]
}

SAMPLE_EXTRACTION_RESPONSE = {
    "nodes": [
        {
            "id": "person_1",
            "type": "Person",
            "properties": {
                "name": "John Smith",
                "title": "Software Engineer"
            },
            "document_location": {
                "start_position": 45,
                "end_position": 55,
                "text_snippet": "John Smith works"
            }
        },
        {
            "id": "org_1", 
            "type": "Organization",
            "properties": {
                "name": "TechCorp",
                "industry": "Technology"
            },
            "document_location": {
                "start_position": 60,
                "end_position": 68,
                "text_snippet": "for TechCorp as"
            }
        }
    ],
    "relationships": [
        {
            "id": "rel_1",
            "type": "works_for",
            "source": "person_1",
            "target": "org_1",
            "properties": {
                "position": "Software Engineer",
                "start_date": "2023-01-01"
            },
            "document_location": {
                "start_position": 45,
                "end_position": 75,
                "text_snippet": "John Smith works for TechCorp"
            }
        }
    ]
}

# Mock LLM service
class MockLLMService:
    async def extract_ontology_from_chunk(self, chunk: str, existing_entities=None, existing_relationships=None):
        """Return consistent mock ontology response."""
        return SAMPLE_ONTOLOGY_RESPONSE
    
    async def extract_graph_data(self, chunk: str, ontology: list):
        """Return consistent mock extraction response.""" 
        return SAMPLE_EXTRACTION_RESPONSE
```

### Performance Testing

#### Load Testing
```python
# tests/load/test_api_performance.py
import asyncio
import time
from httpx import AsyncClient
from app.main import app

async def load_test_document_upload():
    """Test document upload under load."""
    
    async def upload_document(client, file_data):
        start_time = time.time()
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": file_data},
            headers={"Authorization": "Bearer test-token"}
        )
        end_time = time.time()
        return {
            "status_code": response.status_code,
            "response_time": end_time - start_time
        }
    
    # Simulate 50 concurrent uploads
    file_data = ("test.pdf", b"x" * 1024 * 100, "application/pdf")  # 100KB file
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        tasks = [upload_document(client, file_data) for _ in range(50)]
        results = await asyncio.gather(*tasks)
    
    # Analyze results
    success_count = sum(1 for r in results if r["status_code"] == 200)
    avg_response_time = sum(r["response_time"] for r in results) / len(results)
    max_response_time = max(r["response_time"] for r in results)
    
    assert success_count / len(results) >= 0.95  # 95% success rate
    assert avg_response_time < 2.0  # Average under 2 seconds
    assert max_response_time < 5.0  # Max under 5 seconds
```

### Test Configuration

#### pytest Configuration
```python
# conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.core.database import get_db
from app.core.config import get_settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def db_session():
    """Create test database session."""
    settings = get_settings()
    engine = create_async_engine(settings.test_database_url, echo=True)
    
    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
def override_get_db(db_session):
    """Override database dependency for testing."""
    def _override():
        return db_session
    
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()
```

## Continuous Integration Testing

### GitHub Actions Workflow
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run unit tests
        run: cd frontend && npm run test:coverage
      - name: Run E2E tests
        run: cd frontend && npm run test:e2e
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: cd backend && pip install -r requirements.txt
      - name: Run unit tests
        run: cd backend && pytest tests/unit --cov=app
      - name: Run integration tests
        run: cd backend && pytest tests/integration
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        
  e2e-tests:
    needs: [frontend-tests, backend-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Wait for services
        run: ./scripts/wait-for-services.sh
      - name: Run E2E tests
        run: npm run test:e2e:full
      - name: Cleanup
        run: docker-compose -f docker-compose.test.yml down
```

This comprehensive testing specification ensures high-quality, reliable software delivery with extensive coverage of all system components and user workflows.