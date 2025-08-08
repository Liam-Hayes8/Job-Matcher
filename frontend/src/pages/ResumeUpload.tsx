import React, { useState, useCallback } from 'react';
import {
  Paper,
  Typography,
  Button,
  Box,
  Alert,
  LinearProgress,
  CircularProgress,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { resumeApi } from '../services/api';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

const ResumeUpload: React.FC = () => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const uploadMutation = useMutation({
    mutationFn: (file: File) => resumeApi.uploadResume(file),
    onSuccess: () => {
      enqueueSnackbar('Resume uploaded successfully!', { variant: 'success' });
      navigate('/dashboard');
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Upload failed';
      enqueueSnackbar(errorMessage, { variant: 'error' });
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
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
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/dashboard')}
          sx={{ mr: 2 }}
        >
          Back to Dashboard
        </Button>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          Upload Resume
        </Typography>
      </Box>

      <Paper
        {...getRootProps()}
        sx={{
          p: 6,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: uploadMutation.isPending ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease-in-out',
          opacity: uploadMutation.isPending ? 0.6 : 1,
          '&:hover': {
            borderColor: uploadMutation.isPending ? 'grey.300' : 'primary.main',
            backgroundColor: uploadMutation.isPending ? 'background.paper' : 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} disabled={uploadMutation.isPending} />
        
        {uploadMutation.isPending ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <CircularProgress size={64} sx={{ mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Uploading Resume...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Please wait while we process your resume
            </Typography>
          </Box>
        ) : (
          <>
            <CloudUploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop your resume here' : 'Drag & drop your resume here'}
            </Typography>
            
            <Typography variant="body2" color="text.secondary" gutterBottom>
              or click to browse files
            </Typography>
            
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              Supported formats: PDF, TXT, DOCX (max 10MB)
            </Typography>
          </>
        )}
      </Paper>

      {uploadMutation.isPending && (
        <Box sx={{ mt: 3 }}>
          <LinearProgress />
          <Typography variant="body2" align="center" sx={{ mt: 1 }}>
            Uploading resume...
          </Typography>
        </Box>
      )}

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Tips for better results:
        </Typography>
        <Box component="ul" sx={{ pl: 2 }}>
          <Typography component="li" variant="body2" color="text.secondary">
            Use PDF format for best compatibility
          </Typography>
          <Typography component="li" variant="body2" color="text.secondary">
            Ensure your resume is clear and well-formatted
          </Typography>
          <Typography component="li" variant="body2" color="text.secondary">
            Include relevant skills and experience
          </Typography>
          <Typography component="li" variant="body2" color="text.secondary">
            Keep file size under 10MB
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default ResumeUpload;