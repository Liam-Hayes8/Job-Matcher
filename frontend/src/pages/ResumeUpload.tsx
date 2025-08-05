import React, { useState, useCallback } from 'react';
import {
  Paper,
  Typography,
  Button,
  Box,
  Alert,
  LinearProgress,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { useMutation } from 'react-query';
import { resumeApi } from '../services/api';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const ResumeUpload: React.FC = () => {
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const uploadMutation = useMutation(
    (file: File) => resumeApi.uploadResume(file),
    {
      onSuccess: () => {
        navigate('/dashboard');
      },
      onError: (error: any) => {
        setError(error.response?.data?.detail || 'Upload failed');
      },
    }
  );

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setError('');
      uploadMutation.mutate(acceptedFiles[0]);
    }
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Resume
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        
        <CloudUploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop your resume here' : 'Drag & drop your resume here'}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          or click to browse files
        </Typography>
        
        <Typography variant="caption" color="text.secondary">
          Supported formats: PDF, TXT, DOCX (max 10MB)
        </Typography>

        {uploadMutation.isLoading && (
          <Box sx={{ mt: 3 }}>
            <LinearProgress />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Uploading resume...
            </Typography>
          </Box>
        )}
      </Paper>

      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Button
          variant="outlined"
          onClick={() => navigate('/dashboard')}
          disabled={uploadMutation.isLoading}
        >
          Back to Dashboard
        </Button>
      </Box>
    </Box>
  );
};

export default ResumeUpload;