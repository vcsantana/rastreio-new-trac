import React, { useRef, useEffect, useState, ReactNode } from 'react';
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

// Default map styles
const DEFAULT_STYLE = {
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

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Initialize the map
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: DEFAULT_STYLE,
      center: initialCenter,
      zoom: initialZoom,
      attributionControl: false
    });

    // Add controls
    map.current.addControl(
      new maplibregl.AttributionControl({ compact: true }),
      'bottom-right'
    );
    
    map.current.addControl(
      new maplibregl.NavigationControl(),
      'top-right'
    );

    // Handle map load
    map.current.on('load', () => {
      setMapReady(true);
      if (onMapLoad && map.current) {
        onMapLoad(map.current);
      }
    });

    // Cleanup function
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, [initialCenter, initialZoom, onMapLoad]);

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
    <Box sx={{ position: 'relative', ...style }}>
      <div
        ref={mapContainer}
        style={{ width: '100%', height: '100%' }}
      />
      {mapReady && childrenWithProps}
    </Box>
  );
};

export default MapContainer;
