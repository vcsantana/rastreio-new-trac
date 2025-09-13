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

    map.addControl(control, theme.direction === 'rtl' ? 'bottom-right' : 'bottom-left');
    return () => {
      if (map && map.removeControl) {
        map.removeControl(control);
      }
    };
  }, [map, control, theme.direction]);

  // Set default unit to metric (km)
  useEffect(() => {
    control.setUnit('metric');
  }, [control]);

  return null;
};

export default MapScale;
