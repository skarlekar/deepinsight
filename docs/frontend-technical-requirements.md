# Frontend Technical Requirements

## Overview
The DeepInsight frontend is a React-based web application that provides an intuitive, accessible interface for document upload, ontology management, data extraction, and visualization of extracted knowledge graphs. The frontend communicates directly with the FastAPI backend via HTTP/HTTPS and WebSocket connections.

## Technology Stack

### Core Technologies
- **Framework**: React 18.2+
- **Language**: TypeScript 5.0+
- **Build Tool**: Vite 5.0+
- **Package Manager**: npm
- **Node.js**: 18.0+

### UI Framework & Styling
- **UI Library**: Material-UI (MUI) v5.14+
- **Icons**: MUI Icons
- **Styling**: Emotion (built into MUI) + CSS Modules for custom styles
- **Theme**: Material Design 3 with dark/light mode support
- **Responsive Design**: Mobile-first approach with MUI breakpoints

### State Management & Data Flow
- **State Management**: Zustand 4.4+ for client state
- **Server State**: TanStack Query v5 (React Query)
- **HTTP Client**: Axios 1.6+ with interceptors
- **Form Management**: React Hook Form 7.47+ with Zod validation
- **WebSocket**: Native WebSocket API with automatic reconnection

### Visualization & File Handling
- **Graph Visualization**: vis.js network 9.1+ (replacing pyvis.network)
- **File Upload**: react-dropzone 14.2+
- **Data Grid**: MUI Data Grid Pro
- **Charts**: Recharts 2.8+ for analytics dashboards

## Application Structure

### Project Structure
```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── NotificationSystem.tsx
│   │   ├── document/
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   └── DocumentViewer.tsx
│   │   ├── ontology/
│   │   │   ├── OntologyEditor.tsx
│   │   │   ├── OntologyViewer.tsx
│   │   │   └── OntologyTemplates.tsx
│   │   ├── extraction/
│   │   │   ├── ExtractionConfig.tsx
│   │   │   ├── ExtractionProgress.tsx
│   │   │   └── ExtractionResults.tsx
│   │   └── visualization/
│   │       ├── NetworkGraph.tsx
│   │       ├── GraphControls.tsx
│   │       └── GraphLegend.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Documents.tsx
│   │   ├── Ontologies.tsx
│   │   ├── Extractions.tsx
│   │   └── Settings.tsx
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useDocuments.ts
│   │   ├── useOntologies.ts
│   │   └── useExtractions.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── documentService.ts
│   │   ├── ontologyService.ts
│   │   ├── extractionService.ts
│   │   └── websocketService.ts
│   ├── types/
│   │   ├── api.ts
│   │   ├── document.ts
│   │   ├── ontology.ts
│   │   ├── extraction.ts
│   │   └── graph.ts
│   ├── utils/
│   │   ├── validation.ts
│   │   ├── formatters.ts
│   │   ├── constants.ts
│   │   └── errorHandling.ts
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── settingsStore.ts
│   ├── styles/
│   │   ├── theme.ts
│   │   ├── globals.css
│   │   └── components.css
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── package.json
├── tsconfig.json
├── vite.config.ts
├── vitest.config.ts
└── .env.example
```

## Feature Requirements

### 1. Document Upload & Management

#### Document Upload Component
- **File Types**: PDF, DOCX, TXT, MD (with mime type validation)
- **Upload Methods**: Drag-and-drop, file browser, paste from clipboard
- **File Validation**: Size limits (100MB max), type checking, content scanning
- **Progress Tracking**: Real-time upload progress with cancel functionality
- **Batch Upload**: Multiple file selection with queue management

#### Technical Specifications
```typescript
interface DocumentUploadProps {
  onUploadSuccess: (files: UploadedFile[]) => void;
  onUploadError: (error: UploadError) => void;
  onUploadProgress: (progress: UploadProgress) => void;
  maxFileSize: number;
  acceptedTypes: string[];
  multiple: boolean;
  disabled?: boolean;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: 'uploading' | 'processing' | 'processed' | 'error';
  processingProgress?: number;
  errorMessage?: string;
}

interface UploadProgress {
  fileId: string;
  progress: number; // 0-100
  stage: 'uploading' | 'validating' | 'processing';
  estimatedTimeRemaining?: number;
}
```

#### UI Requirements
- **Drag-and-drop Zone**: Visual feedback with hover states
- **File Preview**: Thumbnails and metadata display
- **Progress Indicators**: Individual and batch progress bars
- **Error Handling**: Clear error messages with retry options
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### 2. Ontology Management Interface

#### Ontology Creator
- **Auto-Generation**: One-click ontology creation from uploaded documents
- **Real-time Updates**: Live progress tracking with WebSocket connection
- **Progress Visualization**: Step-by-step progress with detailed status
- **Background Processing**: Non-blocking UI during generation

#### Ontology Editor
- **CRUD Operations**: Add, edit, delete ontology entries with validation
- **Bulk Operations**: Select multiple entries for batch actions
- **Search & Filter**: Real-time search with advanced filtering
- **Import/Export**: JSON file import/export with validation
- **Version Control**: Save multiple ontology versions with diff view

#### Technical Specifications
```typescript
interface OntologyEntry {
  id: string;
  subject: {
    entity_type: string;
    type_variations: string[];
    primitive_type: 'string' | 'float' | 'integer' | 'boolean';
  };
  relationship: {
    relationship_type: string;
    type_variations: string[];
  };
  object: {
    entity_type: string;
    type_variations: string[];
    primitive_type: 'string' | 'float' | 'integer' | 'boolean';
  };
  created_at: Date;
  updated_at: Date;
  confidence_score?: number;
  source_location?: DocumentLocation;
}

interface OntologyEditorProps {
  ontology: OntologyEntry[];
  onUpdate: (ontology: OntologyEntry[]) => void;
  onExport: (format: 'json' | 'csv') => void;
  onImport: (file: File) => Promise<void>;
  isReadOnly?: boolean;
  allowBulkOperations?: boolean;
}
```

#### Advanced Features
- **Smart Suggestions**: AI-powered suggestions for missing relationships
- **Validation Rules**: Real-time validation with error highlighting
- **Template System**: Pre-built ontology templates for common domains
- **Collaboration**: Real-time collaborative editing (future enhancement)

### 3. Data Extraction Interface

#### Extraction Configuration
- **Ontology Selection**: Dropdown with search and preview
- **Parameter Tuning**: Advanced settings with tooltips and validation
- **Batch Processing**: Multiple document extraction with queue management
- **Target Database**: Neo4j, Neptune, or both formats

#### Extraction Progress
- **Real-time Updates**: WebSocket-based live progress tracking
- **Detailed Status**: Current step, progress percentage, time estimates
- **Cancellation Support**: Ability to cancel long-running extractions
- **Log Viewer**: Expandable log display with filtering and search

#### Technical Specifications
```typescript
interface ExtractionConfig {
  documentId: string;
  ontologyId: string;
  parameters: {
    chunkSize: number; // 500-2000
    overlapPercentage: number; // 0-50%
    confidenceThreshold: number; // 0.0-1.0
    maxRetries: number; // 1-5
    enableParallelProcessing: boolean;
  };
  exportFormats: Array<'neo4j' | 'neptune'>;
  notificationPreferences: {
    onCompletion: boolean;
    onError: boolean;
    emailNotification: boolean;
  };
}

interface ExtractionProgress {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  currentStep: string;
  progress: number; // 0-100
  stepsCompleted: number;
  totalSteps: number;
  startedAt: Date;
  completedAt?: Date;
  estimatedTimeRemaining?: number;
  logs: ExtractionLog[];
  results?: ExtractionResults;
  errors?: ExtractionError[];
}
```

#### Real-time Features
- **Progress Notifications**: Toast notifications for status changes
- **Background Processing**: Continue extraction while navigating
- **Queue Management**: View and manage multiple extraction jobs
- **Result Preview**: Live preview of extracted entities and relationships

### 4. Network Visualization

#### Graph Display
- **Interactive Visualization**: Pan, zoom, select nodes/edges with vis.js
- **Layout Algorithms**: Force-directed, hierarchical, circular layouts
- **Customization**: Node size, color, labels based on properties
- **Edge Styling**: Different styles for relationship types
- **Performance**: Virtualization for large graphs (10k+ nodes)

#### Advanced Visualization Features
- **Clustering**: Automatic node clustering for large graphs
- **Filtering**: Interactive filters for nodes and relationships
- **Search**: Global search with highlighting and focus
- **Export Options**: PNG, SVG, PDF export with high resolution
- **Mini-map**: Overview panel for large graph navigation

#### Technical Specifications
```typescript
interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
  position?: { x: number; y: number };
  documentLocation?: {
    page?: number;
    position: { start: number; end: number };
    snippet: string;
  };
  size?: number;
  color?: string;
  shape?: 'circle' | 'box' | 'diamond' | 'triangle';
}

interface GraphEdge {
  id: string;
  from: string;
  to: string;
  label: string;
  type: string;
  properties: Record<string, any>;
  documentLocation?: {
    page?: number;
    position: { start: number; end: number };
    snippet: string;
  };
  width?: number;
  color?: string;
  dashes?: boolean;
}

interface NetworkVisualizationProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeSelect: (node: GraphNode) => void;
  onEdgeSelect: (edge: GraphEdge) => void;
  onNodeDoubleClick: (node: GraphNode) => void;
  layoutType: 'force' | 'hierarchical' | 'circular';
  showLabels: boolean;
  enableClustering: boolean;
  filterOptions: FilterOptions;
  searchQuery: string;
}
```

### 5. Database Integration

#### Connection Management
- **Connection Testing**: Real-time connectivity validation
- **Credential Security**: Encrypted storage with masked display
- **Multi-Environment**: Development, staging, production profiles
- **Connection Pooling**: Optimized connection management

#### Data Loading Interface
- **Preview Mode**: Sample data preview before import
- **Validation**: Comprehensive data integrity checking
- **Progress Tracking**: Real-time import progress with statistics
- **Rollback**: Ability to undo imports with confirmation dialogs

#### Technical Specifications
```typescript
interface DatabaseConnection {
  id: string;
  type: 'neo4j' | 'neptune';
  name: string;
  config: Neo4jConfig | NeptuneConfig;
  isActive: boolean;
  lastTested?: Date;
  testResult?: ConnectionTestResult;
}

interface Neo4jConfig {
  uri: string;
  username: string;
  password: string; // encrypted client-side
  database?: string;
  encrypted: boolean;
}

interface NeptuneConfig {
  endpoint: string;
  region: string;
  accessKeyId: string;
  secretAccessKey: string; // encrypted client-side
}

interface ImportProgress {
  totalRecords: number;
  processedRecords: number;
  successfulRecords: number;
  failedRecords: number;
  currentOperation: string;
  errors: ImportError[];
  estimatedTimeRemaining?: number;
}
```

## API Integration

### Direct FastAPI Communication
- **Base URL**: Configurable via environment variables
- **Authentication**: JWT token-based with automatic refresh
- **Error Handling**: Centralized error handling with user notifications
- **Retry Logic**: Exponential backoff for failed requests
- **Request Cancellation**: AbortController for long-running requests

### WebSocket Integration
```typescript
interface WebSocketService {
  connect(userId: string): Promise<void>;
  disconnect(): void;
  subscribe(event: string, callback: (data: any) => void): void;
  unsubscribe(event: string): void;
  send(event: string, data: any): void;
  getConnectionStatus(): 'connecting' | 'connected' | 'disconnected' | 'error';
}

// WebSocket Events
type WebSocketEvent = 
  | 'extraction_progress'
  | 'extraction_complete'
  | 'extraction_error'
  | 'ontology_generated'
  | 'document_processed'
  | 'system_notification';
```

### API Endpoints
```typescript
// Document endpoints
const documentAPI = {
  upload: (file: File) => Promise<Document>,
  getAll: () => Promise<Document[]>,
  getById: (id: string) => Promise<Document>,
  delete: (id: string) => Promise<void>,
  getContent: (id: string) => Promise<string>
};

// Ontology endpoints  
const ontologyAPI = {
  generate: (documentId: string, config: GenerationConfig) => Promise<string>,
  getAll: () => Promise<Ontology[]>,
  getById: (id: string) => Promise<Ontology>,
  update: (id: string, ontology: Ontology) => Promise<Ontology>,
  delete: (id: string) => Promise<void>,
  export: (id: string, format: 'json' | 'csv') => Promise<Blob>
};

// Extraction endpoints
const extractionAPI = {
  start: (config: ExtractionConfig) => Promise<string>,
  getStatus: (id: string) => Promise<ExtractionProgress>,
  getResults: (id: string) => Promise<ExtractionResults>,
  cancel: (id: string) => Promise<void>,
  export: (id: string, format: 'neo4j' | 'neptune') => Promise<Blob>
};
```

## Performance Requirements

### Loading Performance
- **Initial Load**: < 2 seconds for application shell
- **Code Splitting**: Lazy loading for all page components
- **Bundle Size**: < 500KB compressed for initial bundle
- **Resource Optimization**: Image compression, font subsetting

### Runtime Performance
- **UI Responsiveness**: < 100ms for all interactions
- **Large Dataset Handling**: Virtual scrolling for 1000+ items
- **Memory Management**: < 100MB heap size for typical operations
- **Network Optimization**: Request deduplication, response caching

### Graph Visualization Performance
- **Large Graphs**: Efficient rendering for 10,000+ nodes
- **Smooth Interactions**: 60fps pan/zoom operations
- **Layout Calculation**: Background web worker processing
- **Memory Optimization**: Node/edge virtualization

## Mobile & Responsive Design

### Responsive Breakpoints
```typescript
const breakpoints = {
  mobile: '320px-767px',
  tablet: '768px-1023px',
  desktop: '1024px-1439px',
  large: '1440px+'
};
```

### Mobile-Specific Features
- **Touch Optimization**: Touch-friendly controls and gestures
- **Responsive Navigation**: Collapsible sidebar and mobile menu
- **File Upload**: Camera integration for document capture
- **Offline Support**: Basic offline functionality with service workers

### Tablet Optimizations
- **Split View**: Side-by-side ontology editing and graph view
- **Gesture Support**: Pinch-to-zoom, swipe navigation
- **Adaptive UI**: Dynamic layout based on orientation

## Error Handling & Recovery

### Error Boundary Implementation
```typescript
class AppErrorBoundary extends Component<Props, State> {
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error with context
    logError(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: 'AppErrorBoundary',
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    });
  }
}
```

### Error Recovery Strategies
- **Automatic Retry**: Failed API requests with exponential backoff
- **Graceful Degradation**: Fallback UI when features fail
- **User Notification**: Clear error messages with action options
- **State Recovery**: Restore application state after errors

## Testing Requirements

### Unit Testing (80% Coverage)
```typescript
// Example test structure
describe('DocumentUpload', () => {
  it('should validate file types correctly', () => {});
  it('should handle upload progress updates', () => {});
  it('should display error messages appropriately', () => {});
});
```

### Integration Testing
- **API Integration**: Mock backend responses with MSW
- **WebSocket Testing**: Mock real-time communication
- **File Upload**: Test with various file types and sizes
- **Error Scenarios**: Network failures, validation errors

### End-to-End Testing (Playwright)
```typescript
// Critical user journeys
test('Complete ontology creation workflow', async ({ page }) => {
  // Upload document → Generate ontology → Edit → Save
});

test('Data extraction and visualization', async ({ page }) => {
  // Select ontology → Configure extraction → View results
});
```

### Accessibility Testing
- **Automated Testing**: axe-core integration in test suite
- **Keyboard Navigation**: Tab order and focus management
- **Screen Reader**: ARIA labels and semantic HTML
- **Color Contrast**: WCAG 2.1 AA compliance verification

## Security Requirements

### Client-Side Security
- **Content Security Policy**: Strict CSP headers
- **XSS Prevention**: Sanitization of all user input
- **Secure Storage**: No sensitive data in localStorage
- **HTTPS Enforcement**: Automatic HTTP to HTTPS redirect

### Authentication & Session Management
```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const authStore = create<AuthState>((set, get) => ({
  // Secure token handling with automatic refresh
  login: async (credentials) => {
    const response = await authAPI.login(credentials);
    set({ 
      user: response.user,
      accessToken: response.accessToken,
      refreshToken: response.refreshToken,
      isAuthenticated: true 
    });
  },
  
  refreshAccessToken: async () => {
    // Automatic token refresh logic
  }
}));
```

## Browser Support & Compatibility

### Supported Browsers
- **Chrome**: 100+ (Primary target)
- **Firefox**: 100+
- **Safari**: 15+
- **Edge**: 100+

### Progressive Enhancement
- **Core Functionality**: Works in all supported browsers
- **Enhanced Features**: Advanced features for modern browsers
- **Polyfills**: Minimal polyfills for compatibility
- **Feature Detection**: Runtime feature detection

## Build & Development

### Development Environment
```json
{
  "scripts": {
    "dev": "vite --host",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:e2e": "playwright test",
    "lint": "eslint src/ --ext .ts,.tsx",
    "type-check": "tsc --noEmit",
    "format": "prettier --write src/"
  }
}
```

### Build Optimization
- **Tree Shaking**: Eliminate unused code
- **Code Splitting**: Route-based and component-based splitting
- **Asset Optimization**: Image compression, font subsetting
- **Bundle Analysis**: Regular bundle size monitoring

This enhanced frontend specification addresses all reviewer feedback with specific technology choices, comprehensive error handling, mobile responsiveness, and direct FastAPI communication while maintaining enterprise-grade quality and accessibility standards.