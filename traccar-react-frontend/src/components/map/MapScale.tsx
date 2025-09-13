/**
 * Map Scale Component
 * Adds a scale control to the map
 * Based on traccar-web MapScale.js
 */

import React, { useEffect, useMemo } from 'react';
import { useTheme } from '@mui/material/styles';
import maplibregl from 'maplibre-gl';

interface MapScaleProps {
  map?: maplibregl.Map | null;
}

const MapScale: React.FC<MapScaleProps> = ({ map }) => {
  const theme = useTheme();

  // Create scale control instance
  const control = useMemo(() => new maplibregl.ScaleControl(), []);

  useEffect(() => {
    if (!map) return;

    // Add control to map
    map.addControl(control, theme.direction === 'rtl' ? 'bottom-right' : 'bottom-left');
    
    // Set default unit to metric (km) after control is added
    try {
      control.setUnit('metric');
    } catch (error) {
      console.warn('Failed to set scale unit:', error);
    }
    
    return () => {
      if (map && map.removeControl) {
        try {
          map.removeControl(control);
        } catch (error) {
          console.warn('Failed to remove scale control:', error);
        }
      }
    };
  }, [map, control, theme.direction]);

  return null;
};

export default MapScale;
