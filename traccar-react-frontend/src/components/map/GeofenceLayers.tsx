/**
 * Geofence Layers Component
 * Renders geofences on the map using MapLibre GL
 */

import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import { Geofence } from '../../types/geofences';

interface GeofenceLayersProps {
  map: maplibregl.Map | null;
  geofences: Geofence[];
  selectedGeofenceId?: number;
  onGeofenceClick?: (geofence: Geofence) => void;
  showGeofences?: boolean;
}

const GeofenceLayers: React.FC<GeofenceLayersProps> = ({
  map,
  geofences,
  selectedGeofenceId,
  onGeofenceClick,
  showGeofences = true
}) => {
  const geofenceLayersRef = useRef<Set<string>>(new Set());

  // Add geofence layers to map
  useEffect(() => {
    if (!map || !showGeofences) return;

    const addGeofenceLayers = () => {
      geofences.forEach((geofence) => {
        const layerId = `geofence-${geofence.id}`;
        const sourceId = `geofence-source-${geofence.id}`;

        // Remove existing layer if it exists
        if (map.getLayer(layerId)) {
          map.removeLayer(layerId);
        }
        if (map.getSource(sourceId)) {
          map.removeSource(sourceId);
        }

        try {
          // Parse geometry
          const geometry = JSON.parse(geofence.geometry);
          
          // Add source
          map.addSource(sourceId, {
            type: 'geojson',
            data: {
              type: 'Feature',
              properties: {
                id: geofence.id,
                name: geofence.name,
                type: geofence.type,
                disabled: geofence.disabled
              },
              geometry: geometry
            }
          });

          // Determine colors based on status and selection
          const isSelected = selectedGeofenceId === geofence.id;
          const isDisabled = geofence.disabled;
          
          let fillColor = '#4caf50'; // Default green
          let strokeColor = '#2e7d32'; // Darker green
          let fillOpacity = 0.2;
          let strokeOpacity = 0.8;

          if (isDisabled) {
            fillColor = '#f44336'; // Red for disabled
            strokeColor = '#d32f2f';
            fillOpacity = 0.1;
            strokeOpacity = 0.6;
          } else if (isSelected) {
            fillColor = '#2196f3'; // Blue for selected
            strokeColor = '#1976d2';
            fillOpacity = 0.3;
            strokeOpacity = 1.0;
          }

          // Add layer based on geometry type
          if (geometry.type === 'Polygon') {
            // Fill layer
            map.addLayer({
              id: layerId,
              type: 'fill',
              source: sourceId,
              paint: {
                'fill-color': fillColor,
                'fill-opacity': fillOpacity
              }
            });

            // Stroke layer
            map.addLayer({
              id: `${layerId}-stroke`,
              type: 'line',
              source: sourceId,
              paint: {
                'line-color': strokeColor,
                'line-width': isSelected ? 3 : 2,
                'line-opacity': strokeOpacity
              }
            });
          } else if (geometry.type === 'Circle') {
            // For circles, we need to create a polygon approximation
            const [lon, lat, radius] = geometry.coordinates;
            const points = 64; // Number of points to approximate circle
            const coordinates = [];
            
            for (let i = 0; i < points; i++) {
              const angle = (i * 360) / points;
              const radian = (angle * Math.PI) / 180;
              const x = lon + (radius / 111320) * Math.cos(radian); // Rough conversion to degrees
              const y = lat + (radius / 111320) * Math.sin(radian);
              coordinates.push([x, y]);
            }
            coordinates.push(coordinates[0]); // Close the polygon

            // Add circle as polygon
            map.addSource(sourceId, {
              type: 'geojson',
              data: {
                type: 'Feature',
                properties: {
                  id: geofence.id,
                  name: geofence.name,
                  type: geofence.type,
                  disabled: geofence.disabled
                },
                geometry: {
                  type: 'Polygon',
                  coordinates: [coordinates]
                }
              }
            });

            // Fill layer
            map.addLayer({
              id: layerId,
              type: 'fill',
              source: sourceId,
              paint: {
                'fill-color': fillColor,
                'fill-opacity': fillOpacity
              }
            });

            // Stroke layer
            map.addLayer({
              id: `${layerId}-stroke`,
              type: 'line',
              source: sourceId,
              paint: {
                'line-color': strokeColor,
                'line-width': isSelected ? 3 : 2,
                'line-opacity': strokeOpacity
              }
            });
          } else if (geometry.type === 'LineString') {
            // Line layer for polylines
            map.addLayer({
              id: layerId,
              type: 'line',
              source: sourceId,
              paint: {
                'line-color': strokeColor,
                'line-width': isSelected ? 4 : 3,
                'line-opacity': strokeOpacity
              }
            });
          }

          // Add click handler
          map.on('click', layerId, (e) => {
            if (onGeofenceClick) {
              onGeofenceClick(geofence);
            }
          });

          // Change cursor on hover
          map.on('mouseenter', layerId, () => {
            map.getCanvas().style.cursor = 'pointer';
          });

          map.on('mouseleave', layerId, () => {
            map.getCanvas().style.cursor = '';
          });

          geofenceLayersRef.current.add(layerId);
        } catch (error) {
          console.error(`Error adding geofence layer for ${geofence.name}:`, error);
        }
      });
    };

    // Wait for map to be ready
    if (map.isStyleLoaded()) {
      addGeofenceLayers();
    } else {
      map.on('styledata', () => {
        if (map.isStyleLoaded()) {
          addGeofenceLayers();
        }
      });
    }

    // Cleanup function
    return () => {
      geofenceLayersRef.current.forEach((layerId) => {
        if (map.getLayer(layerId)) {
          map.removeLayer(layerId);
        }
        if (map.getLayer(`${layerId}-stroke`)) {
          map.removeLayer(`${layerId}-stroke`);
        }
        const sourceId = layerId.replace('geofence-', 'geofence-source-');
        if (map.getSource(sourceId)) {
          map.removeSource(sourceId);
        }
      });
      geofenceLayersRef.current.clear();
    };
  }, [map, geofences, selectedGeofenceId, onGeofenceClick, showGeofences]);

  // Update layer styles when selection changes
  useEffect(() => {
    if (!map || !showGeofences) return;

    geofences.forEach((geofence) => {
      const layerId = `geofence-${geofence.id}`;
      const strokeLayerId = `${layerId}-stroke`;

      if (map.getLayer(layerId)) {
        const isSelected = selectedGeofenceId === geofence.id;
        const isDisabled = geofence.disabled;

        let fillColor = '#4caf50';
        let strokeColor = '#2e7d32';
        let fillOpacity = 0.2;
        let strokeOpacity = 0.8;
        let lineWidth = 2;

        if (isDisabled) {
          fillColor = '#f44336';
          strokeColor = '#d32f2f';
          fillOpacity = 0.1;
          strokeOpacity = 0.6;
        } else if (isSelected) {
          fillColor = '#2196f3';
          strokeColor = '#1976d2';
          fillOpacity = 0.3;
          strokeOpacity = 1.0;
          lineWidth = 3;
        }

        // Update fill layer
        if (map.getLayer(layerId)) {
          map.setPaintProperty(layerId, 'fill-color', fillColor);
          map.setPaintProperty(layerId, 'fill-opacity', fillOpacity);
        }

        // Update stroke layer
        if (map.getLayer(strokeLayerId)) {
          map.setPaintProperty(strokeLayerId, 'line-color', strokeColor);
          map.setPaintProperty(strokeLayerId, 'line-width', lineWidth);
          map.setPaintProperty(strokeLayerId, 'line-opacity', strokeOpacity);
        }
      }
    });
  }, [map, geofences, selectedGeofenceId, showGeofences]);

  return null; // This component doesn't render anything visible
};

export default GeofenceLayers;
