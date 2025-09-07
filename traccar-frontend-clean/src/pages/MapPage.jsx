import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import { useSelector } from 'react-redux';

const MapPage = () => {
  const user = useSelector((state) => state.auth.user);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/devices', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setDevices(data);
        } else {
          setError('Failed to fetch devices');
        }
      } catch (err) {
        setError('Network error. Please check if the API is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchDevices();
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
        Map View
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ height: 500, p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Interactive Map
            </Typography>
            <Box 
              sx={{ 
                height: 400, 
                backgroundColor: '#f5f5f5', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                border: '2px dashed #ccc'
              }}
            >
              <Typography variant="body1" color="text.secondary">
                Map component will be integrated here
                <br />
                (MapLibre GL, Google Maps, or OpenStreetMap)
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Device List
              </Typography>
              {devices.length > 0 ? (
                devices.map((device) => (
                  <Box key={device.id} sx={{ mb: 2, p: 1, border: '1px solid #eee', borderRadius: 1 }}>
                    <Typography variant="subtitle2">{device.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      ID: {device.unique_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Status: {device.status || 'Unknown'}
                    </Typography>
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No devices found
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default MapPage;
