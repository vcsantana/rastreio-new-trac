/**
 * Map Geofence Edit Component
 * Allows drawing and editing geofences on the map (based on traccar-web)
 */

import React, { useEffect, useMemo } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '@mui/material/styles';
import maplibregl from 'maplibre-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';

import { useGeofences } from '../../hooks/useGeofences';
import { useAuth } from '../../contexts/AuthContext';

// Extend MapboxDraw constants for MapLibre compatibility
(MapboxDraw as any).constants.classes.CONTROL_BASE = 'maplibregl-ctrl';
(MapboxDraw as any).constants.classes.CONTROL_PREFIX = 'maplibregl-ctrl-';
(MapboxDraw as any).constants.classes.CONTROL_GROUP = 'maplibregl-ctrl-group';

interface MapGeofenceEditProps {
  map?: maplibregl.Map | null;
  selectedGeofenceId?: number;
}

const MapGeofenceEdit: React.FC<MapGeofenceEditProps> = ({
  map,
  selectedGeofenceId
}) => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { token } = useAuth();
  const { geofences, fetchGeofences } = useGeofences();

  // Draw theme configuration
  const drawTheme = useMemo(() => [
    {
      id: 'gl-draw-polygon-fill-inactive',
      type: 'fill',
      filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'Polygon'], ['!=', 'mode', 'static']],
      paint: {
        'fill-color': '#3bb2d0',
        'fill-outline-color': '#3bb2d0',
        'fill-opacity': 0.1,
      },
    },
    {
      id: 'gl-draw-polygon-fill-active',
      type: 'fill',
      filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'Polygon']],
      paint: {
        'fill-color': '#fbb03b',
        'fill-outline-color': '#fbb03b',
        'fill-opacity': 0.1,
      },
    },
    {
      id: 'gl-draw-polygon-midpoint',
      type: 'circle',
      filter: ['all', ['==', '$type', 'Point'], ['==', 'meta', 'midpoint']],
      paint: {
        'circle-radius': 3,
        'circle-color': '#fbb03b',
      },
    },
    {
      id: 'gl-draw-polygon-stroke-inactive',
      type: 'line',
      filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'Polygon'], ['!=', 'mode', 'static']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#3bb2d0',
        'line-width': 2,
      },
    },
    {
      id: 'gl-draw-polygon-stroke-active',
      type: 'line',
      filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'Polygon']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#fbb03b',
        'line-width': 2,
      },
    },
    {
      id: 'gl-draw-line-inactive',
      type: 'line',
      filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'LineString'], ['!=', 'mode', 'static']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#3bb2d0',
        'line-width': 2,
      },
    },
    {
      id: 'gl-draw-line-active',
      type: 'line',
      filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'LineString']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#fbb03b',
        'line-width': 2,
      },
    },
    {
      id: 'gl-draw-polygon-and-line-vertex-stroke-inactive',
      type: 'circle',
      filter: ['all', ['==', 'meta', 'vertex'], ['==', '$type', 'Point'], ['!=', 'mode', 'static']],
      paint: {
        'circle-radius': 5,
        'circle-color': '#fff',
      },
    },
    {
      id: 'gl-draw-polygon-and-line-vertex-inactive',
      type: 'circle',
      filter: ['all', ['==', 'meta', 'vertex'], ['==', '$type', 'Point'], ['!=', 'mode', 'static']],
      paint: {
        'circle-radius': 3,
        'circle-color': '#fbb03b',
      },
    },
    {
      id: 'gl-draw-point-point-stroke-inactive',
      type: 'circle',
      filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'Point'], ['==', 'meta', 'feature'], ['!=', 'mode', 'static']],
      paint: {
        'circle-radius': 5,
        'circle-color': '#fff',
      },
    },
    {
      id: 'gl-draw-point-inactive',
      type: 'circle',
      filter: ['all', ['==', 'active', 'false'], ['==', '$type', 'Point'], ['==', 'meta', 'feature'], ['!=', 'mode', 'static']],
      paint: {
        'circle-radius': 3,
        'circle-color': '#3bb2d0',
      },
    },
    {
      id: 'gl-draw-point-stroke-active',
      type: 'circle',
      filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'Point'], ['!=', 'meta', 'midpoint']],
      paint: {
        'circle-radius': 7,
        'circle-color': '#fff',
      },
    },
    {
      id: 'gl-draw-point-active',
      type: 'circle',
      filter: ['all', ['==', 'active', 'true'], ['==', '$type', 'Point'], ['!=', 'meta', 'midpoint']],
      paint: {
        'circle-radius': 5,
        'circle-color': '#fbb03b',
      },
    },
    {
      id: 'gl-draw-polygon-fill-static',
      type: 'fill',
      filter: ['all', ['==', 'mode', 'static'], ['==', '$type', 'Polygon']],
      paint: {
        'fill-color': '#404040',
        'fill-outline-color': '#404040',
        'fill-opacity': 0.1,
      },
    },
    {
      id: 'gl-draw-polygon-stroke-static',
      type: 'line',
      filter: ['all', ['==', 'mode', 'static'], ['==', '$type', 'Polygon']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#404040',
        'line-width': 2,
      },
    },
    {
      id: 'gl-draw-line-static',
      type: 'line',
      filter: ['all', ['==', 'mode', 'static'], ['==', '$type', 'LineString']],
      layout: {
        'line-cap': 'round',
        'line-join': 'round',
      },
      paint: {
        'line-color': '#404040',
        'line-width': 2,
      },
    },
    {
      id: 'gl-draw-point-static',
      type: 'circle',
      filter: ['all', ['==', 'mode', 'static'], ['==', '$type', 'Point']],
      paint: {
        'circle-radius': 5,
        'circle-color': '#404040',
      },
    },
  ], []);

  // Initialize MapboxDraw
  const draw = useMemo(() => new MapboxDraw({
    displayControlsDefault: false,
    controls: {
      polygon: true,
      line_string: true,
      trash: true,
    },
    userProperties: true,
    styles: [...drawTheme, {
      id: 'gl-draw-title',
      type: 'symbol',
      filter: ['all'],
      layout: {
        'text-field': '{user_name}',
        'text-font': ['Open Sans Regular'],
        'text-size': 12,
      },
      paint: {
        'text-halo-color': 'white',
        'text-halo-width': 1,
      },
    }],
  }), [drawTheme]);

  // Utility functions
  const geofenceToFeature = (geofence: any) => {
    let geometry;
    const area = typeof geofence.area === 'string' ? geofence.area : '';

    if (area.startsWith('CIRCLE')) {
      const [_, lon, lat, radius] = area.match(/CIRCLE \((\d+\.?\d*) (\d+\.?\d*) (\d+\.?\d*)\)/);
      // Create a simple polygon approximation for circle
      const points = 32;
      const coordinates = [];
      for (let i = 0; i <= points; i++) {
        const angle = (i * 360) / points;
        const radian = (angle * Math.PI) / 180;
        coordinates.push([
          parseFloat(lon) + (parseFloat(radius) / 111320) * Math.cos(radian),
          parseFloat(lat) + (parseFloat(radius) / 111320) * Math.sin(radian)
        ]);
      }
      geometry = {
        type: 'Polygon',
        coordinates: [coordinates]
      };
    } else if (area.startsWith('POLYGON')) {
      const matches = area.match(/POLYGON \(\((.*?)\)\)/);
      if (matches) {
        const coordinates = matches[1].split(', ').map((coord: string) =>
          coord.split(' ').map(parseFloat)
        );
        geometry = {
          type: 'Polygon',
          coordinates: [coordinates]
        };
      }
    } else if (geofence.area?.startsWith('LINESTRING')) {
      const matches = geofence.area.match(/LINESTRING \((.*?)\)/);
      if (matches) {
        const coordinates = matches[1].split(', ').map((coord: string) =>
          coord.split(' ').map(parseFloat)
        );
        geometry = {
          type: 'LineString',
          coordinates
        };
      }
    }

    return {
      type: 'Feature',
      id: geofence.id,
      geometry,
      properties: {
        user_name: geofence.name
      }
    };
  };

  const geometryToArea = (geometry: any) => {
    if (geometry.type === 'Polygon') {
      const coordinates = geometry.coordinates[0];
      return `POLYGON ((${coordinates.map((coord: number[]) => coord.join(' ')).join(', ')}))`;
    } else if (geometry.type === 'LineString') {
      const coordinates = geometry.coordinates;
      return `LINESTRING (${coordinates.map((coord: number[]) => coord.join(' ')).join(', ')})`;
    }
    return '';
  };

  // Load geofences on mount
  useEffect(() => {
    if (token) {
      fetchGeofences();
    }
  }, [fetchGeofences, token]);

  // Add draw control to map
  useEffect(() => {
    if (!map || !draw) return;

    try {
      map.addControl(draw, theme.direction === 'rtl' ? 'top-right' : 'top-left');
    } catch (error) {
      console.warn('Failed to add draw control:', error);
      return;
    }

    return () => {
      if (map && draw && map.removeControl) {
        try {
          // Check if the draw control is still attached to the map
          if (map.hasControl && map.hasControl(draw)) {
            map.removeControl(draw);
          } else if (!map.hasControl) {
            // Fallback for older versions without hasControl
            map.removeControl(draw);
          }
        } catch (error) {
          console.warn('Failed to remove draw control:', error);
        }
      }
    };
  }, [map, draw, theme.direction]);

  // Handle draw create event
  useEffect(() => {
    if (!map || !token) return;

    const handleCreate = async (event: any) => {
      const feature = event.features[0];
      const newItem = {
        name: 'New Geofence',
        area: geometryToArea(feature.geometry),
        type: feature.geometry.type === 'Polygon' ? 'polygon' : 'polyline'
      };

      try {
        const response = await fetch('http://localhost:8000/api/geofences', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(newItem),
        });

        if (!response.ok) {
          throw new Error(`Failed to create geofence: ${response.statusText}`);
        }

        const item = await response.json();
        draw.delete(feature.id);
        fetchGeofences();
        navigate(`/geofences/${item.id}`);
      } catch (error) {
        console.error('Failed to create geofence:', error);
      }
    };

    map.on('draw.create', handleCreate);
    return () => {
      if (map && map.off) {
        try {
          map.off('draw.create', handleCreate);
        } catch (error) {
          console.warn('Failed to remove draw.create listener:', error);
        }
      }
    };
  }, [map, draw, token, fetchGeofences, navigate]);

  // Handle draw delete event
  useEffect(() => {
    if (!map || !token) return;

    const handleDelete = async (event: any) => {
      const feature = event.features[0];
      try {
        await fetch(`http://localhost:8000/api/geofences/${feature.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        fetchGeofences();
      } catch (error) {
        console.error('Failed to delete geofence:', error);
      }
    };

    map.on('draw.delete', handleDelete);
    return () => {
      if (map && map.off) {
        try {
          map.off('draw.delete', handleDelete);
        } catch (error) {
          console.warn('Failed to remove draw.delete listener:', error);
        }
      }
    };
  }, [map, token, fetchGeofences]);

  // Handle draw update event
  useEffect(() => {
    if (!map || !token) return;

    const handleUpdate = async (event: any) => {
      const feature = event.features[0];
      const geofence = geofences.find((g: any) => g.id === feature.id);
      if (geofence) {
        const updatedGeofence = {
          ...geofence,
          area: geometryToArea(feature.geometry)
        };

        try {
          await fetch(`http://localhost:8000/api/geofences/${feature.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(updatedGeofence),
          });
          fetchGeofences();
        } catch (error) {
          console.error('Failed to update geofence:', error);
        }
      }
    };

    map.on('draw.update', handleUpdate);
    return () => {
      if (map && map.off) {
        try {
          map.off('draw.update', handleUpdate);
        } catch (error) {
          console.warn('Failed to remove draw.update listener:', error);
        }
      }
    };
  }, [map, token, geofences, fetchGeofences]);

  // Load geofences into draw
  useEffect(() => {
    if (!draw) return;

    draw.deleteAll();
    geofences.forEach((geofence: any) => {
      const feature = geofenceToFeature(geofence);
      if (feature.geometry) {
        draw.add(feature);
      }
    });
  }, [geofences, draw]);

  // Fit bounds to selected geofence
  useEffect(() => {
    if (!map || !selectedGeofenceId || !draw) return;

    const feature = draw.get(selectedGeofenceId.toString());
    if (feature && feature.geometry) {
      let { coordinates } = feature.geometry;
      if (Array.isArray(coordinates[0][0])) {
        [coordinates] = coordinates;
      }

      if (coordinates && coordinates.length > 0) {
        const bounds = coordinates.reduce(
          (bounds: maplibregl.LngLatBounds, coordinate: number[]) =>
            bounds.extend(coordinate),
          new maplibregl.LngLatBounds(coordinates[0], coordinates[0])
        );

        const canvas = map.getCanvas();
        map.fitBounds(bounds, {
          padding: Math.min(canvas.width, canvas.height) * 0.1
        });
      }
    }
  }, [selectedGeofenceId, map, draw]);

  return null;
};

export default MapGeofenceEdit;
