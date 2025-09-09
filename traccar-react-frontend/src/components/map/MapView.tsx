import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Box } from '@mui/material';
import maplibregl from 'maplibre-gl';
import MapContainer from './MapContainer';
import DeviceMarkers from './DeviceMarkers';
import MapControls from './MapControls';
import DeviceInfoCard from './DeviceInfoCard';
import RoutePath from './RoutePath';
import RouteControls from './RouteControls';
import ReplayMarker from './ReplayMarker';
import GeofenceLayers from './GeofenceLayers';
import EventMarkers from './EventMarkers';
import { useDeviceHistory } from '../../hooks/useDeviceHistory';
import { useGeofences } from '../../hooks/useGeofences';
import { useEvents } from '../../hooks/useEvents';
import { Geofence } from '../../types/geofences';
import { Event } from '../../types/events';

interface Position {
  id: number;
  device_id?: number;
  unknown_device_id?: number;
  deviceId?: number; // For backward compatibility
  server_time: string;
  device_time?: string;
  fix_time?: string;
  latitude: number;
  longitude: number;
  course?: number;
  speed?: number;
  address?: string;
  altitude?: number;
  accuracy?: number;
  valid: boolean;
  protocol: string;
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
  currentReplayPosition?: Position | null;
  isReplaying?: boolean;
  showGeofences?: boolean;
  selectedGeofenceId?: number;
  onGeofenceSelect?: (geofence: Geofence) => void;
  showEvents?: boolean;
  selectedEventId?: number;
  onEventSelect?: (event: Event) => void;
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
  style = { width: '100%', height: '400px' },
  currentReplayPosition,
  isReplaying = false,
  showGeofences = true,
  selectedGeofenceId,
  onGeofenceSelect,
  showEvents = false,
  selectedEventId,
  onEventSelect,
}) => {
  console.log('🗺️ MapView render - positions:', positions?.length || 0, 'devices:', devices?.length || 0, 'selectedDeviceId:', selectedDeviceId, 'isReplaying:', isReplaying);
  console.log('🗺️ MapView props:', { positions, devices, selectedDeviceId, currentReplayPosition, isReplaying });
  const [map, setMap] = useState<maplibregl.Map | null>(null);
  const [mapStyle, setMapStyle] = useState<'streets' | 'satellite' | 'hybrid'>('streets');
  const [showTraffic, setShowTraffic] = useState(false);
  
  // Fetch geofences for map display
  const { geofences, fetchGeofences } = useGeofences();
  
  // Fetch events for map display
  const { events, eventTypeInfo, fetchEvents } = useEvents();
  
  // Route controls state
  const [showRoutes, setShowRoutes] = useState(false);
  const [showSpeedColors, setShowSpeedColors] = useState(true);
  const [routeColor, setRouteColor] = useState('#3b82f6');
  const [routeWidth, setRouteWidth] = useState(3);
  const [routeOpacity, setRouteOpacity] = useState(0.8);
  const [fromTime, setFromTime] = useState<Date | null>(null);
  const [toTime, setToTime] = useState<Date | null>(null);
  
  // Fetch geofences when component mounts
  useEffect(() => {
    if (showGeofences) {
      fetchGeofences();
    }
  }, [showGeofences, fetchGeofences]);

  // Fetch events when component mounts
  useEffect(() => {
    if (showEvents) {
      fetchEvents({ size: 100 }); // Fetch recent events for map display
    }
  }, [showEvents, fetchEvents]);

  // Auto-enable routes during replay
  useEffect(() => {
    if (isReplaying && selectedDeviceId && positions && positions.length > 1) {
      setShowRoutes(true);
    }
  }, [isReplaying, selectedDeviceId, positions]);
  
  // Move camera to current replay position
  useEffect(() => {
    if (isReplaying && currentReplayPosition && map) {
      console.log('🎬 Moving camera to replay position:', currentReplayPosition);
      map.flyTo({
        center: [currentReplayPosition.longitude, currentReplayPosition.latitude],
        zoom: Math.max(map.getZoom(), 16),
        duration: 800,
        essential: true
      });
    }
  }, [isReplaying, currentReplayPosition, map]);

  // Find selected device and its position (memoized to prevent re-renders)
  const selectedDevice = useMemo(() => 
    devices?.find(d => d.id === selectedDeviceId), 
    [devices, selectedDeviceId]
  );
  
  // For replay mode, use currentReplayPosition, otherwise use latest position
  const selectedPosition = useMemo(() => {
    if (isReplaying && currentReplayPosition && (currentReplayPosition.device_id === selectedDeviceId || currentReplayPosition.unknown_device_id === selectedDeviceId)) {
      return currentReplayPosition;
    }
    return positions?.find(p => (p.deviceId || p.device_id || p.unknown_device_id) === selectedDeviceId);
  }, [positions, selectedDeviceId, isReplaying, currentReplayPosition]);

  // Fetch device history for route tracking (skip if we're in replay mode and already have positions)
  const { positions: historyPositions, refetch: refetchHistory } = useDeviceHistory({
    deviceId: selectedDeviceId,
    fromTime: fromTime || undefined,
    toTime: toTime || undefined,
    enabled: showRoutes && !!selectedDeviceId && !isReplaying
  });
  
  // Use replay positions if available, otherwise use history positions
  const routePositions = useMemo(() => {
    if (isReplaying && positions && positions.length > 0) {
      // Convert positions to the format expected by RoutePath
      return positions.map(pos => ({
        ...pos,
        deviceId: pos.device_id || pos.deviceId || pos.unknown_device_id || 0,
      }));
    }
    return historyPositions;
  }, [isReplaying, positions, historyPositions]);

  const handleMapLoad = useCallback((mapInstance: maplibregl.Map) => {
    setMap(mapInstance);
    
    // Fit map to show all devices if we have positions
    if (positions && positions.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      positions.forEach(position => {
        bounds.extend([position.longitude, position.latitude]);
      });
      
      // Only fit bounds if we have multiple positions or if bounds are reasonable
      if (positions && positions.length > 1 || !bounds.isEmpty()) {
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
    const position = positions.find(p => (p.deviceId || p.device_id || p.unknown_device_id) === deviceId);
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
      map.setStyle(MAP_STYLES[newStyle as keyof typeof MAP_STYLES] as maplibregl.StyleSpecification);
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

  const handleEventClick = useCallback((event: Event) => {
    if (onEventSelect) {
      onEventSelect(event);
    }
    
    // Fly to the event location
    if (event.position_data && map) {
      map.flyTo({
        center: [event.position_data.longitude, event.position_data.latitude],
        zoom: Math.max(map.getZoom(), 15),
        duration: 1500
      });
    }
  }, [onEventSelect, map]);

  // Route control handlers
  const handleApplyFilters = useCallback(() => {
    refetchHistory();
  }, [refetchHistory]);

  const handleClearFilters = useCallback(() => {
    setFromTime(null);
    setToTime(null);
    refetchHistory();
  }, [refetchHistory]);

  return (
    <Box sx={{ position: 'relative', ...style }}>
      <MapContainer onMapLoad={handleMapLoad} style={style}>
        <DeviceMarkers
          positions={positions}
          devices={devices}
          onMarkerClick={handleMarkerClick}
          selectedDeviceId={selectedDeviceId}
        />
        
        {/* Route path for selected device */}
        {showRoutes && selectedDeviceId && routePositions && routePositions.length > 1 && (
          <RoutePath
            map={map}
            positions={routePositions}
            color={routeColor}
            width={routeWidth}
            opacity={routeOpacity}
            showSpeedColors={showSpeedColors}
          />
        )}
        
        {/* Replay marker for current position */}
        {isReplaying && currentReplayPosition && (
          <ReplayMarker
            map={map}
            position={currentReplayPosition}
            deviceName={selectedDevice?.name}
          />
        )}
        
        {/* Geofence layers */}
        {showGeofences && (
          <GeofenceLayers
            map={map}
            geofences={geofences}
            selectedGeofenceId={selectedGeofenceId}
            onGeofenceClick={onGeofenceSelect}
            showGeofences={showGeofences}
          />
        )}
        
        {/* Event markers */}
        {showEvents && (
          <EventMarkers
            events={events}
            eventTypeInfo={eventTypeInfo}
            onEventSelect={handleEventClick}
            showPopup={true}
            clusterEvents={true}
            map={map}
          />
        )}
      </MapContainer>
      
      <MapControls
        map={map || undefined}
        mapReady={!!map}
        mapStyle={mapStyle}
        onStyleChange={handleStyleChange}
        showTraffic={showTraffic}
        onTrafficToggle={handleTrafficToggle}
      />

      {/* Hide route controls during replay mode */}
      {!isReplaying && (
        <RouteControls
          showRoutes={showRoutes}
          onShowRoutesChange={setShowRoutes}
          showSpeedColors={showSpeedColors}
          onShowSpeedColorsChange={setShowSpeedColors}
          routeColor={routeColor}
          onRouteColorChange={setRouteColor}
          routeWidth={routeWidth}
          onRouteWidthChange={setRouteWidth}
          routeOpacity={routeOpacity}
          onRouteOpacityChange={setRouteOpacity}
          fromTime={fromTime}
          onFromTimeChange={setFromTime}
          toTime={toTime}
          onToTimeChange={setToTime}
          onApplyFilters={handleApplyFilters}
          onClearFilters={handleClearFilters}
        />
      )}

      {selectedDevice && selectedPosition && (
        <DeviceInfoCard
          device={selectedDevice}
          position={{
            ...selectedPosition,
            deviceId: selectedPosition.deviceId || selectedPosition.device_id || selectedPosition.unknown_device_id || 0
          }}
          onClose={handleCloseDeviceInfo}
        />
      )}
    </Box>
  );
};

export default MapView;
