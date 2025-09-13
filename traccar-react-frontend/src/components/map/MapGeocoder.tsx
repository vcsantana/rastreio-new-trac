/**
 * Map Geocoder Component
 * Adds a geocoder control to the map for searching locations
 * Based on traccar-web MapGeocoder.js
 */

import React, { useState } from 'react';
import { useTheme } from '@mui/material/styles';
import {
  Box,
  TextField,
  Autocomplete,
  IconButton,
  Paper,
} from '@mui/material';
import { Search as SearchIcon, Close as CloseIcon } from '@mui/icons-material';
import maplibregl from 'maplibre-gl';

interface MapGeocoderProps {
  map?: maplibregl.Map | null;
}

interface GeocodeResult {
  place_name: string;
  center: [number, number];
  bbox?: [number, number, number, number];
}

const MapGeocoder: React.FC<MapGeocoderProps> = ({ map }) => {
  const theme = useTheme();
  const [searchValue, setSearchValue] = useState('');
  const [options, setOptions] = useState<GeocodeResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const searchGeocode = async (query: string) => {
    if (!query.trim()) {
      setOptions([]);
      return;
    }

    setLoading(true);
    try {
      const request = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5&addressdetails=1`;
      const response = await fetch(request);
      const results = await response.json();

      const formattedResults: GeocodeResult[] = results.map((result: any) => ({
        place_name: result.display_name,
        center: [parseFloat(result.lon), parseFloat(result.lat)],
        bbox: result.bbox ? [
          parseFloat(result.bbox[0]),
          parseFloat(result.bbox[1]),
          parseFloat(result.bbox[2]),
          parseFloat(result.bbox[3])
        ] : undefined,
      }));

      setOptions(formattedResults);
    } catch (error) {
      console.error('Geocoding error:', error);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchValue(value);
    searchGeocode(value);
  };

  const handleSelect = (result: GeocodeResult | null) => {
    if (!result || !map) return;

    const { center, bbox } = result;

    if (bbox) {
      // Fit to bounding box if available
      map.fitBounds([
        [bbox[0], bbox[1]],
        [bbox[2], bbox[3]]
      ], {
        padding: 50,
        maxZoom: 16
      });
    } else {
      // Otherwise, just center on the location
      map.flyTo({
        center,
        zoom: 16
      });
    }

    setOpen(false);
    setSearchValue(result.place_name);
  };

  const clearSearch = () => {
    setSearchValue('');
    setOptions([]);
    setOpen(false);
  };

  return (
    <Box
      sx={{
        position: 'absolute',
        top: theme.spacing(1),
        right: theme.spacing(1),
        left: theme.spacing(1),
        zIndex: 1000,
        maxWidth: 400,
      }}
    >
      <Autocomplete
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
        options={options}
        getOptionLabel={(option) => option.place_name}
        loading={loading}
        value={null}
        onChange={(_, value) => handleSelect(value)}
        inputValue={searchValue}
        onInputChange={(_, value) => handleSearch(value)}
        renderInput={(params) => (
          <TextField
            {...params}
            placeholder="Search places..."
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: 'background.paper',
                boxShadow: 2,
              }
            }}
            InputProps={{
              ...params.InputProps,
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              endAdornment: searchValue ? (
                <IconButton size="small" onClick={clearSearch}>
                  <CloseIcon />
                </IconButton>
              ) : null,
            }}
          />
        )}
        renderOption={(props, option) => (
          <Box component="li" {...props} key={option.place_name}>
            {option.place_name}
          </Box>
        )}
        PaperComponent={({ children, ...props }) => (
          <Paper elevation={8} sx={{ mt: 1 }} {...props}>
            {children}
          </Paper>
        )}
        noOptionsText="No places found"
        loadingText="Searching..."
      />
    </Box>
  );
};

export default MapGeocoder;
