/**
 * Geofence Test Dialog Component
 * Dialog for testing geofences with coordinates
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Divider
} from '@mui/material';
import {
  TestTube as TestIcon,
  CheckCircle as InsideIcon,
  Cancel as OutsideIcon,
  LocationOn as LocationIcon
} from '@mui/icons-material';
import { useGeofences } from '../../hooks/useGeofences';
import { GeofenceTestRequest, GeofenceTestResponse } from '../../types/geofences';

interface GeofenceTestDialogProps {
  open: boolean;
  onClose: () => void;
}

const GeofenceTestDialog: React.FC<GeofenceTestDialogProps> = ({
  open,
  onClose
}) => {
  const { testGeofences, loading, error, clearError } = useGeofences();
  
  const [testRequest, setTestRequest] = useState<GeofenceTestRequest>({
    latitude: -23.5505,
    longitude: -46.6333
  });
  const [testResults, setTestResults] = useState<GeofenceTestResponse[]>([]);
  const [hasTested, setHasTested] = useState(false);

  const handleInputChange = (field: keyof GeofenceTestRequest, value: number) => {
    setTestRequest(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTest = async () => {
    try {
      const results = await testGeofences(testRequest);
      setTestResults(results);
      setHasTested(true);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleClose = () => {
    setTestRequest({ latitude: -23.5505, longitude: -46.6333 });
    setTestResults([]);
    setHasTested(false);
    clearError();
    onClose();
  };

  const formatDistance = (distance?: number) => {
    if (distance === undefined || distance === null) return 'N/A';
    
    if (distance < 1000) {
      return `${distance.toFixed(0)} m`;
    } else {
      return `${(distance / 1000).toFixed(2)} km`;
    }
  };

  const getInsideCount = () => {
    return testResults.filter(result => result.is_inside).length;
  };

  const getOutsideCount = () => {
    return testResults.filter(result => !result.is_inside).length;
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TestIcon />
          Test Geofences
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={clearError}>
            {error}
          </Alert>
        )}

        {/* Test Coordinates */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Test Coordinates
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Latitude"
                type="number"
                value={testRequest.latitude}
                onChange={(e) => handleInputChange('latitude', parseFloat(e.target.value) || 0)}
                inputProps={{ step: 0.000001, min: -90, max: 90 }}
                helperText="Enter latitude to test (-90 to 90)"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Longitude"
                type="number"
                value={testRequest.longitude}
                onChange={(e) => handleInputChange('longitude', parseFloat(e.target.value) || 0)}
                inputProps={{ step: 0.000001, min: -180, max: 180 }}
                helperText="Enter longitude to test (-180 to 180)"
              />
            </Grid>
          </Grid>
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={16} /> : <TestIcon />}
              onClick={handleTest}
              disabled={loading}
            >
              Test Geofences
            </Button>
          </Box>
        </Paper>

        {/* Test Results */}
        {hasTested && (
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Test Results
            </Typography>
            
            {/* Summary */}
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Chip
                icon={<InsideIcon />}
                label={`${getInsideCount()} Inside`}
                color="success"
                variant="filled"
              />
              <Chip
                icon={<OutsideIcon />}
                label={`${getOutsideCount()} Outside`}
                color="default"
                variant="outlined"
              />
              <Chip
                label={`${testResults.length} Total`}
                color="primary"
                variant="outlined"
              />
            </Box>

            <Divider sx={{ mb: 2 }} />

            {/* Results Table */}
            {testResults.length > 0 ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Geofence</TableCell>
                      <TableCell align="center">Status</TableCell>
                      <TableCell align="center">Distance</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {testResults.map((result) => (
                      <TableRow key={result.geofence_id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {result.geofence_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ID: {result.geofence_id}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            icon={result.is_inside ? <InsideIcon /> : <OutsideIcon />}
                            label={result.is_inside ? 'Inside' : 'Outside'}
                            color={result.is_inside ? 'success' : 'default'}
                            size="small"
                            variant={result.is_inside ? 'filled' : 'outlined'}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Typography variant="body2">
                            {formatDistance(result.distance)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <LocationIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  No geofences found to test
                </Typography>
              </Box>
            )}
          </Paper>
        )}

        {/* Quick Test Locations */}
        <Paper sx={{ p: 2, mt: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Quick Test Locations
          </Typography>
          <Grid container spacing={1}>
            <Grid item xs={12} sm={4}>
              <Button
                fullWidth
                variant="outlined"
                size="small"
                onClick={() => setTestRequest({ latitude: -23.5505, longitude: -46.6333 })}
              >
                São Paulo, Brazil
              </Button>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Button
                fullWidth
                variant="outlined"
                size="small"
                onClick={() => setTestRequest({ latitude: 40.7128, longitude: -74.0060 })}
              >
                New York, USA
              </Button>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Button
                fullWidth
                variant="outlined"
                size="small"
                onClick={() => setTestRequest({ latitude: 51.5074, longitude: -0.1278 })}
              >
                London, UK
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default GeofenceTestDialog;
