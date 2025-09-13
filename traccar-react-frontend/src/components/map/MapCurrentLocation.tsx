/**
 * Map Current Location Component
 * Adds a geolocate control to the map for user location tracking
 * Based on traccar-web MapCurrentLocation.js
 */

import React, { useEffect } from 'react';
import { useTheme } from '@mui/material/styles';
import maplibregl from 'maplibre-gl';

interface MapCurrentLocationProps {
  map?: maplibregl.Map | null;
}

const MapCurrentLocation: React.FC<MapCurrentLocationProps> = ({ map }) => {
  const theme = useTheme();

  useEffect(() => {
    if (!map) return;

    const control = new maplibregl.GeolocateControl({
      positionOptions: {
        enableHighAccuracy: true,
        timeout: 5000,
      },
      trackUserLocation: true,
    });

    map.addControl(control, theme.direction === 'rtl' ? 'top-left' : 'top-right');
    return () => {
      if (map && map.removeControl) {
        map.removeControl(control);
      }
    };
  }, [map, theme.direction]);

  return null;
};

export default MapCurrentLocation;
