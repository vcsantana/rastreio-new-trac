import React, { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const MapTest: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    console.log('🧪 Testing maplibre-gl initialization...');

    try {
      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: {
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
        },
        center: [0, 0],
        zoom: 2
      });

      map.current.on('load', () => {
        console.log('🧪 Map loaded successfully!');
        setError(null);
      });

      map.current.on('error', (e) => {
        console.error('🧪 Map error:', e);
        setError(`Map error: ${e.error?.message || 'Unknown error'}`);
      });

    } catch (err) {
      console.error('🧪 Failed to initialize map:', err);
      setError(`Initialization error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }

    return () => {
      if (map.current) {
        console.log('🧪 Cleaning up test map');
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  return (
    <Box sx={{ width: '100%', height: 400, border: '1px solid #ccc' }}>
      <div
        ref={mapContainer}
        style={{ width: '100%', height: '100%' }}
      />
      {error && (
        <Box sx={{
          position: 'absolute',
          top: 10,
          left: 10,
          backgroundColor: 'rgba(255, 0, 0, 0.8)',
          color: 'white',
          padding: '8px',
          borderRadius: '4px',
          zIndex: 1000
        }}>
          {error}
        </Box>
      )}
    </Box>
  );
};

export default MapTest;
