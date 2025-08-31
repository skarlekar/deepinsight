import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  Alert,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { Upload } from '@mui/icons-material';
import apiService from '../services/api';

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUploadComplete: () => void;
}

export const UploadDialog: React.FC<UploadDialogProps> = ({
  open,
  onClose,
  onUploadComplete,
}) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: false,
  });

  const handleUpload = async () => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setError('');
    setUploadProgress(0);

    try {
      const file = acceptedFiles[0];
      await apiService.uploadDocument(file);
      
      setUploadProgress(100);
      onUploadComplete();
      onClose();
    } catch (error: any) {
      setError(error.response?.data?.error?.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      onClose();
      setError('');
      setUploadProgress(0);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Upload Document</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            cursor: 'pointer',
            bgcolor: isDragActive ? 'action.hover' : 'background.paper',
            transition: 'all 0.2s ease',
            '&:hover': {
              borderColor: 'primary.main',
              bgcolor: 'action.hover',
            },
          }}
        >
          <input {...getInputProps()} />
          <Upload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive
              ? 'Drop the file here'
              : 'Drag & drop a document here, or click to select'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Supported formats: PDF, DOCX, TXT, MD (max 50MB)
          </Typography>
        </Box>

        {acceptedFiles.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Selected file:
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {acceptedFiles[0].name} ({(acceptedFiles[0].size / 1024 / 1024).toFixed(2)} MB)
            </Typography>
          </Box>
        )}

        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress variant="determinate" value={uploadProgress} />
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
              Uploading... {uploadProgress}%
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={uploading}>
          Cancel
        </Button>
        <Button
          onClick={handleUpload}
          variant="contained"
          disabled={acceptedFiles.length === 0 || uploading}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};