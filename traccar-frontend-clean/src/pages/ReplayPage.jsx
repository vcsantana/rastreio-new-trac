import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Button,
  Slider,
  IconButton,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  TextField
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  FastForward,
  FastRewind,
  Download,
  Tune
} from '@mui/icons-material';
import { useSelector } from 'react-redux';

const ReplayPage = () => {
  const user = useSelector((state) => state.auth.user);
  const [positions, setPositions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showControls, setShowControls] = useState(true);

  useEffect(() => {
    let interval;
    if (playing && positions.length > 0) {
      interval = setInterval(() => {
        setCurrentIndex(prev => {
          if (prev >= positions.length - 1) {
            setPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [playing, positions]);

  const handleLoadPositions = async () => {
    if (!deviceId || !dateFrom || !dateTo) {
      setError('Please fill all fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/positions?deviceId=${deviceId}&from=${dateFrom}&to=${dateTo}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPositions(data);
        setCurrentIndex(0);
        setShowControls(false);
      } else {
        setError('Failed to load positions');
      }
    } catch (err) {
      setError('Network error. Please check if the API is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (positions.length > 0) {
      const query = new URLSearchParams({ deviceId, from: dateFrom, to: dateTo });
      window.open(`/api/positions/kml?${query.toString()}`, '_blank');
    }
  };

  const currentPosition = positions[currentIndex];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Replay
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Replay Controls
            </Typography>

            {showControls ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  fullWidth
                  label="Device ID"
                  value={deviceId}
                  onChange={(e) => setDeviceId(e.target.value)}
                  placeholder="Enter device ID"
                />

                <TextField
                  fullWidth
                  label="From Date"
                  type="datetime-local"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />

                <TextField
                  fullWidth
                  label="To Date"
                  type="datetime-local"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />

                <Button
                  variant="contained"
                  onClick={handleLoadPositions}
                  disabled={loading}
                  fullWidth
                >
                  {loading ? <CircularProgress size={24} /> : 'Load Positions'}
                </Button>
              </Box>
            ) : (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="subtitle1">
                    {positions.length} positions loaded
                  </Typography>
                  <IconButton onClick={() => setShowControls(true)}>
                    <Tune />
                  </IconButton>
                </Box>

                {positions.length > 0 && (
                  <>
                    <Typography variant="body2" gutterBottom>
                      Position {currentIndex + 1} of {positions.length}
                    </Typography>
                    
                    <Slider
                      value={currentIndex}
                      min={0}
                      max={positions.length - 1}
                      onChange={(_, value) => setCurrentIndex(value)}
                      sx={{ mb: 2 }}
                    />

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <IconButton 
                        onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
                        disabled={playing}
                      >
                        <FastRewind />
                      </IconButton>

                      <IconButton 
                        onClick={() => setPlaying(!playing)}
                        disabled={currentIndex >= positions.length - 1}
                      >
                        {playing ? <Pause /> : <PlayArrow />}
                      </IconButton>

                      <IconButton 
                        onClick={() => setCurrentIndex(Math.min(positions.length - 1, currentIndex + 1))}
                        disabled={playing}
                      >
                        <FastForward />
                      </IconButton>

                      <IconButton onClick={handleDownload}>
                        <Download />
                      </IconButton>
                    </Box>
                  </>
                )}
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ height: 500, p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Map View
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
                Map component will show replay here
                <br />
                Current position: {currentIndex + 1}/{positions.length}
              </Typography>
            </Box>
          </Paper>

          {currentPosition && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Position Details
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      <strong>Latitude:</strong> {currentPosition.latitude}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      <strong>Longitude:</strong> {currentPosition.longitude}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      <strong>Speed:</strong> {currentPosition.speed || 0} km/h
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      <strong>Course:</strong> {currentPosition.course || 0}°
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2">
                      <strong>Time:</strong> {new Date(currentPosition.fixTime).toLocaleString()}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default ReplayPage;

