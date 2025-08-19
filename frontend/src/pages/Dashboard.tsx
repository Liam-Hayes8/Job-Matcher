import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Box,
  Chip,
  Skeleton,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { resumeApi, setAuthToken, fetchLiveJobs } from '../services/api';
import { useMockAuth as useAuth } from '../contexts/MockAuthContext';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import FindInPageIcon from '@mui/icons-material/FindInPage';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { getToken, user } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [debug, setDebug] = useState<any>(null);

  useEffect(() => {
    const setupAuth = async () => {
      const token = await getToken();
      setAuthToken(token);
    };
    setupAuth();
  }, [getToken]);

  const { data: resumes, isLoading, error } = useQuery({
    queryKey: ['resumes'],
    queryFn: () => resumeApi.getResumes().then(res => res.data),
    enabled: !!user,
  });

  const parseResumeMutation = useMutation({
    mutationFn: (resumeId: number) => resumeApi.parseResume(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      enqueueSnackbar('Resume parsed successfully!', { variant: 'success' });
    },
    onError: (error: any) => {
      console.error('Failed to parse resume:', error);
      enqueueSnackbar(
        error.response?.data?.detail || 'Failed to parse resume', 
        { variant: 'error' }
      );
    },
  });

  const deleteResumeMutation = useMutation({
    mutationFn: (resumeId: number) => resumeApi.deleteResume(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      enqueueSnackbar('Resume deleted successfully!', { variant: 'success' });
    },
    onError: (error: any) => {
      console.error('Failed to delete resume:', error);
      enqueueSnackbar(
        error.response?.data?.detail || 'Failed to delete resume', 
        { variant: 'error' }
      );
    },
  });

  const handleParseResume = async (resumeId: number) => {
    parseResumeMutation.mutate(resumeId);
  };

  const handleDeleteResume = async (resumeId: number) => {
    if (window.confirm('Are you sure you want to delete this resume?')) {
      deleteResumeMutation.mutate(resumeId);
    }
  };

  const handleFindJobs = async (resumeId: number) => {
    setLoading(true);
    try {
      const { jobs, debug } = await fetchLiveJobs({ 
        resumeId: resumeId.toString(), 
        debug: true 
      });
      setJobs(jobs);
      setDebug(debug);
      enqueueSnackbar(`Found ${jobs.length} job matches!`, { variant: 'success' });
    } catch (e) {
      enqueueSnackbar(String(e), { variant: 'error' });
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load resumes: {error.message}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
            <UploadFileIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Upload Resume
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Upload your resume to get started with job matching
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate('/upload')}
              sx={{ mt: 2 }}
              startIcon={<UploadFileIcon />}
            >
              Upload Resume
            </Button>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Resume Statistics
            </Typography>
            {isLoading ? (
              <Box>
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="40%" />
              </Box>
            ) : (
              <Box>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  Total Resumes: {resumes?.length || 0}
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  Parsed Resumes: {resumes?.filter(r => r.parsed_data).length || 0}
                </Typography>
                <Typography variant="body1">
                  Ready for Matching: {resumes?.filter(r => r.parsed_data).length || 0}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mt: 3, mb: 2 }}>
            Your Resumes
          </Typography>
          
          {isLoading ? (
            <Grid container spacing={2}>
              {[1, 2, 3].map((i) => (
                <Grid item xs={12} md={6} lg={4} key={i}>
                  <Card>
                    <CardContent>
                      <Skeleton variant="text" width="80%" />
                      <Skeleton variant="text" width="60%" />
                      <Skeleton variant="text" width="40%" />
                    </CardContent>
                    <CardActions>
                      <Skeleton variant="rectangular" width={60} height={32} />
                      <Skeleton variant="rectangular" width={60} height={32} />
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : resumes && resumes.length > 0 ? (
            <Grid container spacing={2}>
              {resumes.map((resume) => (
                <Grid item xs={12} md={6} lg={4} key={resume.id}>
                  <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" gutterBottom noWrap>
                        {resume.filename}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Uploaded: {new Date(resume.created_at).toLocaleDateString()}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {resume.parsed_data ? (
                          <Chip 
                            label="Parsed" 
                            color="success" 
                            size="small" 
                            icon={<PlayArrowIcon />}
                          />
                        ) : (
                          <Chip 
                            label="Not Parsed" 
                            color="warning" 
                            size="small" 
                          />
                        )}
                      </Box>
                    </CardContent>
                    <CardActions sx={{ justifyContent: 'space-between' }}>
                      <Box>
                        {!resume.parsed_data && (
                          <Button 
                            size="small"
                            variant="outlined"
                            onClick={() => handleParseResume(resume.id)}
                            disabled={parseResumeMutation.isPending}
                            startIcon={<PlayArrowIcon />}
                          >
                            {parseResumeMutation.isPending ? 'Parsing...' : 'Parse'}
                          </Button>
                        )}
                        {resume.parsed_data && (
                          <Button 
                            size="small"
                            variant="contained"
                            startIcon={<FindInPageIcon />}
                            onClick={() => handleFindJobs(resume.id)}
                            disabled={loading}
                          >
                            {loading ? 'Finding...' : 'Find Jobs'}
                          </Button>
                        )}
                      </Box>
                      <Button 
                        size="small" 
                        color="error"
                        variant="outlined"
                        onClick={() => handleDeleteResume(resume.id)}
                        disabled={deleteResumeMutation.isPending}
                        startIcon={<DeleteIcon />}
                      >
                        Delete
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <UploadFileIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom color="text.secondary">
                No resumes uploaded yet
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Upload your first resume to get started with job matching!
              </Typography>
              <Button
                variant="contained"
                onClick={() => navigate('/upload')}
                sx={{ mt: 2 }}
                startIcon={<UploadFileIcon />}
              >
                Upload Resume
              </Button>
            </Paper>
          )}
        </Grid>

        {/* Job Results Section */}
        {jobs.length > 0 && (
          <Grid item xs={12}>
            <Typography variant="h5" gutterBottom sx={{ mt: 3, mb: 2 }}>
              Job Matches
            </Typography>
            
            {/* Debug Info */}
            {debug && (
              <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Debug Info:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Resume ID: {debug.used_resume_id} | 
                  Tokens: {debug.tokens?.join(', ')}
                </Typography>
              </Paper>
            )}

            <Grid container spacing={2}>
              {jobs.map((job, index) => (
                <Grid item xs={12} md={6} lg={4} key={job.id || index}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {job.title}
                      </Typography>
                      <Typography variant="subtitle1" color="primary" gutterBottom>
                        {job.company}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {job.location}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {job.description?.substring(0, 150)}...
                      </Typography>
                      {job.apply_url && (
                        <Button
                          variant="contained"
                          size="small"
                          href={job.apply_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          fullWidth
                        >
                          Apply Now
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default Dashboard;