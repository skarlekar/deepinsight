import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import apiService from '../services/api';
import { Document } from '../types';

interface DocumentUploadProps {
  onUploadSuccess?: (document: Document) => void;
  onUploadError?: (error: string) => void;
  allowedTypes?: string[];
  maxFileSize?: number;
}

interface FileUploadStatus {
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
  document?: Document;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUploadSuccess,
  onUploadError,
  allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
  ],
  maxFileSize = 100 * 1024 * 1024, // 100MB
}) => {
  const [uploadFiles, setUploadFiles] = useState<FileUploadStatus[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newUploads: FileUploadStatus[] = acceptedFiles.map(file => ({
      file,
      progress: 0,
      status: 'uploading',
    }));

    setUploadFiles(prev => [...prev, ...newUploads]);

    // Start uploading each file
    acceptedFiles.forEach((file, index) => {
      uploadFile(file, uploadFiles.length + index);
    });
  }, [uploadFiles.length]);

  const uploadFile = async (file: File, index: number) => {
    try {
      setUploadFiles(prev => prev.map((item, i) => 
        i === index ? { ...item, progress: 25 } : item
      ));

      const document = await apiService.uploadDocument(file);

      setUploadFiles(prev => prev.map((item, i) => 
        i === index 
          ? { ...item, progress: 100, status: 'completed', document }
          : item
      ));

      onUploadSuccess?.(document);
    } catch (error: any) {
      const errorMessage = error.response?.data?.error?.message || 'Upload failed';
      
      setUploadFiles(prev => prev.map((item, i) => 
        i === index 
          ? { ...item, status: 'error', error: errorMessage }
          : item
      ));

      onUploadError?.(errorMessage);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: allowedTypes.reduce((acc, type) => {
      acc[type] = [];
      return acc;
    }, {} as Record<string, string[]>),
    maxSize: maxFileSize,
  });

  const clearCompleted = () => {
    setUploadFiles(prev => prev.filter(item => item.status !== 'completed'));
  };

  const getFileIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'error':
        return <Error color="error" />;
      default:
        return <Description />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          mb: 2,
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        
        {isDragActive ? (
          <Typography variant="h6" color="primary">
            Drop files here...
          </Typography>
        ) : (
          <>
            <Typography variant="h6" gutterBottom>
              Drag & drop documents here
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              or click to browse files
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Supported formats: PDF, DOCX, TXT, MD (Max: {Math.round(maxFileSize / 1024 / 1024)}MB)
            </Typography>
          </>
        )}
      </Paper>

      {uploadFiles.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Upload Progress</Typography>
            <Button
              size="small"
              onClick={clearCompleted}
              disabled={!uploadFiles.some(item => item.status === 'completed')}
            >
              Clear Completed
            </Button>
          </Box>

          <List dense>
            {uploadFiles.map((item, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  {getFileIcon(item.status)}
                </ListItemIcon>
                <ListItemText
                  primary={item.file.name}
                  secondary={
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        {(item.file.size / 1024 / 1024).toFixed(1)} MB
                      </Typography>
                      {item.status === 'uploading' && (
                        <LinearProgress
                          variant="determinate"
                          value={item.progress}
                          sx={{ mt: 1 }}
                          color={getStatusColor(item.status) as any}
                        />
                      )}
                      {item.error && (
                        <Alert severity="error" sx={{ mt: 1 }}>
                          {item.error}
                        </Alert>
                      )}
                      {item.document && (
                        <Typography variant="caption" color="success.main">
                          Document ID: {item.document.id}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};