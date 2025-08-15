import React, { useEffect, useState } from 'react';
import {
  Typography,
  Button,
  Card,
  CardContent,
  Box,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Paper,
  Skeleton,
  Divider,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { matchApi, setAuthToken, JobMatch } from '../services/api';
import { useMockAuth as useAuth } from '../contexts/MockAuthContext';
import WorkIcon from '@mui/icons-material/Work';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SearchIcon from '@mui/icons-material/Search';
import StarIcon from '@mui/icons-material/Star';
import LaunchIcon from '@mui/icons-material/Launch';
import BusinessIcon from '@mui/icons-material/Business';

const JobMatches: React.FC = () => {
  const { resumeId } = useParams<{ resumeId: string }>();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const [matches, setMatches] = useState<JobMatch[]>([]);

  useEffect(() => {
    const setupAuth = async () => {
      const token = await getToken();
      setAuthToken(token);
    };
    setupAuth();
  }, [getToken]);

  const findMatchesMutation = useMutation({
    mutationFn: () => matchApi.findMatches(parseInt(resumeId!), 20),
    onSuccess: (response) => {
      setMatches(response.data);
      enqueueSnackbar('Job matches found successfully!', { variant: 'success' });
    },
    onError: (error: any) => {
      console.error('Failed to find matches:', error);
      enqueueSnackbar(
        error.response?.data?.detail || 'Failed to find job matches', 
        { variant: 'error' }
      );
    },
  });

  const { data: existingMatches, isLoading, error } = useQuery({
    queryKey: ['matches', resumeId],
    queryFn: () => matchApi.getMatches(parseInt(resumeId!)).then(res => res.data),
    enabled: !!resumeId,
  });

  // Update matches when data changes
  React.useEffect(() => {
    if (existingMatches && existingMatches.length > 0) {
      setMatches(existingMatches);
    }
  }, [existingMatches]);

  const handleFindMatches = () => {
    findMatchesMutation.mutate();
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 0.8) return <StarIcon />;
    return undefined;
  };

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return 'Salary not specified';
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    if (min) return `$${min.toLocaleString()}+`;
    if (max) return `Up to $${max.toLocaleString()}`;
    return 'Salary not specified';
  };

  const handleApplyClick = (url?: string) => {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    } else {
      enqueueSnackbar('Job application link not available', { variant: 'warning' });
    }
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load job matches: {error.message}
      </Alert>
    );
  }

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
          Job Matches
        </Typography>
        <Button
          variant="contained"
          onClick={handleFindMatches}
          disabled={findMatchesMutation.isPending}
          startIcon={<SearchIcon />}
        >
          {findMatchesMutation.isPending ? 'Finding Matches...' : 'Find New Matches'}
        </Button>
      </Box>

      {findMatchesMutation.isPending && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress />
          <Typography variant="body2" align="center" sx={{ mt: 1 }}>
            Analyzing your resume and finding the best job matches...
          </Typography>
        </Box>
      )}

      {matches.length === 0 && !findMatchesMutation.isPending && !isLoading && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No job matches found
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Click "Find New Matches" to analyze your resume and find suitable job opportunities.
          </Typography>
          <Button
            variant="contained"
            onClick={handleFindMatches}
            sx={{ mt: 2 }}
            startIcon={<SearchIcon />}
          >
            Find New Matches
          </Button>
        </Paper>
      )}

      {isLoading ? (
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} key={i}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="60%" height={32} />
                  <Skeleton variant="text" width="40%" height={24} />
                  <Skeleton variant="text" width="80%" />
                  <Skeleton variant="text" width="70%" />
                  <Skeleton variant="text" width="50%" />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Grid container spacing={3}>
          {matches.map((match, index) => (
            <Grid item xs={12} key={`${match.id || index}-${index}`}>
              <Card sx={{ position: 'relative' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {match.title}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <BusinessIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                        <Typography variant="subtitle1" color="text.secondary">
                          {match.company}
                        </Typography>
                        {match.source && (
                          <Chip
                            label={match.source}
                            size="small"
                            variant="outlined"
                            color="secondary"
                          />
                        )}
                      </Box>
                    </Box>
                    <Chip
                      label={`${Math.round(match.match_score * 100)}% Match`}
                      color={getScoreColor(match.match_score)}
                      icon={getScoreIcon(match.match_score)}
                      sx={{ ml: 2 }}
                    />
                  </Box>

                  <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                    {match.location && (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <LocationOnIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {match.location}
                        </Typography>
                      </Box>
                    )}
                    
                    {match.job_type && (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <WorkIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {match.job_type}
                        </Typography>
                      </Box>
                    )}

                    {(match.salary_min || match.salary_max) && (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <AttachMoneyIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {formatSalary(match.salary_min, match.salary_max)}
                        </Typography>
                      </Box>
                    )}

                    {match.remote && (
                      <Chip
                        label={match.remote}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="body2" paragraph>
                    {match.description.length > 300
                      ? `${match.description.substring(0, 300)}...`
                      : match.description
                    }
                  </Typography>

                  {match.matching_skills.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Matching Skills:
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {match.matching_skills.slice(0, 10).map((skill, skillIndex) => (
                          <Chip
                            key={skillIndex}
                            label={skill}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        ))}
                        {match.matching_skills.length > 10 && (
                          <Chip
                            label={`+${match.matching_skills.length - 10} more`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={() => handleApplyClick(match.url)}
                      startIcon={<LaunchIcon />}
                      disabled={!match.url}
                    >
                      {match.url ? 'Apply Now' : 'Link Unavailable'}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {matches.length > 0 && (
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Found {matches.length} job matches for your resume
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default JobMatches;