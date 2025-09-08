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
  Chip,
  Button,
  TextField,
  Grid
} from '@mui/material';
import { useSelector } from 'react-redux';

const EventsPage = () => {
  const user = useSelector((state) => state.auth.user);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('');

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/events', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setEvents(data);
        } else {
          setError('Failed to fetch events');
        }
      } catch (err) {
        setError('Network error. Please check if the API is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  const getEventColor = (type) => {
    const colors = {
      'alarm': 'error',
      'warning': 'warning',
      'info': 'info',
      'success': 'success',
      'default': 'default'
    };
    return colors[type] || 'default';
  };

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
          Events
        </Typography>
        <Button variant="contained" color="primary">
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Filter events"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Search by device name, event type..."
          />
        </Grid>
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Device</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Message</TableCell>
              <TableCell>Time</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {events.length > 0 ? (
              events
                .filter(event => 
                  !filter || 
                  event.device_name?.toLowerCase().includes(filter.toLowerCase()) ||
                  event.type?.toLowerCase().includes(filter.toLowerCase())
                )
                .map((event) => (
                <TableRow key={event.id}>
                  <TableCell>{event.id}</TableCell>
                  <TableCell>{event.device_name || 'Unknown'}</TableCell>
                  <TableCell>
                    <Chip 
                      label={event.type || 'Unknown'} 
                      color={getEventColor(event.type)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{event.message || 'No message'}</TableCell>
                  <TableCell>
                    {event.event_time ? new Date(event.event_time).toLocaleString() : 'Unknown'}
                  </TableCell>
                  <TableCell>
                    <Button size="small" variant="outlined">
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No events found
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

export default EventsPage;

