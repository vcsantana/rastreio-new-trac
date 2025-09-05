import { useEffect, useId } from 'react';
import maplibregl from 'maplibre-gl';

interface Position {
  id: number;
  deviceId: number;
  latitude: number;
  longitude: number;
  course?: number;
  speed?: number;
  fixTime?: string;
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
}

const DeviceMarkers: React.FC<DeviceMarkersProps> = ({
  map,
  mapReady,
  positions,
  devices,
  onMarkerClick,
  selectedDeviceId
}) => {
  const sourceId = useId();
  const layerId = useId();
  const selectedLayerId = useId();

  // Create device lookup map
  const deviceMap = devices.reduce((acc, device) => {
    acc[device.id] = device;
    return acc;
  }, {} as Record<number, Device>);

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

    // Add labels
    map.addLayer({
      id: `${layerId}-labels`,
      type: 'symbol',
      source: sourceId,
      layout: {
        'text-field': '{name}',
        'text-font': ['Open Sans Regular', 'Arial Unicode MS Regular'],
        'text-size': 12,
        'text-anchor': 'top',
        'text-offset': [0, 1.5]
      },
      paint: {
        'text-color': '#333333',
        'text-halo-color': '#ffffff',
        'text-halo-width': 1
      }
    });

    // Add click handlers
    const handleClick = (e: maplibregl.MapMouseEvent) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: [layerId, selectedLayerId]
      });
      
      if (features.length > 0) {
        const feature = features[0];
        const deviceId = feature.properties?.deviceId;
        const position = positions.find(p => p.deviceId === deviceId);
        
        if (deviceId && position && onMarkerClick) {
          onMarkerClick(deviceId, position);
        }
      }
    };

    const handleMouseEnter = () => {
      map.getCanvas().style.cursor = 'pointer';
    };

    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = '';
    };

    map.on('click', layerId, handleClick);
    map.on('click', selectedLayerId, handleClick);
    map.on('mouseenter', layerId, handleMouseEnter);
    map.on('mouseenter', selectedLayerId, handleMouseEnter);
    map.on('mouseleave', layerId, handleMouseLeave);
    map.on('mouseleave', selectedLayerId, handleMouseLeave);

    // Cleanup
    return () => {
      if (map.getLayer(`${layerId}-labels`)) {
        map.removeLayer(`${layerId}-labels`);
      }
      if (map.getLayer(selectedLayerId)) {
        map.removeLayer(selectedLayerId);
      }
      if (map.getLayer(layerId)) {
        map.removeLayer(layerId);
      }
      if (map.getSource(sourceId)) {
        map.removeSource(sourceId);
      }
      
      map.off('click', layerId, handleClick);
      map.off('click', selectedLayerId, handleClick);
      map.off('mouseenter', layerId, handleMouseEnter);
      map.off('mouseenter', selectedLayerId, handleMouseEnter);
      map.off('mouseleave', layerId, handleMouseLeave);
      map.off('mouseleave', selectedLayerId, handleMouseLeave);
    };
  }, [map, mapReady, sourceId, layerId, selectedLayerId, onMarkerClick]);

  // Update markers when positions or devices change
  useEffect(() => {
    if (!map || !mapReady) return;

    const source = map.getSource(sourceId) as maplibregl.GeoJSONSource;
    if (!source) return;

    const features = positions
      .filter(position => deviceMap[position.deviceId])
      .map(position => {
        const device = deviceMap[position.deviceId];
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
            fixTime: position.fixTime
          }
        };
      });

    source.setData({
      type: 'FeatureCollection',
      features
    });
  }, [map, mapReady, positions, devices, deviceMap, selectedDeviceId, sourceId]);

  return null;
};

export default DeviceMarkers;
