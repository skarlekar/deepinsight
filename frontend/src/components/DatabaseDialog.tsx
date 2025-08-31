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
  Box,
  Typography,
  Alert,
  CircularProgress,
  Card,
  CardContent,
} from '@mui/material';
import { Download, Storage } from '@mui/icons-material';
import apiService from '../services/api';
import { Extraction } from '../types';

interface DatabaseDialogProps {
  open: boolean;
  onClose: () => void;
  onExportComplete: () => void;
}

export const DatabaseDialog: React.FC<DatabaseDialogProps> = ({
  open,
  onClose,
  onExportComplete,
}) => {
  const [loading, setLoading] = useState(false);
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [selectedExtraction, setSelectedExtraction] = useState('');
  const [exportType, setExportType] = useState<'neo4j' | 'neptune'>('neo4j');
  const [error, setError] = useState('');
  const [exportResult, setExportResult] = useState<any>(null);

  useEffect(() => {
    if (open) {
      loadExtractions();
    }
  }, [open]);

  const loadExtractions = async () => {
    try {
      const extractionsResponse = await apiService.getExtractions();
      setExtractions(extractionsResponse.filter(ext => ext.status === 'completed'));
    } catch (error) {
      console.error('Failed to load extractions:', error);
    }
  };

  const handleExport = async () => {
    if (!selectedExtraction) return;

    setLoading(true);
    setError('');
    setExportResult(null);

    try {
      let result;
      if (exportType === 'neo4j') {
        result = await apiService.exportToNeo4j(selectedExtraction);
      } else {
        result = await apiService.exportToNeptune(selectedExtraction);
      }

      setExportResult(result);
      onExportComplete();
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Export failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (filename: string) => {
    try {
      await apiService.downloadFile(filename);
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback to the old method if the new one fails
      const url = apiService.getDownloadUrl(filename);
      window.open(url, '_blank');
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
      setSelectedExtraction('');
      setExportType('neo4j');
      setError('');
      setExportResult(null);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Storage sx={{ mr: 1 }} />
          Configure Database Export
        </Box>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Export your extracted graph data to Neo4j or AWS Neptune database formats.
        </Typography>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Select Completed Extraction</InputLabel>
          <Select
            value={selectedExtraction}
            label="Select Completed Extraction"
            onChange={(e) => setSelectedExtraction(e.target.value)}
            required
          >
            {extractions.map((ext) => (
              <MenuItem key={ext.id} value={ext.id}>
                Extraction {ext.id.slice(0, 8)} - {new Date(ext.created_at).toLocaleDateString()}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Export Format</InputLabel>
          <Select
            value={exportType}
            label="Export Format"
            onChange={(e) => setExportType(e.target.value as 'neo4j' | 'neptune')}
            required
          >
            <MenuItem value="neo4j">
              <Box>
                <Typography variant="body1">Neo4j CSV Format</Typography>
                <Typography variant="body2" color="text.secondary">
                  Nodes and relationships CSV files for Neo4j import
                </Typography>
              </Box>
            </MenuItem>
            <MenuItem value="neptune">
              <Box>
                <Typography variant="body1">AWS Neptune Format</Typography>
                <Typography variant="body2" color="text.secondary">
                  Vertices and edges CSV files for Neptune bulk loader
                </Typography>
              </Box>
            </MenuItem>
          </Select>
        </FormControl>

        {extractions.length === 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            No completed extractions available. Please complete an extraction first.
          </Alert>
        )}

        {exportResult && (
          <Card sx={{ mt: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Export Complete!
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Your graph data has been exported to {exportType.toUpperCase()} format.
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {exportType === 'neo4j' ? (
                  <>
                    {exportResult.nodes_csv_url && (
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<Download />}
                        onClick={() => handleDownload(exportResult.nodes_csv_url.split('/').pop())}
                      >
                        Download Nodes CSV
                      </Button>
                    )}
                    {exportResult.relationships_csv_url && (
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<Download />}
                        onClick={() => handleDownload(exportResult.relationships_csv_url.split('/').pop())}
                      >
                        Download Relationships CSV
                      </Button>
                    )}
                  </>
                ) : (
                  <>
                    {exportResult.vertices_csv_url && (
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<Download />}
                        onClick={() => handleDownload(exportResult.vertices_csv_url.split('/').pop())}
                      >
                        Download Vertices CSV
                      </Button>
                    )}
                    {exportResult.edges_csv_url && (
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<Download />}
                        onClick={() => handleDownload(exportResult.edges_csv_url.split('/').pop())}
                      >
                        Download Edges CSV
                      </Button>
                    )}
                  </>
                )}
              </Box>
              <Typography variant="caption" display="block" sx={{ mt: 1, opacity: 0.8 }}>
                Downloads expire: {new Date(exportResult.download_expires_at).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        )}

        {loading && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
            <CircularProgress size={20} sx={{ mr: 2 }} />
            <Typography variant="body2" color="text.secondary">
              Exporting data to {exportType.toUpperCase()} format...
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          {exportResult ? 'Close' : 'Cancel'}
        </Button>
        {!exportResult && (
          <Button
            onClick={handleExport}
            variant="contained"
            disabled={!selectedExtraction || loading || extractions.length === 0}
          >
            {loading ? 'Exporting...' : `Export to ${exportType.toUpperCase()}`}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};