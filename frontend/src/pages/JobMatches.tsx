import React, { useEffect, useState, useRef } from 'react';
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
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSnackbar } from 'notistack';
import { matchApi, liveJobApi, setAuthToken, JobMatch, LiveJobSearchRequest } from '../services/api';
import { fetchLiveJobs } from '../lib/jobs';
import { useMockAuth as useAuth } from '../contexts/MockAuthContext';
import WorkIcon from '@mui/icons-material/Work';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SearchIcon from '@mui/icons-material/Search';
import StarIcon from '@mui/icons-material/Star';
import LaunchIcon from '@mui/icons-material/Launch';
import BusinessIcon from '@mui/icons-material/Business';
import RefreshIcon from '@mui/icons-material/Refresh';
import ScheduleIcon from '@mui/icons-material/Schedule';
import SchoolIcon from '@mui/icons-material/School';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const JobMatches: React.FC = () => {
  const { resumeId } = useParams<{ resumeId: string }>();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [searchMetadata, setSearchMetadata] = useState<any>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const setupAuth = async () => {
      const token = await getToken();
      setAuthToken(token);
    };
    setupAuth();
  }, [getToken]);

  // Live job search mutation
  const liveSearchMutation = useMutation({
    mutationFn: async () => {
      // Cancel any previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      
      // Create new abort controller
      abortControllerRef.current = new AbortController();
      
      return fetchLiveJobs({ 
        resumeId: resumeId, 
        debug: true,
        limit: 40
      });
    },
    onSuccess: (response) => {
      setMatches(response.jobs);
      setSearchMetadata(response.debug);
      enqueueSnackbar(`Found ${response.jobs.length} fresh job matches!`, { variant: 'success' });
    },
    onError: (error: any) => {
      if (error.name === 'AbortError') {
        enqueueSnackbar('Search cancelled', { variant: 'info' });
      } else {
        console.error('Failed to find live matches:', error);
        enqueueSnackbar(
          error.message || 'Failed to find live job matches', 
          { variant: 'error' }
        );
      }
    },
  });

  // Legacy matches query (fallback)
  const { data: existingMatches, isLoading, error } = useQuery({
    queryKey: ['matches', resumeId],
    queryFn: () => matchApi.getMatches(parseInt(resumeId!)).then(res => res.data),
    enabled: !!resumeId && !liveSearchMutation.isPending,
  });

  // Update matches when data changes
  React.useEffect(() => {
    if (existingMatches && existingMatches.length > 0 && !liveSearchMutation.isPending) {
      setMatches(existingMatches);
    }
  }, [existingMatches, liveSearchMutation.isPending]);

  const handleFindLiveMatches = () => {
    if (!resumeId) {
      enqueueSnackbar('Resume ID not found', { variant: 'error' });
      return;
    }

    liveSearchMutation.mutate();
  };

  const handleCancelSearch = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
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
          Internship Matches
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {liveSearchMutation.isPending ? (
            <Button
              variant="outlined"
              onClick={handleCancelSearch}
              startIcon={<RefreshIcon />}
              color="warning"
            >
              Cancel Search
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleFindLiveMatches}
              disabled={liveSearchMutation.isPending}
              startIcon={<SearchIcon />}
            >
              Find Live Jobs
            </Button>
          )}
        </Box>
      </Box>

      {/* Search metadata */}
      {searchMetadata && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'primary.50' }}>
          <Typography variant="subtitle2" gutterBottom>
            Search Results
          </Typography>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Typography variant="body2">
              <strong>Resume ID:</strong> {searchMetadata.used_resume_id || 'N/A'}
            </Typography>
            <Typography variant="body2">
              <strong>Tokens:</strong> {(searchMetadata.tokens || []).join(', ')}
            </Typography>
            <Typography variant="body2">
              <strong>Jobs found:</strong> {matches.length}
            </Typography>
          </Box>
        </Paper>
      )}

      {liveSearchMutation.isPending && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress />
          <Typography variant="body2" align="center" sx={{ mt: 1 }}>
            Searching for fresh internship opportunities in real-time...
          </Typography>
        </Box>
      )}

      {matches.length === 0 && !liveSearchMutation.isPending && !isLoading && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No internship matches found
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Click "Find Live Jobs" to search for fresh internship opportunities in real-time.
          </Typography>
          <Button
            variant="contained"
            onClick={handleFindLiveMatches}
            sx={{ mt: 2 }}
            startIcon={<SearchIcon />}
          >
            Find Live Jobs
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

                    {/* Internship Duration */}
                    {(match as any).duration && (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <ScheduleIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {(match as any).duration}
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

                  {/* Internship Requirements */}
                  {(match as any).requirements && (match as any).requirements.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                        <SchoolIcon sx={{ fontSize: 16, mr: 0.5 }} />
                        Requirements:
                      </Typography>
                      <List dense sx={{ py: 0 }}>
                        {(match as any).requirements.slice(0, 3).map((requirement: string, reqIndex: number) => (
                          <ListItem key={reqIndex} sx={{ py: 0.5, px: 0 }}>
                            <ListItemIcon sx={{ minWidth: 24 }}>
                              <CheckCircleIcon sx={{ fontSize: 16, color: 'primary.main' }} />
                            </ListItemIcon>
                            <ListItemText 
                              primary={requirement}
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        ))}
                        {(match as any).requirements.length > 3 && (
                          <ListItem sx={{ py: 0.5, px: 0 }}>
                            <ListItemText 
                              primary={`+${(match as any).requirements.length - 3} more requirements`}
                              primaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
                            />
                          </ListItem>
                        )}
                      </List>
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                    {(match.apply_url || match.url) ? (
                      <Button
                        component="a"
                        href={match.apply_url || match.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="contained"
                        color="primary"
                        startIcon={<LaunchIcon />}
                        sx={{ textDecoration: 'none' }}
                      >
                        Apply Now
                      </Button>
                    ) : (
                      <Button
                        variant="contained"
                        color="primary"
                        disabled
                        startIcon={<LaunchIcon />}
                      >
                        Link Unavailable
                      </Button>
                    )}
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
          Found {matches.length} internship matches for your resume
        </Typography>
        </Box>
      )}
    </Box>
  );
};

export default JobMatches;