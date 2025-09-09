/**
 * Geofence Geometry Editor Component
 * Editor for creating and editing geofence geometries
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  Alert,
  Divider,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Map as MapIcon,
  Circle as CircleIcon,
  Square as SquareIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { GeoJSONGeometry, EXAMPLE_GEOMETRIES } from '../../types/geofences';

interface GeofenceGeometryEditorProps {
  type: 'polygon' | 'circle' | 'polyline';
  geometry: string;
  geometryData: any;
  onChange: (geometry: string, geometryData: any) => void;
  disabled?: boolean;
}

interface Coordinate {
  lat: number;
  lon: number;
}

const GeofenceGeometryEditor: React.FC<GeofenceGeometryEditorProps> = ({
  type,
  geometry,
  geometryData,
  onChange,
  disabled = false
}) => {
  const [coordinates, setCoordinates] = useState<Coordinate[]>([]);
  const [radius, setRadius] = useState<number>(1000);
  const [center, setCenter] = useState<Coordinate>({ lat: -23.5505, lon: -46.6333 });
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [tempCoordinate, setTempCoordinate] = useState<Coordinate>({ lat: 0, lon: 0 });
  const [showExampleDialog, setShowExampleDialog] = useState(false);

  // Initialize coordinates from geometry data
  useEffect(() => {
    if (geometryData) {
      if (type === 'circle') {
        const [lon, lat, rad] = geometryData.coordinates;
        setCenter({ lat, lon });
        setRadius(rad);
      } else if (type === 'polygon' && geometryData.coordinates[0]) {
        const coords = geometryData.coordinates[0].map((coord: number[]) => ({
          lat: coord[1],
          lon: coord[0]
        }));
        setCoordinates(coords);
      } else if (type === 'polyline' && geometryData.coordinates) {
        const coords = geometryData.coordinates.map((coord: number[]) => ({
          lat: coord[1],
          lon: coord[0]
        }));
        setCoordinates(coords);
      }
    } else {
      // Initialize with default values
      setCoordinates([]);
      setRadius(1000);
      setCenter({ lat: -23.5505, lon: -46.6333 });
    }
  }, [type, geometryData]);

  // Generate geometry when coordinates change
  useEffect(() => {
    generateGeometry();
  }, [type, coordinates, radius, center]);

  const generateGeometry = () => {
    let newGeometry: GeoJSONGeometry;
    let newGeometryData: any;

    if (type === 'circle') {
      newGeometry = {
        type: 'Circle',
        coordinates: [center.lon, center.lat, radius]
      };
      newGeometryData = newGeometry;
    } else if (type === 'polygon') {
      if (coordinates.length < 3) {
        return; // Need at least 3 points for a polygon
      }
      // Close the polygon by adding the first point at the end
      const polygonCoords = [...coordinates.map(coord => [coord.lon, coord.lat])];
      if (polygonCoords.length > 0) {
        polygonCoords.push(polygonCoords[0]);
      }
      newGeometry = {
        type: 'Polygon',
        coordinates: [polygonCoords]
      };
      newGeometryData = newGeometry;
    } else if (type === 'polyline') {
      if (coordinates.length < 2) {
        return; // Need at least 2 points for a polyline
      }
      newGeometry = {
        type: 'LineString',
        coordinates: coordinates.map(coord => [coord.lon, coord.lat])
      };
      newGeometryData = newGeometry;
    } else {
      return;
    }

    onChange(JSON.stringify(newGeometry), newGeometryData);
  };

  const addCoordinate = () => {
    if (tempCoordinate.lat !== 0 || tempCoordinate.lon !== 0) {
      setCoordinates(prev => [...prev, tempCoordinate]);
      setTempCoordinate({ lat: 0, lon: 0 });
    }
  };

  const editCoordinate = (index: number) => {
    setEditingIndex(index);
    setTempCoordinate(coordinates[index]);
  };

  const saveCoordinate = () => {
    if (editingIndex !== null && (tempCoordinate.lat !== 0 || tempCoordinate.lon !== 0)) {
      setCoordinates(prev => 
        prev.map((coord, index) => 
          index === editingIndex ? tempCoordinate : coord
        )
      );
      setEditingIndex(null);
      setTempCoordinate({ lat: 0, lon: 0 });
    }
  };

  const deleteCoordinate = (index: number) => {
    setCoordinates(prev => prev.filter((_, i) => i !== index));
  };

  const loadExample = (exampleType: string) => {
    const example = EXAMPLE_GEOMETRIES[exampleType as keyof typeof EXAMPLE_GEOMETRIES];
    if (example) {
      if (exampleType === 'circle') {
        const [lon, lat, rad] = example.coordinates;
        setCenter({ lat, lon });
        setRadius(rad);
      } else if (exampleType === 'polygon' && example.coordinates[0]) {
        const coords = example.coordinates[0].map((coord: number[]) => ({
          lat: coord[1],
          lon: coord[0]
        }));
        setCoordinates(coords);
      } else if (exampleType === 'polyline' && example.coordinates) {
        const coords = example.coordinates.map((coord: number[]) => ({
          lat: coord[1],
          lon: coord[0]
        }));
        setCoordinates(coords);
      }
      setShowExampleDialog(false);
    }
  };

  const getTypeIcon = () => {
    switch (type) {
      case 'circle':
        return <CircleIcon />;
      case 'polygon':
        return <SquareIcon />;
      case 'polyline':
        return <TimelineIcon />;
      default:
        return <MapIcon />;
    }
  };

  const getMinPoints = () => {
    switch (type) {
      case 'circle':
        return 1;
      case 'polygon':
        return 3;
      case 'polyline':
        return 2;
      default:
        return 0;
    }
  };

  const isValid = () => {
    switch (type) {
      case 'circle':
        return radius > 0;
      case 'polygon':
        return coordinates.length >= 3;
      case 'polyline':
        return coordinates.length >= 2;
      default:
        return false;
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {getTypeIcon()}
          <Typography variant="h6">
            {type.charAt(0).toUpperCase() + type.slice(1)} Geometry
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<MapIcon />}
          onClick={() => setShowExampleDialog(true)}
          disabled={disabled}
        >
          Load Example
        </Button>
      </Box>

      {/* Validation */}
      {!isValid() && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {type === 'circle' && 'Please set a valid radius (greater than 0)'}
          {type === 'polygon' && 'Please add at least 3 coordinates to create a polygon'}
          {type === 'polyline' && 'Please add at least 2 coordinates to create a polyline'}
        </Alert>
      )}

      {/* Circle Editor */}
      {type === 'circle' && (
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Center Latitude"
              type="number"
              value={center.lat}
              onChange={(e) => setCenter(prev => ({ ...prev, lat: parseFloat(e.target.value) || 0 }))}
              disabled={disabled}
              inputProps={{ step: 0.000001, min: -90, max: 90 }}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Center Longitude"
              type="number"
              value={center.lon}
              onChange={(e) => setCenter(prev => ({ ...prev, lon: parseFloat(e.target.value) || 0 }))}
              disabled={disabled}
              inputProps={{ step: 0.000001, min: -180, max: 180 }}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Radius (meters)"
              type="number"
              value={radius}
              onChange={(e) => setRadius(parseFloat(e.target.value) || 0)}
              disabled={disabled}
              inputProps={{ min: 1, max: 1000000 }}
            />
          </Grid>
        </Grid>
      )}

      {/* Polygon/Polyline Editor */}
      {(type === 'polygon' || type === 'polyline') && (
        <Box>
          {/* Add New Coordinate */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Add Coordinate
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Latitude"
                  type="number"
                  value={tempCoordinate.lat}
                  onChange={(e) => setTempCoordinate(prev => ({ ...prev, lat: parseFloat(e.target.value) || 0 }))}
                  disabled={disabled}
                  inputProps={{ step: 0.000001, min: -90, max: 90 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Longitude"
                  type="number"
                  value={tempCoordinate.lon}
                  onChange={(e) => setTempCoordinate(prev => ({ ...prev, lon: parseFloat(e.target.value) || 0 }))}
                  disabled={disabled}
                  inputProps={{ step: 0.000001, min: -180, max: 180 }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={addCoordinate}
                  disabled={disabled || (tempCoordinate.lat === 0 && tempCoordinate.lon === 0)}
                >
                  Add Point
                </Button>
              </Grid>
            </Grid>
          </Paper>

          {/* Coordinates List */}
          {coordinates.length > 0 && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Coordinates ({coordinates.length} points)
              </Typography>
              <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                {coordinates.map((coord, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      p: 1,
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1
                    }}
                  >
                    <Chip label={index + 1} size="small" />
                    <Typography variant="body2" sx={{ flexGrow: 1 }}>
                      {coord.lat.toFixed(6)}, {coord.lon.toFixed(6)}
                    </Typography>
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => editCoordinate(index)}
                        disabled={disabled}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        onClick={() => deleteCoordinate(index)}
                        disabled={disabled}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                ))}
              </Box>
            </Paper>
          )}

          {/* Edit Coordinate Dialog */}
          {editingIndex !== null && (
            <Dialog open={editingIndex !== null} onClose={() => setEditingIndex(null)}>
              <DialogTitle>Edit Coordinate {editingIndex + 1}</DialogTitle>
              <DialogContent>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Latitude"
                      type="number"
                      value={tempCoordinate.lat}
                      onChange={(e) => setTempCoordinate(prev => ({ ...prev, lat: parseFloat(e.target.value) || 0 }))}
                      inputProps={{ step: 0.000001, min: -90, max: 90 }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Longitude"
                      type="number"
                      value={tempCoordinate.lon}
                      onChange={(e) => setTempCoordinate(prev => ({ ...prev, lon: parseFloat(e.target.value) || 0 }))}
                      inputProps={{ step: 0.000001, min: -180, max: 180 }}
                    />
                  </Grid>
                </Grid>
              </DialogContent>
              <DialogActions>
                <Button onClick={() => setEditingIndex(null)}>Cancel</Button>
                <Button onClick={saveCoordinate} variant="contained">Save</Button>
              </DialogActions>
            </Dialog>
          )}
        </Box>
      )}

      {/* Geometry Preview */}
      {geometryData && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Geometry Preview
          </Typography>
          <Box
            component="pre"
            sx={{
              bgcolor: 'grey.100',
              p: 1,
              borderRadius: 1,
              fontSize: '0.75rem',
              overflow: 'auto',
              maxHeight: 200
            }}
          >
            {JSON.stringify(geometryData, null, 2)}
          </Box>
        </Paper>
      )}

      {/* Example Dialog */}
      <Dialog open={showExampleDialog} onClose={() => setShowExampleDialog(false)}>
        <DialogTitle>Load Example Geometry</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Choose an example geometry to get started:
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 2 }}>
            <Button
              variant="outlined"
              startIcon={<CircleIcon />}
              onClick={() => loadExample('circle')}
            >
              Circle Example (São Paulo, 1km radius)
            </Button>
            <Button
              variant="outlined"
              startIcon={<SquareIcon />}
              onClick={() => loadExample('polygon')}
            >
              Polygon Example (São Paulo area)
            </Button>
            <Button
              variant="outlined"
              startIcon={<TimelineIcon />}
              onClick={() => loadExample('polyline')}
            >
              Polyline Example (São Paulo route)
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowExampleDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GeofenceGeometryEditor;
