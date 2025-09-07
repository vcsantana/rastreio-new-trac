import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import { useSelector } from 'react-redux';

const DashboardPage = () => {
  const user = useSelector((state) => state.auth.user);
  const [serverInfo, setServerInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchServerInfo = async () => {
      try {
        const response = await fetch('/health');
        if (response.ok) {
          const data = await response.json();
          setServerInfo(data);
        } else {
          setError('Failed to fetch server information');
        }
      } catch (err) {
        setError('Network error. Please check if the API is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchServerInfo();
  }, []);

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                User Information
              </Typography>
              <Typography variant="body1">
                <strong>Name:</strong> {user?.name || 'N/A'}
              </Typography>
              <Typography variant="body1">
                <strong>Email:</strong> {user?.email || 'N/A'}
              </Typography>
              <Typography variant="body1">
                <strong>Role:</strong> {user?.role || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Server Status
              </Typography>
              {serverInfo ? (
                <>
                  <Typography variant="body1">
                    <strong>Status:</strong> {serverInfo.status}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Version:</strong> {serverInfo.version}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Active Protocols:</strong> {serverInfo.protocols_active}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Cache Connected:</strong> {serverInfo.cache?.connected ? 'Yes' : 'No'}
                  </Typography>
                </>
              ) : (
                <Typography variant="body1">No server information available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button 
                  variant="contained" 
                  onClick={() => navigate('/map')}
                >
                  View Map
                </Button>
                <Button 
                  variant="contained" 
                  onClick={() => navigate('/devices')}
                >
                  Manage Devices
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => navigate('/events')}
                >
                  View Events
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => navigate('/reports')}
                >
                  Generate Reports
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                >
                  API Documentation
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DashboardPage;
