import React, { useState, useCallback, useMemo } from 'react';
import { Box } from '@mui/material';
import maplibregl from 'maplibre-gl';
import MapContainer from './MapContainer';
import DeviceMarkers from './DeviceMarkers';
import MapControls from './MapControls';
import DeviceInfoCard from './DeviceInfoCard';

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

interface MapViewProps {
  positions: Position[];
  devices: Device[];
  selectedDeviceId?: number;
  onDeviceSelect?: (deviceId: number) => void;
  style?: React.CSSProperties;
}

// Map style configurations
const MAP_STYLES = {
  streets: {
    version: 8,
    sources: {
      'osm-tiles': {
        type: 'raster',
        tiles: [
          'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
        ],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors'
      }
    },
    layers: [
      {
        id: 'osm-tiles',
        type: 'raster',
        source: 'osm-tiles',
        minzoom: 0,
        maxzoom: 19
      }
    ]
  },
  satellite: {
    version: 8,
    sources: {
      'satellite-tiles': {
        type: 'raster',
        tiles: [
          'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        ],
        tileSize: 256,
        attribution: '© Esri, Maxar, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community'
      }
    },
    layers: [
      {
        id: 'satellite-tiles',
        type: 'raster',
        source: 'satellite-tiles',
        minzoom: 0,
        maxzoom: 19
      }
    ]
  }
};

const MapView: React.FC<MapViewProps> = ({
  positions,
  devices,
  selectedDeviceId,
  onDeviceSelect,
  style = { width: '100%', height: '400px' }
}) => {
  const [map, setMap] = useState<maplibregl.Map | null>(null);
  const [mapStyle, setMapStyle] = useState<'streets' | 'satellite' | 'hybrid'>('streets');
  const [showTraffic, setShowTraffic] = useState(false);

  // Find selected device and its position (memoized to prevent re-renders)
  const selectedDevice = useMemo(() => 
    devices.find(d => d.id === selectedDeviceId), 
    [devices, selectedDeviceId]
  );
  const selectedPosition = useMemo(() => 
    positions.find(p => p.deviceId === selectedDeviceId), 
    [positions, selectedDeviceId]
  );

  const handleMapLoad = useCallback((mapInstance: maplibregl.Map) => {
    setMap(mapInstance);
    
    // Fit map to show all devices if we have positions
    if (positions.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      positions.forEach(position => {
        bounds.extend([position.longitude, position.latitude]);
      });
      
      // Only fit bounds if we have multiple positions or if bounds are reasonable
      if (positions.length > 1 || !bounds.isEmpty()) {
        mapInstance.fitBounds(bounds, {
          padding: 50,
          maxZoom: 15
        });
      }
    }
  }, [positions]);

  const handleMarkerClick = useCallback((deviceId: number) => {
    if (onDeviceSelect) {
      onDeviceSelect(deviceId);
    }
    
    // Fly to the selected device
    const position = positions.find(p => p.deviceId === deviceId);
    if (position && map) {
      map.flyTo({
        center: [position.longitude, position.latitude],
        zoom: Math.max(map.getZoom(), 15),
        duration: 1500
      });
    }
  }, [positions, map, onDeviceSelect]);

  const handleStyleChange = useCallback((newStyle: 'streets' | 'satellite' | 'hybrid') => {
    if (map && MAP_STYLES[newStyle as keyof typeof MAP_STYLES]) {
      map.setStyle(MAP_STYLES[newStyle as keyof typeof MAP_STYLES]);
      setMapStyle(newStyle);
    }
  }, [map]);

  const handleTrafficToggle = useCallback((show: boolean) => {
    setShowTraffic(show);
    // In a real implementation, you would add/remove traffic layers here
    console.log('Traffic toggle:', show);
  }, []);

  const handleCloseDeviceInfo = useCallback(() => {
    if (onDeviceSelect) {
      onDeviceSelect(0); // Deselect device
    }
  }, [onDeviceSelect]);

  return (
    <Box sx={{ position: 'relative', ...style }}>
      <MapContainer onMapLoad={handleMapLoad} style={style}>
        <DeviceMarkers
          positions={positions}
          devices={devices}
          onMarkerClick={handleMarkerClick}
          selectedDeviceId={selectedDeviceId}
        />
      </MapContainer>
      
      <MapControls
        map={map}
        mapReady={!!map}
        mapStyle={mapStyle}
        onStyleChange={handleStyleChange}
        showTraffic={showTraffic}
        onTrafficToggle={handleTrafficToggle}
      />

      {selectedDevice && (
        <DeviceInfoCard
          device={selectedDevice}
          position={selectedPosition}
          onClose={handleCloseDeviceInfo}
        />
      )}
    </Box>
  );
};

export default MapView;
