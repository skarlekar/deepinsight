import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Tooltip,
  LinearProgress,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  PlayArrow,
  Delete,
  Visibility,
  GetApp,
  Refresh,
  DataUsage,
  Stop,
  Replay,
  Timeline,
} from '@mui/icons-material';
import { ExtractionDialog } from './ExtractionDialog';
import { ExtractionProgressDialog } from './ExtractionProgressDialog';
import { NetworkGraph } from './NetworkGraph';
import apiService from '../services/api';
import { Extraction, ExtractionStatus } from '../types';
import { formatDateToLocal } from '../utils/dateUtils';

export const ExtractionsPage: React.FC = () => {
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [extractionToDelete, setExtractionToDelete] = useState<Extraction | null>(null);
  const [progressDialogOpen, setProgressDialogOpen] = useState(false);
  const [selectedExtractionId, setSelectedExtractionId] = useState<string | null>(null);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const [extractionResults, setExtractionResults] = useState<any>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadExtractions();
  }, []);

  useEffect(() => {
    // Clear existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Set up polling only when there are active extractions
    const hasActiveExtractions = extractions.some(ext => 
      ext.status === ExtractionStatus.PROCESSING || ext.status === ExtractionStatus.PENDING
    );

    if (hasActiveExtractions) {
      intervalRef.current = setInterval(() => {
        loadExtractions();
      }, 10000); // Poll every 10 seconds (reduced frequency)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [extractions.map(e => e.id + e.status).join(',')]);

  const loadExtractions = async () => {
    try {
      setLoading(true);
      const response = await apiService.getExtractions();
      setExtractions(response);
    } catch (error) {
      console.error('Failed to load extractions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (extraction: Extraction) => {
    setExtractionToDelete(extraction);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!extractionToDelete) return;

    try {
      await apiService.deleteExtraction(extractionToDelete.id);
      setDeleteDialogOpen(false);
      setExtractionToDelete(null);
      loadExtractions();
    } catch (error) {
      console.error('Failed to delete extraction:', error);
    }
  };

  const handleViewResults = async (extractionId: string) => {
    try {
      const results = await apiService.getExtractionResult(extractionId);
      console.log('Extraction results:', results);
      setExtractionResults(results);
      setResultsDialogOpen(true);
    } catch (error) {
      console.error('Failed to load extraction results:', error);
    }
  };

  const handleDownloadResults = async (extractionId: string) => {
    try {
      const blob = await apiService.downloadExtractionResults(extractionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `extraction_${extractionId.slice(0, 8)}_results.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download extraction results:', error);
    }
  };

  const handleRestartExtraction = async (extractionId: string) => {
    try {
      await apiService.restartExtraction(extractionId);
      loadExtractions(); // Refresh to show updated status
    } catch (error) {
      console.error('Failed to restart extraction:', error);
    }
  };

  const handleViewProgress = (extractionId: string) => {
    setSelectedExtractionId(extractionId);
    setProgressDialogOpen(true);
  };

  const handleProgressDialogClose = () => {
    setProgressDialogOpen(false);
    setSelectedExtractionId(null);
    // Refresh extractions when dialog closes to get latest status
    loadExtractions();
  };

  const getStatusColor = (status: ExtractionStatus) => {
    switch (status) {
      case ExtractionStatus.COMPLETED:
        return 'success';
      case ExtractionStatus.PROCESSING:
        return 'warning';
      case ExtractionStatus.ERROR:
        return 'error';
      case ExtractionStatus.PENDING:
        return 'info';
      default:
        return 'default';
    }
  };

  // Using formatDateToLocalToLocal from utils instead of local function

  const getStatusIcon = (status: ExtractionStatus) => {
    switch (status) {
      case ExtractionStatus.PROCESSING:
        return <DataUsage sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />;
      case ExtractionStatus.COMPLETED:
        return <DataUsage color="success" />;
      case ExtractionStatus.ERROR:
        return <DataUsage color="error" />;
      default:
        return <DataUsage />;
    }
  };

  if (loading && extractions.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Extractions
        </Typography>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2 }}>
          Loading extractions...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Data Extractions
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadExtractions}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Start Extraction
          </Button>
        </Box>
      </Box>

      {/* Status Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Extractions
              </Typography>
              <Typography variant="h4">
                {extractions.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Completed
              </Typography>
              <Typography variant="h4" color="success.main">
                {extractions.filter(e => e.status === ExtractionStatus.COMPLETED).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Processing
              </Typography>
              <Typography variant="h4" color="warning.main">
                {extractions.filter(e => e.status === ExtractionStatus.PROCESSING || e.status === ExtractionStatus.PENDING).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Failed
              </Typography>
              <Typography variant="h4" color="error.main">
                {extractions.filter(e => e.status === ExtractionStatus.ERROR).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {extractions.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <DataUsage sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            No extractions yet
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            Start your first data extraction to convert documents into structured graph data
          </Typography>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={() => setCreateDialogOpen(true)}
            size="large"
          >
            Start Your First Extraction
          </Button>
        </Paper>
      ) : (
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Document</TableCell>
                  <TableCell>Ontology</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Completed</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {extractions.map((extraction) => (
                  <TableRow key={extraction.id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getStatusIcon(extraction.status)}
                        <Typography variant="body2" fontFamily="monospace">
                          {extraction.id.slice(0, 8)}...
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={extraction.status}
                        color={getStatusColor(extraction.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        Doc ID: {extraction.document_id.slice(0, 8)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        Ont ID: {extraction.ontology_id.slice(0, 8)}...
                      </Typography>
                    </TableCell>
                    <TableCell>{formatDateToLocal(extraction.created_at)}</TableCell>
                    <TableCell>
                      {extraction.completed_at ? formatDateToLocal(extraction.completed_at) : '-'}
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {(extraction.status === ExtractionStatus.PROCESSING || extraction.status === ExtractionStatus.PENDING) && (
                          <Tooltip title="View Progress">
                            <IconButton 
                              size="small"
                              color="primary"
                              onClick={() => handleViewProgress(extraction.id)}
                            >
                              <Timeline />
                            </IconButton>
                          </Tooltip>
                        )}
                        {extraction.status === ExtractionStatus.COMPLETED && (
                          <Tooltip title="View Results">
                            <IconButton 
                              size="small"
                              onClick={() => handleViewResults(extraction.id)}
                            >
                              <Visibility />
                            </IconButton>
                          </Tooltip>
                        )}
                        {extraction.status === ExtractionStatus.COMPLETED && (
                          <Tooltip title="Download Results">
                            <IconButton 
                              size="small"
                              onClick={() => handleDownloadResults(extraction.id)}
                            >
                              <GetApp />
                            </IconButton>
                          </Tooltip>
                        )}
                        {extraction.status === ExtractionStatus.PROCESSING && (
                          <Tooltip title="Stop Extraction">
                            <IconButton size="small" color="warning">
                              <Stop />
                            </IconButton>
                          </Tooltip>
                        )}
                        {(extraction.status === ExtractionStatus.PROCESSING || extraction.status === ExtractionStatus.PENDING) && (
                          <Tooltip title="Restart Extraction">
                            <IconButton 
                              size="small" 
                              color="secondary"
                              onClick={() => handleRestartExtraction(extraction.id)}
                            >
                              <Replay />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="Delete">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleDeleteClick(extraction)}
                          >
                            <Delete />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Create Dialog */}
      <ExtractionDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onExtractionStarted={loadExtractions}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Extraction</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this extraction? 
            This action cannot be undone and will remove all extracted data.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Progress Dialog */}
      <ExtractionProgressDialog
        open={progressDialogOpen}
        onClose={handleProgressDialogClose}
        extractionId={selectedExtractionId}
      />

      {/* Results Dialog */}
      <Dialog
        open={resultsDialogOpen}
        onClose={() => setResultsDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Extraction Results</DialogTitle>
        <DialogContent>
          {extractionResults && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Summary
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary">Nodes</Typography>
                      <Typography variant="h4">{extractionResults.nodes?.length || 0}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary">Relationships</Typography>
                      <Typography variant="h4">{extractionResults.relationships?.length || 0}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Additional Instructions */}
              {extractionResults.metadata?.additional_instructions && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Additional Instructions Used
                  </Typography>
                  <Typography variant="body2" sx={{ backgroundColor: '#f5f5f5', padding: 2, borderRadius: 1 }}>
                    {extractionResults.metadata.additional_instructions}
                  </Typography>
                </Box>
              )}

              {/* Network Visualization */}
              {(extractionResults.nodes?.length > 0 || extractionResults.relationships?.length > 0) && (
                <NetworkGraph 
                  nodes={extractionResults.nodes || []}
                  relationships={extractionResults.relationships || []}
                  height={400}
                />
              )}

              {extractionResults.nodes?.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                    Sample Nodes
                  </Typography>
                  <pre style={{ backgroundColor: '#f5f5f5', padding: 16, borderRadius: 4, overflow: 'auto' }}>
                    {JSON.stringify(extractionResults.nodes.slice(0, 3), null, 2)}
                  </pre>
                </>
              )}

              {extractionResults.relationships?.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                    Sample Relationships
                  </Typography>
                  <pre style={{ backgroundColor: '#f5f5f5', padding: 16, borderRadius: 4, overflow: 'auto' }}>
                    {JSON.stringify(extractionResults.relationships.slice(0, 3), null, 2)}
                  </pre>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResultsDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};