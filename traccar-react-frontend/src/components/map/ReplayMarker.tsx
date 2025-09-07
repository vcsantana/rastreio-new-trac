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
  server_time?: string;
  attributes?: Record<string, any>;
}

interface ReplayMarkerProps {
  map: maplibregl.Map | null;
  position: Position | null;
  deviceName?: string;
}

const ReplayMarker: React.FC<ReplayMarkerProps> = ({
  map,
  position,
  deviceName = 'Device'
}) => {
  const sourceId = useRef(`replay-marker-${Math.random().toString(36).substr(2, 9)}`);
  const layerId = useRef(`${sourceId.current}-circle`);
  const pulseLayerId = useRef(`${sourceId.current}-pulse`);

  useEffect(() => {
    if (!map || !position) return;

    const source = sourceId.current;
    const layer = layerId.current;
    const pulseLayer = pulseLayerId.current;

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

    // Add main marker layer if it doesn't exist
    if (!map.getLayer(layer)) {
      map.addLayer({
        id: layer,
        type: 'circle',
        source: source,
        paint: {
          'circle-radius': 12,
          'circle-color': '#FF5722', // Orange-red for current position
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 3,
          'circle-opacity': 0.9
        }
      });
    }

    // Add pulsing animation layer if it doesn't exist
    if (!map.getLayer(pulseLayer)) {
      map.addLayer({
        id: pulseLayer,
        type: 'circle',
        source: source,
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 20,
            20, 40
          ],
          'circle-color': '#FF5722',
          'circle-opacity': [
            'interpolate',
            ['linear'],
            ['get', 'pulse'],
            0, 0.3,
            1, 0
          ],
          'circle-stroke-color': '#FF5722',
          'circle-stroke-width': 1,
          'circle-stroke-opacity': [
            'interpolate',
            ['linear'],
            ['get', 'pulse'],
            0, 0.5,
            1, 0
          ]
        }
      });
    }

    // Update marker position
    const sourceInstance = map.getSource(source) as maplibregl.GeoJSONSource;
    if (sourceInstance) {
      sourceInstance.setData({
        type: 'FeatureCollection',
        features: [{
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [position.longitude, position.latitude]
          },
          properties: {
            deviceName,
            speed: position.speed || 0,
            course: position.course || 0,
            time: position.server_time,
            pulse: 0 // For animation
          }
        }]
      });
    }

    // Animate the pulse effect with safety checks
    let pulseValue = 0;
    let isAnimating = true;
    
    const pulseAnimation = () => {
      // Safety check: stop animation if component is unmounted or map is destroyed
      if (!isAnimating || !map || !map.getSource) {
        return;
      }
      
      try {
        pulseValue = (pulseValue + 0.02) % 1;
        
        const sourceInstance = map.getSource(source) as maplibregl.GeoJSONSource;
        if (sourceInstance && sourceInstance.setData) {
          sourceInstance.setData({
            type: 'FeatureCollection',
            features: [{
              type: 'Feature',
              geometry: {
                type: 'Point',
                coordinates: [position.longitude, position.latitude]
              },
              properties: {
                deviceName,
                speed: position.speed || 0,
                course: position.course || 0,
                time: position.server_time,
                pulse: pulseValue
              }
            }]
          });
        }
        
        if (isAnimating) {
          requestAnimationFrame(pulseAnimation);
        }
      } catch (error) {
        // Stop animation on any error (map likely destroyed)
        console.warn('ReplayMarker animation stopped due to error:', error);
        isAnimating = false;
      }
    };
    
    const animationId = requestAnimationFrame(pulseAnimation);

    // Cleanup function with safety checks
    return () => {
      // Stop animation immediately
      isAnimating = false;
      cancelAnimationFrame(animationId);
      
      // Safely remove map layers and sources
      try {
        if (map && map.getLayer && map.removeLayer) {
          if (map.getLayer(pulseLayer)) {
            map.removeLayer(pulseLayer);
          }
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
        console.warn('ReplayMarker cleanup warning:', error);
      }
    };
  }, [map, position, deviceName]);

  return null;
};

export default ReplayMarker;
