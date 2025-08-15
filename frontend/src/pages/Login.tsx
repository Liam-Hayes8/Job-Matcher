import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useSnackbar } from 'notistack';
import { useMockAuth as useAuth } from '../contexts/MockAuthContext';
import { useNavigate } from 'react-router-dom';
import WorkIcon from '@mui/icons-material/Work';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';

const Login: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (tabValue === 0) {
        await login(email, password);
        enqueueSnackbar('Login successful!', { variant: 'success' });
      } else {
        await signup(email, password);
        enqueueSnackbar('Account created successfully!', { variant: 'success' });
      }
      navigate('/dashboard');
    } catch (error: any) {
      const errorMessage = error.message || 'Authentication failed';
      enqueueSnackbar(errorMessage, { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = email.trim() && password.trim() && password.length >= 6;

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="80vh"
      sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
    >
      <Paper 
        elevation={8} 
        sx={{ 
          p: 4, 
          width: '100%', 
          maxWidth: 400,
          borderRadius: 2,
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <WorkIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
            Job Matcher
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload your resume and find the perfect job match
          </Typography>
        </Box>
        
        <Tabs 
          value={tabValue} 
          onChange={(_, newValue) => setTabValue(newValue)}
          centered
          sx={{ mb: 3 }}
        >
          <Tab label="Login" />
          <Tab label="Sign Up" />
        </Tabs>

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
            required
            InputProps={{
              startAdornment: <PersonIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            required
            InputProps={{
              startAdornment: <LockIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ mb: 3 }}
            helperText={tabValue === 1 ? "Password must be at least 6 characters" : ""}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading || !isFormValid}
            sx={{ 
              py: 1.5,
              fontSize: '1.1rem',
              fontWeight: 600,
            }}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              tabValue === 0 ? 'Login' : 'Sign Up'
            )}
          </Button>
        </form>

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            {tabValue === 0 ? "Don't have an account?" : "Already have an account?"}
          </Typography>
          <Button
            variant="text"
            onClick={() => setTabValue(tabValue === 0 ? 1 : 0)}
            sx={{ mt: 1 }}
          >
            {tabValue === 0 ? 'Sign Up' : 'Login'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default Login;