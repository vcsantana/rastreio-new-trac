import React, { useRef, useEffect, useState, ReactNode, useMemo, useCallback } from 'react';
import { Box } from '@mui/material';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface MapContainerProps {
  children?: ReactNode;
  onMapLoad?: (map: maplibregl.Map) => void;
  initialCenter?: [number, number];
  initialZoom?: number;
  style?: React.CSSProperties;
}

// Default map styles - using a simple OSM style to avoid loading issues
const DEFAULT_STYLE = {
  version: 8,
  sources: {
    'osm': {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors'
    }
  },
  layers: [
    {
      id: 'osm',
      type: 'raster',
      source: 'osm',
      minzoom: 0,
      maxzoom: 19
    }
  ]
};

const MapContainer: React.FC<MapContainerProps> = ({
  children,
  onMapLoad,
  initialCenter = [0, 0],
  initialZoom = 2,
  style = { width: '100%', height: '100%' }
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapReady, setMapReady] = useState(false);

  // Memoize the map configuration to prevent unnecessary re-renders
  const mapConfig = useMemo(() => ({
    style: DEFAULT_STYLE,
    center: initialCenter,
    zoom: initialZoom,
    attributionControl: false
  }), [initialCenter, initialZoom]);

  // Memoize the onMapLoad callback
  const handleMapLoad = useCallback((mapInstance: maplibregl.Map) => {
    setMapReady(true);
    if (onMapLoad) {
      onMapLoad(mapInstance);
    }
  }, [onMapLoad]);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    console.log('🗺️ Initializing map...');

    try {
      // Initialize the map
      map.current = new maplibregl.Map({
        container: mapContainer.current,
        ...mapConfig
      });

      console.log('🗺️ Map instance created');

      // Add controls
      map.current.addControl(
        new maplibregl.AttributionControl({ compact: true }),
        'bottom-right'
      );

      // Handle map load
      map.current.on('load', () => {
        console.log('🗺️ Map loaded successfully');
        handleMapLoad(map.current!);
      });

      map.current.on('error', (e) => {
        console.error('🗺️ Map error:', e);
      });

    } catch (error) {
      console.error('🗺️ Failed to initialize map:', error);
    }

    // Cleanup function
    return () => {
      if (map.current) {
        console.log('🗺️ Cleaning up map');
        map.current.remove();
        map.current = null;
        setMapReady(false);
      }
    };
  }, []); // Empty dependency array to prevent re-initialization

  // Provide map instance to children
  const childrenWithProps = React.Children.map(children, (child) => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, { 
        map: map.current, 
        mapReady 
      } as any);
    }
    return child;
  });

  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%', minHeight: 400, ...style }}>
      <div
        ref={mapContainer}
        style={{ width: '100%', height: '100%', minHeight: 400 }}
      />
      {mapReady && childrenWithProps}
    </Box>
  );
};

export default MapContainer;
