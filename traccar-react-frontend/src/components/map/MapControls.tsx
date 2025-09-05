import React from 'react';
import { 
  Box, 
  IconButton, 
  Paper, 
  Tooltip, 
  ToggleButton, 
  ToggleButtonGroup 
} from '@mui/material';
import {
  MyLocation,
  ZoomIn,
  ZoomOut,
  Layers,
  Traffic,
  Satellite
} from '@mui/icons-material';
import maplibregl from 'maplibre-gl';

interface MapControlsProps {
  map?: maplibregl.Map;
  mapReady?: boolean;
  onLocationClick?: () => void;
  showTraffic?: boolean;
  onTrafficToggle?: (show: boolean) => void;
  mapStyle?: 'streets' | 'satellite' | 'hybrid';
  onStyleChange?: (style: 'streets' | 'satellite' | 'hybrid') => void;
}

const MapControls: React.FC<MapControlsProps> = ({
  map,
  mapReady,
  onLocationClick,
  showTraffic = false,
  onTrafficToggle,
  mapStyle = 'streets',
  onStyleChange
}) => {
  const handleZoomIn = () => {
    if (map) {
      map.zoomIn();
    }
  };

  const handleZoomOut = () => {
    if (map) {
      map.zoomOut();
    }
  };

  const handleLocationClick = () => {
    if (onLocationClick) {
      onLocationClick();
    } else if (navigator.geolocation && map) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          map.flyTo({
            center: [position.coords.longitude, position.coords.latitude],
            zoom: 15,
            duration: 2000
          });
        },
        (error) => {
          console.error('Error getting location:', error);
        }
      );
    }
  };

  const handleTrafficToggle = () => {
    if (onTrafficToggle) {
      onTrafficToggle(!showTraffic);
    }
  };

  const handleStyleChange = (
    _: React.MouseEvent<HTMLElement>,
    newStyle: 'streets' | 'satellite' | 'hybrid' | null
  ) => {
    if (newStyle && onStyleChange) {
      onStyleChange(newStyle);
    }
  };

  if (!mapReady) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        top: 120,
        left: 16,
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: 1
      }}
    >
      {/* Zoom Controls */}
      <Paper elevation={2}>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Tooltip title="Zoom In" placement="right">
            <IconButton 
              onClick={handleZoomIn}
              size="small"
              sx={{ borderRadius: '4px 4px 0 0' }}
            >
              <ZoomIn />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom Out" placement="right">
            <IconButton 
              onClick={handleZoomOut}
              size="small"
              sx={{ borderRadius: '0 0 4px 4px' }}
            >
              <ZoomOut />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* Location Control */}
      <Paper elevation={2}>
        <Tooltip title="My Location" placement="right">
          <IconButton onClick={handleLocationClick} size="small">
            <MyLocation />
          </IconButton>
        </Tooltip>
      </Paper>

      {/* Map Style Toggle */}
      <Paper elevation={2}>
        <ToggleButtonGroup
          value={mapStyle}
          exclusive
          onChange={handleStyleChange}
          orientation="vertical"
          size="small"
        >
          <ToggleButton value="streets">
            <Tooltip title="Street Map" placement="right">
              <Layers />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="satellite">
            <Tooltip title="Satellite" placement="right">
              <Satellite />
            </Tooltip>
          </ToggleButton>
        </ToggleButtonGroup>
      </Paper>

      {/* Traffic Toggle */}
      <Paper elevation={2}>
        <Tooltip title="Toggle Traffic" placement="right">
          <IconButton 
            onClick={handleTrafficToggle}
            size="small"
            color={showTraffic ? 'primary' : 'default'}
          >
            <Traffic />
          </IconButton>
        </Tooltip>
      </Paper>
    </Box>
  );
};

export default MapControls;
