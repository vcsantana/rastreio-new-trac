import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';

interface Position {
  id: number;
  deviceId?: number;
  device_id?: number;
  latitude: number;
  longitude: number;
  course?: number;
  speed?: number;
  fixTime?: string;
  serverTime?: string;
  deviceTime?: string;
  server_time?: string;
  device_time?: string;
  fix_time?: string;
  altitude?: number;
  valid?: boolean;
  address?: string;
  accuracy?: number;
  attributes?: Record<string, any>;
}

interface RoutePathProps {
  map: maplibregl.Map | null;
  positions: Position[];
  color?: string;
  width?: number;
  opacity?: number;
  showSpeedColors?: boolean;
}

const RoutePath: React.FC<RoutePathProps> = ({
  map,
  positions,
  color = '#3b82f6',
  width = 3,
  opacity = 0.8,
  showSpeedColors = true
}) => {
  const sourceId = useRef(`route-path-${Math.random().toString(36).substr(2, 9)}`);
  const layerId = useRef(`${sourceId.current}-line`);

  // Function to get speed-based color
  const getSpeedColor = (speed: number, minSpeed: number, maxSpeed: number): string => {
    if (maxSpeed === minSpeed) return color;
    
    const normalizedSpeed = (speed - minSpeed) / (maxSpeed - minSpeed);
    
    // Color gradient from blue (slow) to red (fast)
    if (normalizedSpeed < 0.33) return '#3b82f6'; // Blue
    if (normalizedSpeed < 0.66) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  useEffect(() => {
    if (!map || positions.length < 2) return;

    const source = sourceId.current;
    const layer = layerId.current;

    // Add source if it doesn't exist
    if (!map.getSource(source)) {
      map.addSource(source, {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: []
        }
      });
    }

    // Add layer if it doesn't exist
    if (!map.getLayer(layer)) {
      map.addLayer({
        id: layer,
        type: 'line',
        source: source,
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': showSpeedColors ? ['get', 'color'] : color,
          'line-width': width,
          'line-opacity': opacity
        }
      });
    }

    // Calculate speed range for color coding
    const speeds = positions.map(p => p.speed || 0);
    const minSpeed = Math.min(...speeds);
    const maxSpeed = Math.max(...speeds);

    // Create line segments with speed-based colors
    const features = [];
    for (let i = 0; i < positions.length - 1; i++) {
      const currentPos = positions[i];
      const nextPos = positions[i + 1];
      
      features.push({
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [
            [currentPos.longitude, currentPos.latitude],
            [nextPos.longitude, nextPos.latitude]
          ]
        },
        properties: {
          color: showSpeedColors 
            ? getSpeedColor(nextPos.speed || 0, minSpeed, maxSpeed)
            : color,
          width: width,
          opacity: opacity
        }
      });
    }

    // Update source data
    const sourceInstance = map.getSource(source) as maplibregl.GeoJSONSource;
    if (sourceInstance) {
      sourceInstance.setData({
        type: 'FeatureCollection',
        features
      });
    }

    // Cleanup function with safety checks
    return () => {
      try {
        if (map && map.getLayer && map.removeLayer) {
          if (map.getLayer(layer)) {
            map.removeLayer(layer);
          }
        }
        if (map && map.getSource && map.removeSource) {
          if (map.getSource(source)) {
            map.removeSource(source);
          }
        }
      } catch (error) {
        // Silently handle cleanup errors when map is being destroyed
        console.warn('RoutePath cleanup warning:', error);
      }
    };
  }, [map, positions, color, width, opacity, showSpeedColors]);

  return null;
};

export default RoutePath;
