// DeepInsight Frontend Component Specifications
// Complete TypeScript interfaces for Figma design integration

import React from 'react';

// ============================================================================
// Core Data Types
// ============================================================================

export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  created_at: string;
  processed_at?: string;
  error_message?: string;
}

export interface EntityDefinition {
  entity_type: string;
  type_variations: string[];
  primitive_type: 'string' | 'integer' | 'float' | 'boolean';
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
  version: number;
  status: 'draft' | 'processing' | 'active' | 'archived';
  created_at: string;
  updated_at: string;
  triples?: OntologyTriple[];
}

export interface Extraction {
  id: string;
  user_id: string;
  document_id: string;
  ontology_id: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  created_at: string;
  completed_at?: string;
  nodes_count?: number;
  relationships_count?: number;
  neo4j_export_available?: boolean;
  neptune_export_available?: boolean;
  error_message?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
  source_location?: string;
  x?: number;
  y?: number;
}

export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
  source_location?: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// ============================================================================
// Theme & Design System
// ============================================================================

export interface TypographyStyle {
  fontFamily: string;
  fontSize: string;
  fontWeight: number | string;
  lineHeight: number | string;
  letterSpacing?: string;
}

export interface ThemeConfiguration {
  colors: {
    primary: string;           // #1976d2 - Material Blue 700
    primaryLight: string;      // #42a5f5 - Material Blue 400
    primaryDark: string;       // #1565c0 - Material Blue 800
    secondary: string;         // #dc004e - Material Pink A400
    secondaryLight: string;    // #ff5983 - Material Pink A200
    secondaryDark: string;     // #9a0036 - Material Pink A700
    error: string;             // #d32f2f - Material Red 700
    warning: string;           // #ed6c02 - Material Orange 700
    info: string;              // #0288d1 - Material Light Blue 700
    success: string;           // #2e7d32 - Material Green 700
    background: {
      default: string;         // #fafafa - Material Grey 50
      paper: string;           // #ffffff - White
      elevated: string;        // #ffffff with elevation shadow
    };
    text: {
      primary: string;         // rgba(0, 0, 0, 0.87)
      secondary: string;       // rgba(0, 0, 0, 0.6)
      disabled: string;        // rgba(0, 0, 0, 0.38)
    };
    divider: string;           // rgba(0, 0, 0, 0.12)
    grey: {
      50: string;              // #fafafa
      100: string;             // #f5f5f5
      200: string;             // #eeeeee
      300: string;             // #e0e0e0
      400: string;             // #bdbdbd
      500: string;             // #9e9e9e
      600: string;             // #757575
      700: string;             // #616161
      800: string;             // #424242
      900: string;             // #212121
    };
  };
  typography: {
    h1: TypographyStyle;       // 2.125rem (34px), weight 300
    h2: TypographyStyle;       // 1.5rem (24px), weight 400
    h3: TypographyStyle;       // 1.25rem (20px), weight 400
    h4: TypographyStyle;       // 1.125rem (18px), weight 500
    h5: TypographyStyle;       // 1rem (16px), weight 500
    h6: TypographyStyle;       // 0.875rem (14px), weight 500
    body1: TypographyStyle;    // 1rem (16px), weight 400
    body2: TypographyStyle;    // 0.875rem (14px), weight 400
    button: TypographyStyle;   // 0.875rem (14px), weight 500, uppercase
    caption: TypographyStyle;  // 0.75rem (12px), weight 400
    overline: TypographyStyle; // 0.75rem (12px), weight 400, uppercase
  };
  spacing: {
    unit: number;              // 8px base unit
    xs: number;                // 4px (0.5 * unit)
    sm: number;                // 8px (1 * unit)
    md: number;                // 16px (2 * unit)
    lg: number;                // 24px (3 * unit)
    xl: number;                // 32px (4 * unit)
    xxl: number;               // 48px (6 * unit)
  };
  breakpoints: {
    xs: number;                // 0px
    sm: number;                // 600px
    md: number;                // 900px
    lg: number;                // 1200px
    xl: number;                // 1536px
  };
  shadows: string[];           // Material Design elevation shadows
  zIndex: {
    drawer: number;            // 1200
    modal: number;             // 1300
    snackbar: number;          // 1400
    tooltip: number;           // 1500
  };
}

// ============================================================================
// Component Props Interfaces
// ============================================================================

// Document Upload Component
export interface DocumentUploadComponentProps {
  onFileSelect: (files: File[]) => void;
  onUploadProgress?: (progress: number) => void;
  onUploadComplete?: (document: Document) => void;
  onUploadError?: (error: string) => void;
  allowedTypes?: string[];
  maxFileSize?: number;
  multiple?: boolean;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  
  // Visual customization
  dragActiveColor?: string;
  borderStyle?: 'dashed' | 'solid';
  height?: number | string;
  showFileList?: boolean;
  acceptText?: string;
  helperText?: string;
}

// Interactive Ontology Editor Component
export interface OntologyEditorComponentProps {
  ontology?: Ontology;
  triples: OntologyTriple[];
  onChange: (triples: OntologyTriple[]) => void;
  onSave: () => Promise<void>;
  onExport: () => void;
  onImport: (file: File) => void;
  onAddTriple: () => void;
  onDeleteTriple: (index: number) => void;
  
  // State management
  readonly?: boolean;
  loading?: boolean;
  saving?: boolean;
  validationErrors?: ValidationError[];
  
  // UI customization
  showToolbar?: boolean;
  showImportExport?: boolean;
  compactMode?: boolean;
  className?: string;
}

// Triple Editor Sub-component
export interface TripleEditorProps {
  triple: OntologyTriple;
  index: number;
  onChange: (index: number, triple: OntologyTriple) => void;
  onDelete: (index: number) => void;
  readonly?: boolean;
  validationErrors?: ValidationError[];
  showDeleteButton?: boolean;
}

// Entity/Relationship Editor Sub-components
export interface EntityEditorProps {
  entity: EntityDefinition;
  onChange: (entity: EntityDefinition) => void;
  label: string;
  readonly?: boolean;
  validationError?: string;
}

export interface RelationshipEditorProps {
  relationship: RelationshipDefinition;
  onChange: (relationship: RelationshipDefinition) => void;
  readonly?: boolean;
  validationError?: string;
}

// Graph Visualization Component
export interface GraphVisualizationComponentProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  
  // Layout options
  layout?: 'hierarchical' | 'force' | 'circular' | 'random';
  physics?: boolean;
  
  // Interaction options
  interactive?: boolean;
  selectable?: boolean;
  multiSelect?: boolean;
  showLabels?: boolean;
  showTooltips?: boolean;
  
  // Event handlers
  onNodeClick?: (nodeId: string, node: GraphNode) => void;
  onEdgeClick?: (edgeId: string, edge: GraphEdge) => void;
  onNodeDoubleClick?: (nodeId: string, node: GraphNode) => void;
  onSelectionChange?: (selection: { nodes: string[]; edges: string[] }) => void;
  onStabilized?: () => void;
  
  // Visual customization
  height: number | string;
  width: number | string;
  backgroundColor?: string;
  nodeColors?: Record<string, string>;
  edgeColors?: Record<string, string>;
  
  // Performance options
  maxNodes?: number;
  enableClustering?: boolean;
  clusterThreshold?: number;
  
  className?: string;
}

// Graph Controls Sub-component
export interface GraphControlsProps {
  onFitToScreen: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetLayout: () => void;
  onTogglePhysics: () => void;
  onExportImage: () => void;
  
  physicsEnabled: boolean;
  zoomLevel: number;
  className?: string;
}

// Document Management Component
export interface DocumentListComponentProps {
  documents: Document[];
  loading?: boolean;
  onDocumentSelect: (document: Document) => void;
  onDocumentDelete: (documentId: string) => void;
  onDocumentRefresh: () => void;
  
  // Filtering and sorting
  statusFilter?: Document['status'];
  onStatusFilterChange?: (status: Document['status'] | 'all') => void;
  sortBy?: 'created_at' | 'filename' | 'file_size';
  sortOrder?: 'asc' | 'desc';
  onSortChange?: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  
  // Pagination
  page?: number;
  limit?: number;
  total?: number;
  onPageChange?: (page: number) => void;
  
  className?: string;
}

// Document Status Component
export interface DocumentStatusComponentProps {
  document: Document;
  showProgressBar?: boolean;
  showErrorDetails?: boolean;
  onRetry?: () => void;
  onViewDetails?: () => void;
  compact?: boolean;
  className?: string;
}

// Extraction Management Component
export interface ExtractionListComponentProps {
  extractions: Extraction[];
  loading?: boolean;
  onExtractionSelect: (extraction: Extraction) => void;
  onExtractionDelete: (extractionId: string) => void;
  onStartExtraction: () => void;
  onExportNeo4j: (extractionId: string) => void;
  onExportNeptune: (extractionId: string) => void;
  
  statusFilter?: Extraction['status'];
  onStatusFilterChange?: (status: Extraction['status'] | 'all') => void;
  className?: string;
}

// Progress Indicator Component
export interface ProgressIndicatorProps {
  progress: number;        // 0-100
  status: 'idle' | 'processing' | 'completed' | 'error';
  message?: string;
  showPercentage?: boolean;
  animated?: boolean;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  size?: 'small' | 'medium' | 'large';
  variant?: 'linear' | 'circular';
  className?: string;
}

// Navigation Component
export interface NavigationComponentProps {
  currentPath: string;
  user?: User;
  onLogout: () => void;
  onNavigate: (path: string) => void;
  
  // Mobile responsiveness
  mobileOpen?: boolean;
  onMobileToggle?: () => void;
  
  className?: string;
}

// Error Boundary Component
export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  resetOnPropsChange?: boolean;
}

// Notification System Component
export interface NotificationProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  autoHide?: boolean;
  autoHideDelay?: number;
  actions?: Array<{
    label: string;
    onClick: () => void;
    color?: 'primary' | 'secondary';
  }>;
  onClose: (id: string) => void;
}

export interface NotificationSystemProps {
  notifications: NotificationProps[];
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'top-center' | 'bottom-center';
  maxNotifications?: number;
  className?: string;
}

// Loading Spinner Component
export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: 'primary' | 'secondary' | 'inherit';
  message?: string;
  overlay?: boolean;
  className?: string;
}

// Confirmation Dialog Component
export interface ConfirmationDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmColor?: 'primary' | 'secondary' | 'error' | 'warning';
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

// Data Export Component
export interface DataExportComponentProps {
  extractionId: string;
  onExportNeo4j: () => Promise<{ nodes_csv_url: string; relationships_csv_url: string }>;
  onExportNeptune: () => Promise<{ vertices_csv_url: string; edges_csv_url: string }>;
  loading?: boolean;
  className?: string;
}

// ============================================================================
// Page Component Interfaces
// ============================================================================

// Dashboard Page
export interface DashboardPageProps {
  user: User;
  recentDocuments: Document[];
  recentExtractions: Extraction[];
  stats: {
    totalDocuments: number;
    totalOntologies: number;
    totalExtractions: number;
    processingJobs: number;
  };
}

// Documents Page
export interface DocumentsPageProps {
  documents: Document[];
  loading: boolean;
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
}

// Ontologies Page
export interface OntologiesPageProps {
  ontologies: Ontology[];
  documents: Document[];
  loading: boolean;
}

// Extractions Page
export interface ExtractionsPageProps {
  extractions: Extraction[];
  loading: boolean;
}

// Graph Viewer Page
export interface GraphViewerPageProps {
  extraction: Extraction;
  nodes: GraphNode[];
  edges: GraphEdge[];
  loading: boolean;
}

// ============================================================================
// Responsive Design Specifications
// ============================================================================

export interface ResponsiveProps {
  xs?: boolean | number;
  sm?: boolean | number;
  md?: boolean | number;
  lg?: boolean | number;
  xl?: boolean | number;
}

export interface MobileAdaptiveProps {
  // Mobile-specific overrides
  mobileLayout?: 'stack' | 'collapse' | 'hide';
  mobileBreakpoint?: number;
  touchOptimized?: boolean;
}

// ============================================================================
// Accessibility Specifications
// ============================================================================

export interface AccessibilityProps {
  // WCAG 2.1 AA compliance
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-hidden'?: boolean;
  'aria-live'?: 'polite' | 'assertive' | 'off';
  role?: string;
  tabIndex?: number;
}

// ============================================================================
// Component State Management
// ============================================================================

export interface ComponentState {
  loading: boolean;
  error: string | null;
  data: any;
}

export interface AsyncComponentProps {
  loading?: boolean;
  error?: string | null;
  retry?: () => void;
}

// ============================================================================
// Event Handler Types
// ============================================================================

export type ChangeHandler<T> = (value: T) => void;
export type AsyncChangeHandler<T> = (value: T) => Promise<void>;
export type EventHandler = () => void;
export type AsyncEventHandler = () => Promise<void>;
export type ErrorHandler = (error: Error) => void;
export type FileHandler = (file: File) => void;
export type FilesHandler = (files: File[]) => void;

// ============================================================================
// Form Validation
// ============================================================================

export interface FormFieldProps {
  value: any;
  onChange: ChangeHandler<any>;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
  helperText?: string;
}

export interface FormValidation {
  isValid: boolean;
  errors: Record<string, string>;
}

// ============================================================================
// Animation & Transition Specifications
// ============================================================================

export interface AnimationProps {
  duration?: number;
  easing?: 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out';
  delay?: number;
}

export interface TransitionProps extends AnimationProps {
  in?: boolean;
  onEnter?: () => void;
  onExit?: () => void;
}

// Default theme configuration for Figma
export const defaultTheme: ThemeConfiguration = {
  colors: {
    primary: '#1976d2',
    primaryLight: '#42a5f5',
    primaryDark: '#1565c0',
    secondary: '#dc004e',
    secondaryLight: '#ff5983',
    secondaryDark: '#9a0036',
    error: '#d32f2f',
    warning: '#ed6c02',
    info: '#0288d1',
    success: '#2e7d32',
    background: {
      default: '#fafafa',
      paper: '#ffffff',
      elevated: '#ffffff',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
      disabled: 'rgba(0, 0, 0, 0.38)',
    },
    divider: 'rgba(0, 0, 0, 0.12)',
    grey: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#eeeeee',
      300: '#e0e0e0',
      400: '#bdbdbd',
      500: '#9e9e9e',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },
  },
  typography: {
    h1: { fontFamily: 'Roboto', fontSize: '2.125rem', fontWeight: 300, lineHeight: 1.235 },
    h2: { fontFamily: 'Roboto', fontSize: '1.5rem', fontWeight: 400, lineHeight: 1.334 },
    h3: { fontFamily: 'Roboto', fontSize: '1.25rem', fontWeight: 400, lineHeight: 1.6 },
    h4: { fontFamily: 'Roboto', fontSize: '1.125rem', fontWeight: 500, lineHeight: 1.5 },
    h5: { fontFamily: 'Roboto', fontSize: '1rem', fontWeight: 500, lineHeight: 1.5 },
    h6: { fontFamily: 'Roboto', fontSize: '0.875rem', fontWeight: 500, lineHeight: 1.57 },
    body1: { fontFamily: 'Roboto', fontSize: '1rem', fontWeight: 400, lineHeight: 1.5 },
    body2: { fontFamily: 'Roboto', fontSize: '0.875rem', fontWeight: 400, lineHeight: 1.43 },
    button: { fontFamily: 'Roboto', fontSize: '0.875rem', fontWeight: 500, lineHeight: 1.75 },
    caption: { fontFamily: 'Roboto', fontSize: '0.75rem', fontWeight: 400, lineHeight: 1.66 },
    overline: { fontFamily: 'Roboto', fontSize: '0.75rem', fontWeight: 400, lineHeight: 2.66 },
  },
  spacing: {
    unit: 8,
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  breakpoints: {
    xs: 0,
    sm: 600,
    md: 900,
    lg: 1200,
    xl: 1536,
  },
  shadows: [
    'none',
    '0px 2px 1px -1px rgba(0,0,0,0.2),0px 1px 1px 0px rgba(0,0,0,0.14),0px 1px 3px 0px rgba(0,0,0,0.12)',
    '0px 3px 1px -2px rgba(0,0,0,0.2),0px 2px 2px 0px rgba(0,0,0,0.14),0px 1px 5px 0px rgba(0,0,0,0.12)',
    // ... more shadow levels
  ],
  zIndex: {
    drawer: 1200,
    modal: 1300,
    snackbar: 1400,
    tooltip: 1500,
  },
};