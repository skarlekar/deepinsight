import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  AuthResponse, LoginRequest, RegisterRequest, User,
  Document, DocumentListResponse,
  Ontology, OntologyDetail,
  Extraction, ExtractionDetail, ExtractionResult,
  ExportResponse
} from '../types';

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
        console.log('API Request with token to:', config.url);
      } else {
        console.log('API Request without token to:', config.url);
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearToken();
          // Don't redirect here - let the AuthContext handle this
        }
        throw error;
      }
    );

    // Load token from localStorage on initialization
    this.loadToken();
  }

  private loadToken() {
    const token = localStorage.getItem('access_token');
    if (token) {
      this.setToken(token);
    }
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
    console.log('Token set:', token ? 'Token stored' : 'No token');
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  // Authentication endpoints
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/auth/register', data);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/auth/login', data);
    this.setToken(response.data.access_token);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout');
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>('/auth/me');
    return response.data;
  }

  // Document endpoints
  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.api.post<Document>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getDocuments(page: number = 1, limit: number = 10): Promise<DocumentListResponse> {
    const response = await this.api.get<DocumentListResponse>('/documents', {
      params: { page, limit },
    });
    return response.data;
  }

  async getDocument(id: string): Promise<Document> {
    const response = await this.api.get<Document>(`/documents/${id}`);
    return response.data;
  }

  async deleteDocument(id: string): Promise<void> {
    await this.api.delete(`/documents/${id}`);
  }

  async getDocumentStatus(id: string): Promise<any> {
    const response = await this.api.get(`/documents/${id}/status`);
    return response.data;
  }

  getDocumentDownloadUrl(id: string): string {
    return `${this.api.defaults.baseURL}/documents/${id}/download`;
  }

  // Ontology endpoints
  async createOntology(data: { document_id: string; name: string; description?: string }): Promise<Ontology> {
    const response = await this.api.post<Ontology>('/ontologies', data);
    return response.data;
  }

  async getOntologies(documentId?: string): Promise<Ontology[]> {
    const response = await this.api.get<Ontology[]>('/ontologies', {
      params: documentId ? { document_id: documentId } : {},
    });
    return response.data;
  }

  async getOntology(id: string): Promise<OntologyDetail> {
    const response = await this.api.get<OntologyDetail>(`/ontologies/${id}`);
    return response.data;
  }

  async updateOntology(id: string, data: { name: string; description?: string; triples: any[] }): Promise<Ontology> {
    const response = await this.api.put<Ontology>(`/ontologies/${id}`, data);
    return response.data;
  }

  async deleteOntology(id: string): Promise<void> {
    await this.api.delete(`/ontologies/${id}`);
  }

  async reprocessOntology(id: string): Promise<any> {
    const response = await this.api.post(`/ontologies/${id}/reprocess`);
    return response.data;
  }

  // Extraction endpoints
  async createExtraction(data: {
    document_id: string;
    ontology_id: string;
    chunk_size?: number;
    overlap_percentage?: number;
  }): Promise<Extraction> {
    const response = await this.api.post<Extraction>('/extractions', data);
    return response.data;
  }

  async getExtractions(): Promise<Extraction[]> {
    const response = await this.api.get<Extraction[]>('/extractions');
    return response.data;
  }

  async getExtraction(id: string): Promise<ExtractionDetail> {
    const response = await this.api.get<ExtractionDetail>(`/extractions/${id}`);
    return response.data;
  }

  async getExtractionResult(id: string): Promise<ExtractionResult> {
    const response = await this.api.get<ExtractionResult>(`/extractions/${id}/result`);
    return response.data;
  }

  async deleteExtraction(id: string): Promise<void> {
    await this.api.delete(`/extractions/${id}`);
  }

  async getExtractionStatus(id: string): Promise<any> {
    const response = await this.api.get(`/extractions/${id}/status`);
    return response.data;
  }

  async getExtractionProgress(id: string): Promise<any> {
    const response = await this.api.get(`/extractions/${id}/progress`);
    return response.data;
  }

  async downloadExtractionResults(id: string): Promise<Blob> {
    const response = await this.api.get(`/extractions/${id}/result`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async restartExtraction(id: string): Promise<any> {
    const response = await this.api.post(`/extractions/${id}/restart`);
    return response.data;
  }

  // Export endpoints
  async exportToNeo4j(extractionId: string): Promise<ExportResponse> {
    const response = await this.api.post<ExportResponse>(`/exports/${extractionId}/neo4j`);
    return response.data;
  }

  async exportToNeptune(extractionId: string): Promise<ExportResponse> {
    const response = await this.api.post<ExportResponse>(`/exports/${extractionId}/neptune`);
    return response.data;
  }

  getDownloadUrl(filename: string): string {
    return `${this.api.defaults.baseURL}/exports/download/${filename}`;
  }

  async downloadFile(filename: string): Promise<void> {
    const response = await this.api.get(`/exports/download/${filename}`, {
      responseType: 'blob',
    });
    
    // Create blob URL and trigger download
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.api.get('/health');
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;