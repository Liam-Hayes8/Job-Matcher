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
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from 'react-query';
import { matchApi, setAuthToken, JobMatch } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import WorkIcon from '@mui/icons-material/Work';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';

const JobMatches: React.FC = () => {
  const { resumeId } = useParams<{ resumeId: string }>();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [matches, setMatches] = useState<JobMatch[]>([]);

  useEffect(() => {
    const setupAuth = async () => {
      const token = await getToken();
      setAuthToken(token);
    };
    setupAuth();
  }, [getToken]);

  const findMatchesMutation = useMutation(
    () => matchApi.findMatches(parseInt(resumeId!), 20),
    {
      onSuccess: (response) => {
        setMatches(response.data);
      },
      onError: (error: any) => {
        console.error('Failed to find matches:', error);
      },
    }
  );

  const { data: existingMatches, isLoading } = useQuery(
    ['matches', resumeId],
    () => matchApi.getMatches(parseInt(resumeId!)).then(res => res.data),
    {
      enabled: !!resumeId,
      onSuccess: (data) => {
        if (data.length > 0) {
          setMatches(data);
        }
      },
    }
  );

  const handleFindMatches = () => {
    findMatchesMutation.mutate();
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return 'Salary not specified';
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    if (min) return `$${min.toLocaleString()}+`;
    if (max) return `Up to $${max.toLocaleString()}`;
    return 'Salary not specified';
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ flexGrow: 1 }}>
          Job Matches
        </Typography>
        <Button
          variant="outlined"
          onClick={() => navigate('/dashboard')}
          sx={{ mr: 2 }}
        >
          Back to Dashboard
        </Button>
        <Button
          variant="contained"
          onClick={handleFindMatches}
          disabled={findMatchesMutation.isLoading}
        >
          {findMatchesMutation.isLoading ? 'Finding Matches...' : 'Find New Matches'}
        </Button>
      </Box>

      {findMatchesMutation.isLoading && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress />
          <Typography variant="body2" align="center" sx={{ mt: 1 }}>
            Analyzing your resume and finding the best job matches...
          </Typography>
        </Box>
      )}

      {matches.length === 0 && !findMatchesMutation.isLoading && (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            No job matches found
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Click "Find New Matches" to analyze your resume and find suitable job opportunities.
          </Typography>
        </Paper>
      )}

      <Grid container spacing={3}>
        {matches.map((match, index) => (
          <Grid item xs={12} key={`${match.job_listing.id}-${index}`}>
            <Card sx={{ position: 'relative' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" gutterBottom>
                      {match.job_listing.title}
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary" gutterBottom>
                      {match.job_listing.company}
                    </Typography>
                  </Box>
                  <Chip
                    label={`${Math.round(match.match_score * 100)}% Match`}
                    color={getScoreColor(match.match_score)}
                    sx={{ ml: 2 }}
                  />
                </Box>

                <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                  {match.job_listing.location && (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <LocationOnIcon sx={{ fontSize: 16, mr: 0.5 }} />
                      <Typography variant="body2">
                        {match.job_listing.location}
                      </Typography>
                    </Box>
                  )}
                  
                  {match.job_listing.job_type && (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <WorkIcon sx={{ fontSize: 16, mr: 0.5 }} />
                      <Typography variant="body2">
                        {match.job_listing.job_type}
                      </Typography>
                    </Box>
                  )}

                  {(match.job_listing.salary_min || match.job_listing.salary_max) && (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <AttachMoneyIcon sx={{ fontSize: 16, mr: 0.5 }} />
                      <Typography variant="body2">
                        {formatSalary(match.job_listing.salary_min, match.job_listing.salary_max)}
                      </Typography>
                    </Box>
                  )}

                  {match.job_listing.remote && (
                    <Chip
                      label={match.job_listing.remote}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Grid>

                <Typography variant="body2" paragraph>
                  {match.job_listing.description.length > 300
                    ? `${match.job_listing.description.substring(0, 300)}...`
                    : match.job_listing.description
                  }
                </Typography>

                {match.matching_skills.length > 0 && (
                  <Box>
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
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default JobMatches;