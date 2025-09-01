import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import apiService from '../services/api';
import { Document } from '../types';

interface OntologyDialogProps {
  open: boolean;
  onClose: () => void;
  onOntologyCreated: () => void;
}

export const OntologyDialog: React.FC<OntologyDialogProps> = ({
  open,
  onClose,
  onOntologyCreated,
}) => {
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    document_id: '',
    additional_instructions: '',
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (open) {
      loadDocuments();
    }
  }, [open]);

  const loadDocuments = async () => {
    try {
      const response = await apiService.getDocuments(1, 100);
      setDocuments(response.documents.filter(doc => doc.status === 'completed'));
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.document_id) return;

    setLoading(true);
    setError('');

    try {
      await apiService.createOntology({
        document_id: formData.document_id,
        name: formData.name,
        description: formData.description || undefined,
        additional_instructions: formData.additional_instructions || undefined,
      });

      onOntologyCreated();
      onClose();
      setFormData({ name: '', description: '', document_id: '', additional_instructions: '' });
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Failed to create ontology');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
      setFormData({ name: '', description: '', document_id: '', additional_instructions: '' });
      setError('');
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create Ontology</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create an AI-powered ontology schema from your uploaded documents.
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

          {documents.length === 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>
              No processed documents available. Please upload and process a document first.
            </Alert>
          )}

          <TextField
            fullWidth
            label="Ontology Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            sx={{ mb: 2 }}
            placeholder="e.g., Medical Research Ontology"
          />

          <TextField
            fullWidth
            label="Description (Optional)"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            multiline
            rows={3}
            placeholder="Describe the purpose and scope of this ontology..."
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Additional Instructions (Optional)"
            value={formData.additional_instructions}
            onChange={(e) => setFormData({ ...formData, additional_instructions: e.target.value })}
            multiline
            rows={3}
            placeholder="Provide additional instructions for the LLM to guide ontology generation..."
          />

          {loading && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
              <CircularProgress size={20} sx={{ mr: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Creating ontology using AI analysis...
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
            disabled={!formData.name || !formData.document_id || loading || documents.length === 0}
          >
            {loading ? 'Creating...' : 'Create Ontology'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};