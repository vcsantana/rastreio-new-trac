/**
 * Geofence Map Component
 * Interactive map for viewing and editing geofences
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
  Layers as LayersIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { Geofence, GeoJSONGeometry } from '../../types/geofences';

interface GeofenceMapProps {
  geofences?: Geofence[];
  selectedGeofence?: Geofence;
  onGeofenceSelect?: (geofence: Geofence) => void;
  onGeofenceEdit?: (geofence: Geofence) => void;
  height?: number;
  showControls?: boolean;
  editable?: boolean;
}

// Mock map component - in a real implementation, you would use Leaflet, Mapbox, or Google Maps
const GeofenceMap: React.FC<GeofenceMapProps> = ({
  geofences = [],
  selectedGeofence,
  onGeofenceSelect,
  onGeofenceEdit,
  height = 400,
  showControls = true,
  editable = false
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(10);
  const [center, setCenter] = useState<[number, number]>([-23.5505, -46.6333]); // São Paulo

  // Mock map initialization
  useEffect(() => {
    const initMap = async () => {
      try {
        // Simulate map loading
        await new Promise(resolve => setTimeout(resolve, 1000));
        setMapLoaded(true);
      } catch (error) {
        setMapError('Failed to load map');
      }
    };

    initMap();
  }, []);

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 1, 18));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 1, 1));
  };

  const handleCenterMap = () => {
    if (selectedGeofence) {
      // Center on selected geofence
      const geometry = selectedGeofence.geometry_data;
      if (geometry) {
        if (geometry.type === 'Circle') {
          setCenter([geometry.coordinates[1], geometry.coordinates[0]]);
        } else if (geometry.type === 'Polygon' && geometry.coordinates[0]) {
          // Calculate center of polygon
          const coords = geometry.coordinates[0];
          const lat = coords.reduce((sum: number, coord: number[]) => sum + coord[1], 0) / coords.length;
          const lon = coords.reduce((sum: number, coord: number[]) => sum + coord[0], 0) / coords.length;
          setCenter([lat, lon]);
        }
      }
    } else {
      // Center on all geofences
      if (geofences.length > 0) {
        // Calculate bounds of all geofences
        let minLat = Infinity, maxLat = -Infinity;
        let minLon = Infinity, maxLon = -Infinity;

        geofences.forEach(geofence => {
          const geometry = geofence.geometry_data;
          if (geometry) {
            if (geometry.type === 'Circle') {
              const [lon, lat] = geometry.coordinates;
              minLat = Math.min(minLat, lat);
              maxLat = Math.max(maxLat, lat);
              minLon = Math.min(minLon, lon);
              maxLon = Math.max(maxLon, lon);
            } else if (geometry.type === 'Polygon' && geometry.coordinates[0]) {
              geometry.coordinates[0].forEach((coord: number[]) => {
                const [lon, lat] = coord;
                minLat = Math.min(minLat, lat);
                maxLat = Math.max(maxLat, lat);
                minLon = Math.min(minLon, lon);
                maxLon = Math.max(maxLon, lon);
              });
            }
          }
        });

        if (minLat !== Infinity) {
          const centerLat = (minLat + maxLat) / 2;
          const centerLon = (minLon + maxLon) / 2;
          setCenter([centerLat, centerLon]);
        }
      }
    }
  };

  const getGeofenceColor = (geofence: Geofence) => {
    if (geofence.disabled) return '#f44336';
    if (selectedGeofence?.id === geofence.id) return '#2196f3';
    
    switch (geofence.type) {
      case 'circle': return '#4caf50';
      case 'polygon': return '#ff9800';
      case 'polyline': return '#9c27b0';
      default: return '#757575';
    }
  };

  const renderGeofence = (geofence: Geofence) => {
    const geometry = geofence.geometry_data;
    if (!geometry) return null;

    const color = getGeofenceColor(geofence);
    const isSelected = selectedGeofence?.id === geofence.id;

    return (
      <div
        key={geofence.id}
        style={{
          position: 'absolute',
          border: `2px solid ${color}`,
          backgroundColor: `${color}20`,
          cursor: 'pointer',
          borderRadius: geometry.type === 'Circle' ? '50%' : '0',
          minWidth: '20px',
          minHeight: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          fontWeight: 'bold',
          color: color,
          zIndex: isSelected ? 10 : 1,
          transform: isSelected ? 'scale(1.1)' : 'scale(1)',
          transition: 'all 0.2s ease'
        }}
        onClick={() => onGeofenceSelect?.(geofence)}
        title={`${geofence.name} (${geofence.type})`}
      >
        {geofence.name.charAt(0).toUpperCase()}
      </div>
    );
  };

  if (mapError) {
    return (
      <Paper sx={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Alert severity="error">
          {mapError}
        </Alert>
      </Paper>
    );
  }

  if (!mapLoaded) {
    return (
      <Paper sx={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress />
          <Typography variant="body2" sx={{ mt: 1 }}>
            Loading map...
          </Typography>
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ height, position: 'relative', overflow: 'hidden' }}>
      {/* Map Container */}
      <Box
        ref={mapRef}
        sx={{
          width: '100%',
          height: '100%',
          background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {/* Mock map content */}
        <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
          <Typography variant="h6" gutterBottom>
            Interactive Map
          </Typography>
          <Typography variant="body2">
            Center: {center[0].toFixed(4)}, {center[1].toFixed(4)}
          </Typography>
          <Typography variant="body2">
            Zoom: {zoom}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {geofences.length} geofence{geofences.length !== 1 ? 's' : ''} displayed
          </Typography>
        </Box>

        {/* Render geofences */}
        {geofences.map(renderGeofence)}
      </Box>

      {/* Map Controls */}
      {showControls && (
        <Box
          sx={{
            position: 'absolute',
            top: 16,
            right: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 1
          }}
        >
          <Tooltip title="Zoom In">
            <IconButton onClick={handleZoomIn} size="small" sx={{ bgcolor: 'white' }}>
              <ZoomInIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom Out">
            <IconButton onClick={handleZoomOut} size="small" sx={{ bgcolor: 'white' }}>
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Center Map">
            <IconButton onClick={handleCenterMap} size="small" sx={{ bgcolor: 'white' }}>
              <CenterIcon />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      {/* Geofence Info */}
      {selectedGeofence && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 16,
            left: 16,
            right: 16,
            bgcolor: 'white',
            p: 2,
            borderRadius: 1,
            boxShadow: 2
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="subtitle1" fontWeight="bold">
                {selectedGeofence.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedGeofence.type} • {selectedGeofence.disabled ? 'Disabled' : 'Active'}
              </Typography>
            </Box>
            {editable && onGeofenceEdit && (
              <Button
                size="small"
                startIcon={<EditIcon />}
                onClick={() => onGeofenceEdit(selectedGeofence)}
              >
                Edit
              </Button>
            )}
          </Box>
        </Box>
      )}

      {/* Legend */}
      {geofences.length > 0 && (
        <Box
          sx={{
            position: 'absolute',
            top: 16,
            left: 16,
            bgcolor: 'white',
            p: 1,
            borderRadius: 1,
            boxShadow: 1
          }}
        >
          <Typography variant="caption" fontWeight="bold" gutterBottom>
            Legend
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box sx={{ width: 12, height: 12, bgcolor: '#4caf50', borderRadius: '50%' }} />
              <Typography variant="caption">Circle</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box sx={{ width: 12, height: 12, bgcolor: '#ff9800' }} />
              <Typography variant="caption">Polygon</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box sx={{ width: 12, height: 2, bgcolor: '#9c27b0' }} />
              <Typography variant="caption">Polyline</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box sx={{ width: 12, height: 12, bgcolor: '#f44336', borderRadius: '50%' }} />
              <Typography variant="caption">Disabled</Typography>
            </Box>
          </Box>
        </Box>
      )}
    </Paper>
  );
};

export default GeofenceMap;
