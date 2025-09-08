import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Alert,
  CircularProgress,
  Button,
  IconButton,
  Tooltip
} from '@mui/material';
import { Add, Edit, Delete, Upload } from '@mui/icons-material';
import { useSelector } from 'react-redux';

const GeofencesPage = () => {
  const user = useSelector((state) => state.auth.user);
  const [geofences, setGeofences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchGeofences = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/geofences', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setGeofences(data);
        } else {
          setError('Failed to fetch geofences');
        }
      } catch (err) {
        setError('Network error. Please check if the API is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchGeofences();
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Geofences
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Upload GPX">
            <IconButton variant="outlined" color="primary">
              <Upload />
            </IconButton>
          </Tooltip>
          <Button variant="contained" color="primary" startIcon={<Add />}>
            Add Geofence
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Area</TableCell>
              <TableCell>Calendar</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {geofences.length > 0 ? (
              geofences.map((geofence) => (
                <TableRow key={geofence.id}>
                  <TableCell>{geofence.id}</TableCell>
                  <TableCell>{geofence.name}</TableCell>
                  <TableCell>{geofence.description || 'No description'}</TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {geofence.area ? 'Defined' : 'Not defined'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {geofence.calendar_id ? 'Assigned' : 'None'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <IconButton size="small" color="primary">
                      <Edit />
                    </IconButton>
                    <IconButton size="small" color="error">
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No geofences found
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default GeofencesPage;

