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
} from '@mui/icons-material';
import apiService from '../services/api';

interface ChunkProgress {
  status: 'pending' | 'processing' | 'completed' | 'error';
  nodes_count: number;
  relationships_count: number;
}

interface ExtractionProgress {
  extraction_id: string;
  status: string;
  total_chunks: number;
  processed_chunks: number;
  current_chunk: number;
  chunk_progress: ChunkProgress[];
  overall_progress: number;
  nodes_count: number;
  relationships_count: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

interface ExtractionProgressDialogProps {
  open: boolean;
  onClose: () => void;
  extractionId: string | null;
}

export const ExtractionProgressDialog: React.FC<ExtractionProgressDialogProps> = ({
  open,
  onClose,
  extractionId,
}) => {
  const [progress, setProgress] = useState<ExtractionProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (open && extractionId) {
      loadProgress();
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [open, extractionId]);

  const loadProgress = async () => {
    if (!extractionId) return;

    try {
      setLoading(true);
      const progressData = await apiService.getExtractionProgress(extractionId);
      setProgress(progressData);
    } catch (error) {
      console.error('Failed to load extraction progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const startPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = setInterval(() => {
      loadProgress();
    }, 2000); // Poll every 2 seconds for real-time updates
  };

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const getChunkIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'processing':
        return <HourglassEmpty color="warning" sx={{ animation: 'pulse 1.5s ease-in-out infinite' }} />;
      case 'error':
        return <Error color="error" />;
      default:
        return <RadioButtonUnchecked color="disabled" />;
    }
  };

  const getChunkStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString();
  };

  if (!progress) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>Extraction Progress</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <LinearProgress />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DataUsage />
          <Typography variant="h6">
            Extraction Progress
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <Close />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        {/* Overall Progress */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                Overall Progress
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={progress.overall_progress} 
                  sx={{ flex: 1, height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2" fontWeight="bold">
                  {progress.overall_progress}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                {progress.processed_chunks} of {progress.total_chunks} chunks processed
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                Status & Results
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                <Chip 
                  label={progress.status} 
                  color={progress.status === 'completed' ? 'success' : progress.status === 'error' ? 'error' : 'warning'}
                  size="small"
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                {progress.nodes_count} nodes • {progress.relationships_count} relationships
              </Typography>
              {progress.current_chunk > 0 && progress.status === 'processing' && (
                <Typography variant="body2" color="primary" sx={{ mt: 0.5 }}>
                  Currently processing chunk {progress.current_chunk}
                </Typography>
              )}
            </Grid>
          </Grid>
        </Paper>

        {/* Chunk-by-Chunk Progress */}
        <Typography variant="h6" gutterBottom>
          Chunk Progress ({progress.chunk_progress.length} chunks)
        </Typography>
        <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
          <List dense>
            {progress.chunk_progress.map((chunk, index) => (
              <ListItem key={index} divider>
                <ListItemIcon>
                  {getChunkIcon(chunk.status)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2">
                        Chunk {index + 1}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <Chip 
                          label={chunk.status} 
                          color={getChunkStatusColor(chunk.status) as any}
                          size="small"
                          variant="outlined"
                        />
                        {chunk.status === 'completed' && (
                          <Typography variant="caption" color="text.secondary">
                            {chunk.nodes_count}N • {chunk.relationships_count}R
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  }
                  secondary={
                    chunk.status === 'processing' ? 
                      'Extracting entities and relationships...' :
                    chunk.status === 'completed' ? 
                      `Extracted ${chunk.nodes_count} nodes and ${chunk.relationships_count} relationships` :
                    chunk.status === 'error' ? 
                      'Failed to process this chunk' :
                      'Waiting to be processed'
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>

        {/* Error Message */}
        {progress.error_message && (
          <Paper sx={{ p: 2, mt: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
            <Typography variant="subtitle2" gutterBottom>
              Error
            </Typography>
            <Typography variant="body2">
              {progress.error_message}
            </Typography>
          </Paper>
        )}

        {/* Timing Info */}
        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Started: {formatTime(progress.created_at)}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              {progress.completed_at && (
                <Typography variant="caption" color="text.secondary">
                  Completed: {formatTime(progress.completed_at)}
                </Typography>
              )}
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          {progress.status === 'completed' || progress.status === 'error' ? 'Close' : 'Close (Keep Running)'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};