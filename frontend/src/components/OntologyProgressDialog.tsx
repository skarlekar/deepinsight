import React, { useState, useEffect, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Paper,
  Grid,
  IconButton,
} from '@mui/material';
import {
  CheckCircle,
  RadioButtonUnchecked,
  HourglassEmpty,
  Error,
  Close,
  DataUsage,
  Schema,
} from '@mui/icons-material';
import apiService from '../services/api';

interface ChunkProgress {
  status: 'pending' | 'processing' | 'completed' | 'error';
}

interface OntologyProgress {
  ontology_id: string;
  status: string;
  total_chunks: number;
  processed_chunks: number;
  current_chunk: number;
  chunk_progress: ChunkProgress[];
  overall_progress: number;
  triples_count?: number;
  entities_count?: number;
  error_message?: string;
  processing_mode?: 'standard' | 'chunked';
  document_length?: number;
  created_at: string;
  updated_at?: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  ontologyId: string | null;
}

export const OntologyProgressDialog: React.FC<Props> = ({ open, onClose, ontologyId }) => {
  const [progress, setProgress] = useState<OntologyProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchProgress = async () => {
    if (!ontologyId) return;

    console.log('Fetching progress for ontology:', ontologyId);
    try {
      setLoading(true);
      const response = await apiService.getOntologyProgress(ontologyId);
      console.log('Raw API response:', response);
      
      const metadata = response.metadata || {};
      const progressData = {
        ontology_id: response.id,
        status: response.status,
        total_chunks: metadata.total_chunks || 1,
        processed_chunks: metadata.processed_chunks || 0,
        current_chunk: metadata.current_chunk || 0,
        chunk_progress: metadata.chunk_progress || [],
        overall_progress: response.progress_percentage || 0,
        triples_count: metadata.triples_count,
        entities_count: metadata.entities_count,
        error_message: metadata.error_message,
        processing_mode: metadata.processing_mode,
        document_length: metadata.document_length,
        created_at: response.created_at,
        updated_at: response.updated_at,
      };

      console.log('Progress data received:', progressData);
      setProgress(progressData);
    } catch (error) {
      console.error('Failed to fetch ontology progress:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh progress for active ontologies
  useEffect(() => {
    if (open && ontologyId) {
      fetchProgress();
      
      // Set up polling if the ontology is still processing
      intervalRef.current = setInterval(fetchProgress, 2000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, ontologyId]);

  // Stop polling when ontology is completed or failed
  useEffect(() => {
    if (progress && (progress.status === 'active' || progress.status === 'draft' || progress.status === 'error')) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }
  }, [progress]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'processing':
        return <HourglassEmpty color="primary" />;
      case 'error':
        return <Error color="error" />;
      default:
        return <RadioButtonUnchecked color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'processing':
        return 'primary';
      case 'draft':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatProcessingMode = (mode?: string) => {
    return mode === 'chunked' ? 'Chunked Processing' : 'Standard Processing';
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Schema color="primary" />
            <Typography variant="h6">Ontology Generation Progress</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading && !progress ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <LinearProgress />
            <Typography variant="body2" sx={{ mt: 2 }}>
              Loading progress...
            </Typography>
          </Box>
        ) : progress ? (
          <Box>
            {/* Overall Status */}
            <Paper sx={{ p: 2, mb: 3 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Typography variant="h6">Status:</Typography>
                    <Chip 
                      label={progress.status.toUpperCase()} 
                      color={getStatusColor(progress.status) as any}
                      variant="filled"
                    />
                  </Box>
                  
                  {progress.processing_mode && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Mode: {formatProcessingMode(progress.processing_mode)}
                      </Typography>
                    </Box>
                  )}

                  {progress.document_length && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Document Length: {progress.document_length.toLocaleString()} characters
                      </Typography>
                    </Box>
                  )}
                </Grid>

                <Grid item xs={12} sm={6}>
                  {progress.status === 'processing' && (
                    <Box sx={{ textAlign: 'center' }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={progress.overall_progress} 
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="body2">
                        {progress.overall_progress}% Complete
                      </Typography>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </Paper>

            {/* Processing Progress */}
            {progress.total_chunks > 1 && (
              <Paper sx={{ p: 2, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Processing Progress
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Processed {progress.processed_chunks} of {progress.total_chunks} chunks
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(progress.processed_chunks / progress.total_chunks) * 100} 
                    sx={{ mt: 1 }}
                  />
                </Box>

                {/* Chunk Progress List */}
                {progress.chunk_progress && progress.chunk_progress.length > 0 && (
                  <List dense>
                    {progress.chunk_progress.map((chunk, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          {getStatusIcon(chunk.status)}
                        </ListItemIcon>
                        <ListItemText
                          primary={`Chunk ${index + 1}`}
                          secondary={`Status: ${chunk.status}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </Paper>
            )}

            {/* Results Summary */}
            {(progress.status === 'active' || progress.triples_count || progress.entities_count) && (
              <Paper sx={{ p: 2, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Results Summary
                </Typography>
                <Grid container spacing={2}>
                  {progress.entities_count !== undefined && (
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center' }}>
                        <DataUsage color="primary" sx={{ fontSize: 40, mb: 1 }} />
                        <Typography variant="h4" color="primary">
                          {progress.entities_count}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Entity Types
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  {progress.triples_count !== undefined && (
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Schema color="secondary" sx={{ fontSize: 40, mb: 1 }} />
                        <Typography variant="h4" color="secondary">
                          {progress.triples_count}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Ontology Triples
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                </Grid>
              </Paper>
            )}

            {/* Error Message */}
            {progress.error_message && (
              <Paper sx={{ p: 2, mb: 3, bgcolor: 'error.light' }}>
                <Typography variant="h6" color="error" gutterBottom>
                  Error
                </Typography>
                <Typography variant="body2" color="error">
                  {progress.error_message}
                </Typography>
              </Paper>
            )}

            {/* Timestamps */}
            <Paper sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">
                <strong>Created:</strong> {new Date(progress.created_at).toLocaleString()}
              </Typography>
              {progress.updated_at && (
                <Typography variant="body2" color="text.secondary">
                  <strong>Last Updated:</strong> {new Date(progress.updated_at).toLocaleString()}
                </Typography>
              )}
            </Paper>
          </Box>
        ) : (
          <Typography color="error">Failed to load progress information.</Typography>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};