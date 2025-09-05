import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Divider,
} from '@mui/material';
import { useAuth } from '../../hooks/useAuth';

interface WebSocketTestPanelProps {
  onClose?: () => void;
}

export const WebSocketTestPanel: React.FC<WebSocketTestPanelProps> = ({ onClose }) => {
  const { token } = useAuth();
  const [deviceId, setDeviceId] = useState<number>(1);
  const [latitude, setLatitude] = useState<string>('-23.550520');
  const [longitude, setLongitude] = useState<string>('-46.633308');
  const [speed, setSpeed] = useState<string>('0');
  const [course, setCourse] = useState<string>('0');
  const [eventType, setEventType] = useState<string>('ignition_on');
  const [newStatus, setNewStatus] = useState<string>('online');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>('');

  const simulateGPSData = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/ws/simulate-gps-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          device_id: deviceId,
          latitude: parseFloat(latitude),
          longitude: parseFloat(longitude),
          speed: parseFloat(speed),
          course: parseFloat(course),
        }),
      });

      const result = await response.json();
      setMessage(`GPS data simulated: ${result.message}`);
    } catch (error) {
      setMessage(`Error: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const testEvent = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/ws/test-event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          device_id: deviceId,
          event_type: eventType,
        }),
      });

      const result = await response.json();
      setMessage(`Event broadcast: ${result.message}`);
    } catch (error) {
      setMessage(`Error: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const testDeviceStatus = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/ws/test-device-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          device_id: deviceId,
          new_status: newStatus,
        }),
      });

      const result = await response.json();
      setMessage(`Device status broadcast: ${result.message}`);
    } catch (error) {
      setMessage(`Error: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card sx={{ maxWidth: 600, margin: 'auto', mt: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          WebSocket Test Panel
        </Typography>
        
        {message && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {message}
          </Alert>
        )}

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              fullWidth
              label="Device ID"
              type="number"
              value={deviceId}
              onChange={(e) => setDeviceId(parseInt(e.target.value) || 1)}
            />
          </Grid>
        </Grid>

        <Divider sx={{ my: 2 }} />

        <Typography variant="subtitle1" gutterBottom>
          GPS Data Simulation
        </Typography>
        
        <Grid container spacing={2}>
          <Grid size={{ xs: 6 }}>
            <TextField
              fullWidth
              label="Latitude"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
            />
          </Grid>
          <Grid size={{ xs: 6 }}>
            <TextField
              fullWidth
              label="Longitude"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
            />
          </Grid>
          <Grid size={{ xs: 6 }}>
            <TextField
              fullWidth
              label="Speed (km/h)"
              type="number"
              value={speed}
              onChange={(e) => setSpeed(e.target.value)}
            />
          </Grid>
          <Grid size={{ xs: 6 }}>
            <TextField
              fullWidth
              label="Course (degrees)"
              type="number"
              value={course}
              onChange={(e) => setCourse(e.target.value)}
            />
          </Grid>
        </Grid>

        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            onClick={simulateGPSData}
            disabled={loading}
            fullWidth
          >
            Simulate GPS Data
          </Button>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Typography variant="subtitle1" gutterBottom>
          Event Testing
        </Typography>
        
        <Grid container spacing={2}>
          <Grid size={{ xs: 12 }}>
            <FormControl fullWidth>
              <InputLabel>Event Type</InputLabel>
              <Select
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
              >
                <MenuItem value="ignition_on">Ignition On</MenuItem>
                <MenuItem value="ignition_off">Ignition Off</MenuItem>
                <MenuItem value="motion_start">Motion Start</MenuItem>
                <MenuItem value="motion_stop">Motion Stop</MenuItem>
                <MenuItem value="sos">SOS</MenuItem>
                <MenuItem value="parking">Parking</MenuItem>
                <MenuItem value="power_cut">Power Cut</MenuItem>
                <MenuItem value="door">Door</MenuItem>
                <MenuItem value="vibration">Vibration</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            color="secondary"
            onClick={testEvent}
            disabled={loading}
            fullWidth
          >
            Test Event
          </Button>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Typography variant="subtitle1" gutterBottom>
          Device Status Testing
        </Typography>
        
        <Grid container spacing={2}>
          <Grid size={{ xs: 12 }}>
            <FormControl fullWidth>
              <InputLabel>New Status</InputLabel>
              <Select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
              >
                <MenuItem value="online">Online</MenuItem>
                <MenuItem value="offline">Offline</MenuItem>
                <MenuItem value="unknown">Unknown</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            color="warning"
            onClick={testDeviceStatus}
            disabled={loading}
            fullWidth
          >
            Test Device Status
          </Button>
        </Box>

        {onClose && (
          <Box sx={{ mt: 2 }}>
            <Button variant="outlined" onClick={onClose} fullWidth>
              Close
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
