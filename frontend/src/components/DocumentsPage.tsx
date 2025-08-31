import React, { useState, useEffect, useCallback } from 'react';
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
  TablePagination,
} from '@mui/material';
import {
  Upload,
  Delete,
  Visibility,
  GetApp,
  Refresh,
} from '@mui/icons-material';
import { UploadDialog } from './UploadDialog';
import apiService from '../services/api';
import { Document, DocumentStatus } from '../types';
import { formatDateToLocal } from '../utils/dateUtils';

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalCount, setTotalCount] = useState(0);

  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getDocuments(page + 1, rowsPerPage);
      setDocuments(response.documents);
      setTotalCount(response.total);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleDeleteClick = (document: Document) => {
    setDocumentToDelete(document);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!documentToDelete) return;

    try {
      await apiService.deleteDocument(documentToDelete.id);
      setDeleteDialogOpen(false);
      setDocumentToDelete(null);
      loadDocuments();
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const getStatusColor = (status: DocumentStatus) => {
    switch (status) {
      case DocumentStatus.COMPLETED:
        return 'success';
      case DocumentStatus.PROCESSING:
        return 'warning';
      case DocumentStatus.ERROR:
        return 'error';
      default:
        return 'default';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Using formatDateToLocalToLocal from utils instead of local function

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleViewDetails = (document: Document) => {
    setSelectedDocument(document);
    setDetailsDialogOpen(true);
  };

  const handleDownload = async (document: Document) => {
    try {
      await apiService.downloadDocument(document.id, document.original_filename);
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback to window.open if authenticated download fails
      const url = apiService.getDocumentDownloadUrl(document.id);
      window.open(url, '_blank');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Documents
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadDocuments}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Upload />}
            onClick={() => setUploadDialogOpen(true)}
          >
            Upload Document
          </Button>
        </Box>
      </Box>

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Filename</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell>Processed</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    Loading documents...
                  </TableCell>
                </TableRow>
              ) : documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Box sx={{ py: 4, textAlign: 'center' }}>
                      <Typography variant="h6" gutterBottom>
                        No documents yet
                      </Typography>
                      <Typography color="text.secondary" gutterBottom>
                        Upload your first document to get started
                      </Typography>
                      <Button
                        variant="contained"
                        startIcon={<Upload />}
                        onClick={() => setUploadDialogOpen(true)}
                        sx={{ mt: 2 }}
                      >
                        Upload Document
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((document) => (
                  <TableRow key={document.id}>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {document.original_filename}
                        </Typography>
                        {document.error_message && (
                          <Typography variant="caption" color="error">
                            {document.error_message}
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>{formatFileSize(document.file_size)}</TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {document.mime_type.split('/').pop()?.toUpperCase()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={document.status}
                        color={getStatusColor(document.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{formatDateToLocal(document.created_at)}</TableCell>
                    <TableCell>
                      {document.processed_at ? formatDateToLocal(document.processed_at) : '-'}
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="View Details">
                          <IconButton 
                            size="small"
                            onClick={() => handleViewDetails(document)}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download">
                          <IconButton 
                            size="small"
                            onClick={() => handleDownload(document)}
                          >
                            <GetApp />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleDeleteClick(document)}
                          >
                            <Delete />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        {totalCount > 0 && (
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={totalCount}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        )}
      </Paper>

      {/* Upload Dialog */}
      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUploadComplete={loadDocuments}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Document</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{documentToDelete?.original_filename}"? 
            This action cannot be undone.
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

      {/* Document Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={() => setDetailsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Document Details</DialogTitle>
        <DialogContent>
          {selectedDocument && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>Filename:</Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>{selectedDocument.original_filename}</Typography>
              
              <Typography variant="subtitle2" gutterBottom>Document ID:</Typography>
              <Typography variant="body2" sx={{ mb: 2, fontFamily: 'monospace' }}>{selectedDocument.id}</Typography>
              
              <Typography variant="subtitle2" gutterBottom>File Size:</Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>{formatFileSize(selectedDocument.file_size)}</Typography>
              
              <Typography variant="subtitle2" gutterBottom>MIME Type:</Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>{selectedDocument.mime_type}</Typography>
              
              <Typography variant="subtitle2" gutterBottom>Status:</Typography>
              <Chip
                label={selectedDocument.status}
                color={getStatusColor(selectedDocument.status) as any}
                size="small"
                sx={{ mb: 2 }}
              />
              
              <Typography variant="subtitle2" gutterBottom>Uploaded:</Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>{formatDateToLocal(selectedDocument.created_at)}</Typography>
              
              {selectedDocument.processed_at && (
                <>
                  <Typography variant="subtitle2" gutterBottom>Processed:</Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>{formatDateToLocal(selectedDocument.processed_at)}</Typography>
                </>
              )}
              
              {selectedDocument.error_message && (
                <>
                  <Typography variant="subtitle2" gutterBottom color="error">Error Message:</Typography>
                  <Typography variant="body2" color="error">{selectedDocument.error_message}</Typography>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => selectedDocument && handleDownload(selectedDocument)} startIcon={<GetApp />}>
            Download
          </Button>
          <Button onClick={() => setDetailsDialogOpen(false)} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};