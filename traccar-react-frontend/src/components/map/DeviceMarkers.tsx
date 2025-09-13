import { useEffect, useId, useMemo } from 'react';
import maplibregl from 'maplibre-gl';

interface Position {
  id: number;
  deviceId?: number;
  device_id?: number;
  unknown_device_id?: number;
  latitude: number;
  longitude: number;
  course?: number;
  speed?: number;
  fixTime?: string;
  server_time?: string;
  device_time?: string;
  fix_time?: string;
  attributes?: Record<string, any>;
}

interface Device {
  id: number;
  name: string;
  status: string;
  category?: string;
  lastUpdate?: string;
}

interface DeviceMarkersProps {
  map?: maplibregl.Map;
  mapReady?: boolean;
  positions: Position[];
  devices: Device[];
  onMarkerClick?: (deviceId: number, position: Position) => void;
  selectedDeviceId?: number;
  showLabels?: boolean;
}

const DeviceMarkers: React.FC<DeviceMarkersProps> = ({
  map,
  mapReady,
  positions,
  devices,
  onMarkerClick,
  selectedDeviceId,
  showLabels = true
}) => {
  console.log('📍 DeviceMarkers render - map:', !!map, 'mapReady:', mapReady, 'positions:', positions?.length || 0, 'devices:', devices?.length || 0);
  const sourceId = useId();
  const layerId = useId();
  const selectedLayerId = useId();

  // Create device lookup map (memoized)
  const deviceMap = useMemo(() => {
    if (!devices) return {};
    const map = devices.reduce((acc, device) => {
      acc[device.id] = device;
      return acc;
    }, {} as Record<number, Device>);
    console.log('🔍 DeviceMap created:', map);
    return map;
  }, [devices]);

  useEffect(() => {
    if (!map || !mapReady) return;

    // Add source for device positions
    map.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: []
      }
    });

    // Add layer for regular devices
    map.addLayer({
      id: layerId,
      type: 'circle',
      source: sourceId,
      filter: ['!=', 'selected', true],
      paint: {
        'circle-radius': [
          'case',
          ['==', ['get', 'status'], 'online'], 8,
          ['==', ['get', 'status'], 'offline'], 6,
          5
        ],
        'circle-color': [
          'case',
          ['==', ['get', 'status'], 'online'], '#4CAF50',
          ['==', ['get', 'status'], 'offline'], '#f44336',
          '#9E9E9E'
        ],
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 2
      }
    });

    // Add layer for selected device
    map.addLayer({
      id: selectedLayerId,
      type: 'circle',
      source: sourceId,
      filter: ['==', 'selected', true],
      paint: {
        'circle-radius': 12,
        'circle-color': '#2196F3',
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 3
      }
    });

    // Add labels for device names (if enabled)
    if (showLabels) {
      map.addLayer({
        id: `${layerId}-labels`,
        type: 'symbol',
        source: sourceId,
        layout: {
          'text-field': ['get', 'name'],
          'text-size': 12,
          'text-anchor': 'top',
          'text-offset': [0, 1.5],
          'text-allow-overlap': false,
          'text-ignore-placement': false
        },
        paint: {
          'text-color': '#333333',
          'text-halo-color': '#ffffff',
          'text-halo-width': 2,
          'text-halo-blur': 1
        }
      });
    }

    // Add click handlers
    const handleClick = (e: maplibregl.MapMouseEvent) => {
      try {
        const layers = [layerId, selectedLayerId];
        // Only add labels layer if it exists in the map
        if (showLabels && map && map.getLayer && map.getLayer(`${layerId}-labels`)) {
          layers.push(`${layerId}-labels`);
        }
        
        const features = map.queryRenderedFeatures(e.point, { layers });
        
        if (features.length > 0) {
          const feature = features[0];
          const deviceId = feature.properties?.deviceId;
          const position = positions?.find(p => (p.deviceId || p.device_id || p.unknown_device_id) === deviceId);
          
          if (deviceId && position && onMarkerClick) {
            onMarkerClick(deviceId, position);
          }
        }
      } catch (error) {
        console.warn('DeviceMarkers click handler error:', error);
      }
    };

    const handleMouseEnter = () => {
      if (map && map.getCanvas) {
        map.getCanvas().style.cursor = 'pointer';
      }
    };

    const handleMouseLeave = () => {
      if (map && map.getCanvas) {
        map.getCanvas().style.cursor = '';
      }
    };

    if (map) {
      map.on('click', layerId, handleClick);
      map.on('click', selectedLayerId, handleClick);
      map.on('mouseenter', layerId, handleMouseEnter);
      map.on('mouseenter', selectedLayerId, handleMouseEnter);
      map.on('mouseleave', layerId, handleMouseLeave);
      map.on('mouseleave', selectedLayerId, handleMouseLeave);
      
      // Only add event listeners if labels layer exists
      if (showLabels && map.getLayer(`${layerId}-labels`)) {
        map.on('click', `${layerId}-labels`, handleClick);
        map.on('mouseenter', `${layerId}-labels`, handleMouseEnter);
        map.on('mouseleave', `${layerId}-labels`, handleMouseLeave);
      }
    }

    // Cleanup
    return () => {
      // Check if map still exists before trying to access its methods
      if (!map || !map.getLayer) return;
      
      try {
        // Remove layers if they exist
        if (showLabels && map && map.getLayer && map.removeLayer) {
          try {
            if (map.getLayer(`${layerId}-labels`)) {
              map.removeLayer(`${layerId}-labels`);
            }
          } catch (e) {
            // Layer might not exist, continue
          }
        }
        if (map && map.getLayer && map.removeLayer) {
          try {
            if (map.getLayer(selectedLayerId)) {
              map.removeLayer(selectedLayerId);
            }
          } catch (e) {
            // Layer might not exist, continue
          }
        }
        if (map && map.getLayer && map.removeLayer) {
          try {
            if (map.getLayer(layerId)) {
              map.removeLayer(layerId);
            }
          } catch (e) {
            // Layer might not exist, continue
          }
        }
        if (map && map.getSource && map.removeSource) {
          try {
            if (map.getSource(sourceId)) {
              map.removeSource(sourceId);
            }
          } catch (e) {
            // Source might not exist, continue
          }
        }
        
        // Remove event listeners
        if (map) {
          map.off('click', layerId, handleClick);
          map.off('click', selectedLayerId, handleClick);
          map.off('mouseenter', layerId, handleMouseEnter);
          map.off('mouseenter', selectedLayerId, handleMouseEnter);
          map.off('mouseleave', layerId, handleMouseLeave);
          map.off('mouseleave', selectedLayerId, handleMouseLeave);
          
          // Only remove label event listeners if the layer exists
          if (showLabels && map.getLayer && map.off) {
            try {
              if (map.getLayer(`${layerId}-labels`)) {
                map.off('click', `${layerId}-labels`, handleClick);
                map.off('mouseenter', `${layerId}-labels`, handleMouseEnter);
                map.off('mouseleave', `${layerId}-labels`, handleMouseLeave);
              }
            } catch (e) {
              // Layer might not exist, continue
            }
          }
        }
      } catch (error) {
        // Silently handle cleanup errors when map is being destroyed
        console.warn('Error during DeviceMarkers cleanup:', error);
      }
    };
  }, [map, mapReady, sourceId, layerId, selectedLayerId, onMarkerClick, showLabels]);

  // Update markers when positions or devices change
  useEffect(() => {
    if (!map || !mapReady || !map.getSource) return;

    try {
      const source = map.getSource(sourceId) as maplibregl.GeoJSONSource;
      if (!source) return;

    console.log('🔍 Filtering positions:', positions);
    console.log('🔍 Available devices in map:', deviceMap);
    
    const features = positions
      .filter(position => {
        const deviceId = position.deviceId || position.device_id || position.unknown_device_id;
        const hasDevice = deviceId && deviceMap[deviceId];
        const hasValidCoordinates = position.latitude >= -90 && position.latitude <= 90 && 
                                   position.longitude >= -180 && position.longitude <= 180;
        
        if (!hasDevice) {
          console.log('🔍 Position filtered out - no device found:', {
            positionId: position.id,
            deviceId: position.deviceId,
            device_id: position.device_id,
            unknown_device_id: position.unknown_device_id,
            availableDevices: Object.keys(deviceMap)
          });
        } else if (!hasValidCoordinates) {
          console.log('🔍 Position filtered out - invalid coordinates:', {
            positionId: position.id,
            latitude: position.latitude,
            longitude: position.longitude
          });
        } else {
          console.log('✅ Position included:', {
            positionId: position.id,
            deviceId: deviceId,
            device: deviceMap[deviceId],
            coordinates: [position.latitude, position.longitude]
          });
        }
        return hasDevice && hasValidCoordinates;
      })
      .map(position => {
        const deviceId = position.deviceId || position.device_id || position.unknown_device_id;
        const device = deviceMap[deviceId!];
        return {
          type: 'Feature' as const,
          geometry: {
            type: 'Point' as const,
            coordinates: [position.longitude, position.latitude]
          },
          properties: {
            deviceId: device.id,
            name: device.name,
            status: device.status,
            selected: device.id === selectedDeviceId,
            speed: position.speed || 0,
            course: position.course || 0,
            fixTime: position.fixTime || position.server_time || position.fix_time
          }
        };
      });

      console.log('🗺️ Setting map features:', features);
      source.setData({
        type: 'FeatureCollection',
        features
      });
    } catch (error) {
      // Silently handle errors when map is being destroyed
      console.warn('Error updating DeviceMarkers data:', error);
    }
  }, [map, mapReady, positions, devices, deviceMap, selectedDeviceId, sourceId]);

  return null;
};

export default DeviceMarkers;
