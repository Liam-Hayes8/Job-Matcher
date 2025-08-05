import React, { useEffect } from 'react';
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
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { resumeApi, setAuthToken } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import FindInPageIcon from '@mui/icons-material/FindInPage';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { getToken, user } = useAuth();

  useEffect(() => {
    const setupAuth = async () => {
      const token = await getToken();
      setAuthToken(token);
    };
    setupAuth();
  }, [getToken]);

  const { data: resumes, isLoading, refetch } = useQuery(
    'resumes',
    () => resumeApi.getResumes().then(res => res.data),
    {
      enabled: !!user,
    }
  );

  const handleParseResume = async (resumeId: number) => {
    try {
      await resumeApi.parseResume(resumeId);
      refetch();
    } catch (error) {
      console.error('Failed to parse resume:', error);
    }
  };

  const handleDeleteResume = async (resumeId: number) => {
    try {
      await resumeApi.deleteResume(resumeId);
      refetch();
    } catch (error) {
      console.error('Failed to delete resume:', error);
    }
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
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
            >
              Upload Resume
            </Button>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Resume Statistics
            </Typography>
            <Typography variant="body1">
              Total Resumes: {resumes?.length || 0}
            </Typography>
            <Typography variant="body1">
              Parsed Resumes: {resumes?.filter(r => r.parsed_data).length || 0}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Your Resumes
          </Typography>
          
          {resumes && resumes.length > 0 ? (
            <Grid container spacing={2}>
              {resumes.map((resume) => (
                <Grid item xs={12} md={6} lg={4} key={resume.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {resume.filename}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Uploaded: {new Date(resume.created_at).toLocaleDateString()}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {resume.parsed_data ? (
                          <Chip label="Parsed" color="success" size="small" />
                        ) : (
                          <Chip label="Not Parsed" color="warning" size="small" />
                        )}
                      </Box>
                    </CardContent>
                    <CardActions>
                      {!resume.parsed_data && (
                        <Button 
                          size="small"
                          onClick={() => handleParseResume(resume.id)}
                        >
                          Parse
                        </Button>
                      )}
                      {resume.parsed_data && (
                        <Button 
                          size="small"
                          startIcon={<FindInPageIcon />}
                          onClick={() => navigate(`/matches/${resume.id}`)}
                        >
                          Find Jobs
                        </Button>
                      )}
                      <Button 
                        size="small" 
                        color="error"
                        onClick={() => handleDeleteResume(resume.id)}
                      >
                        Delete
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                No resumes uploaded yet. Upload your first resume to get started!
              </Typography>
              <Button
                variant="outlined"
                onClick={() => navigate('/upload')}
                sx={{ mt: 2 }}
              >
                Upload Resume
              </Button>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;