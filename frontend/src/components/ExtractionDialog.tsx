import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Slider,
} from '@mui/material';
import apiService from '../services/api';
import { Document, Ontology } from '../types';

interface ExtractionDialogProps {
  open: boolean;
  onClose: () => void;
  onExtractionStarted: () => void;
}

export const ExtractionDialog: React.FC<ExtractionDialogProps> = ({
  open,
  onClose,
  onExtractionStarted,
}) => {
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [ontologies, setOntologies] = useState<Ontology[]>([]);
  const [formData, setFormData] = useState({
    document_id: '',
    ontology_id: '',
    additional_instructions: '',
    chunk_size: 1000,
    overlap_percentage: 10,
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open]);

  const loadData = async () => {
    try {
      const [docsResponse, ontologiesResponse] = await Promise.all([
        apiService.getDocuments(1, 100),
        apiService.getOntologies(),
      ]);
      
      setDocuments(docsResponse.documents.filter(doc => doc.status === 'completed'));
      setOntologies(ontologiesResponse.filter(ont => ont.status === 'active'));
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.document_id || !formData.ontology_id) return;

    setLoading(true);
    setError('');

    try {
      await apiService.createExtraction({
        document_id: formData.document_id,
        ontology_id: formData.ontology_id,
        additional_instructions: formData.additional_instructions || undefined,
        chunk_size: formData.chunk_size,
        overlap_percentage: formData.overlap_percentage,
      });

      onExtractionStarted();
      onClose();
      setFormData({
        document_id: '',
        ontology_id: '',
        additional_instructions: '',
        chunk_size: 1000,
        overlap_percentage: 10,
      });
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to start extraction');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
      setFormData({
        document_id: '',
        ontology_id: '',
        additional_instructions: '',
        chunk_size: 1000,
        overlap_percentage: 10,
      });
      setError('');
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Start Data Extraction</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Extract structured graph data from documents using AI-powered ontologies.
          </Typography>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Select Document</InputLabel>
            <Select
              value={formData.document_id}
              label="Select Document"
              onChange={(e) => setFormData({ ...formData, document_id: e.target.value })}
              required
            >
              {documents.map((doc) => (
                <MenuItem key={doc.id} value={doc.id}>
                  {doc.original_filename}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Select Ontology</InputLabel>
            <Select
              value={formData.ontology_id}
              label="Select Ontology"
              onChange={(e) => setFormData({ ...formData, ontology_id: e.target.value })}
              required
            >
              {ontologies.map((ont) => (
                <MenuItem key={ont.id} value={ont.id}>
                  {ont.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Additional Instructions (Optional)"
            value={formData.additional_instructions}
            onChange={(e) => setFormData({ ...formData, additional_instructions: e.target.value })}
            multiline
            rows={3}
            placeholder="Provide additional instructions for the LLM to guide data extraction..."
            sx={{ mb: 3 }}
          />

          {(documents.length === 0 || ontologies.length === 0) && (
            <Alert severity="info" sx={{ mb: 2 }}>
              {documents.length === 0 && 'No processed documents available. '}
              {ontologies.length === 0 && 'No active ontologies available. '}
              Please upload documents and create ontologies first.
            </Alert>
          )}

          <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
            Advanced Settings
          </Typography>

          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" gutterBottom>
              Chunk Size: {formData.chunk_size} characters
            </Typography>
            <Slider
              value={formData.chunk_size}
              onChange={(_, value) => setFormData({ ...formData, chunk_size: value as number })}
              min={500}
              max={2000}
              step={100}
              marks={[
                { value: 500, label: '500' },
                { value: 1000, label: '1000' },
                { value: 1500, label: '1500' },
                { value: 2000, label: '2000' },
              ]}
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" gutterBottom>
              Overlap: {formData.overlap_percentage}%
            </Typography>
            <Slider
              value={formData.overlap_percentage}
              onChange={(_, value) => setFormData({ ...formData, overlap_percentage: value as number })}
              min={0}
              max={50}
              step={5}
              marks={[
                { value: 0, label: '0%' },
                { value: 25, label: '25%' },
                { value: 50, label: '50%' },
              ]}
            />
          </Box>

          {loading && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
              <CircularProgress size={20} sx={{ mr: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Starting extraction process...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={
              !formData.document_id ||
              !formData.ontology_id ||
              loading ||
              documents.length === 0 ||
              ontologies.length === 0
            }
          >
            {loading ? 'Starting...' : 'Start Extraction'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};