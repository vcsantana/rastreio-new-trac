import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  Chip,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControlLabel,
  Switch,
  Autocomplete,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  Search as SearchIcon,
  CalendarToday as CalendarIcon,
  DeviceHub as DeviceIcon,
  Category as CategoryIcon,
  Schedule as ScheduleIcon,
  Speed as SpeedIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import { EventFilters, EventTypeInfo } from '../../types/events';
import { Device } from '../../types';

interface EventFiltersProps {
  filters: EventFilters;
  eventTypes: string[];
  eventTypeInfo: Record<string, EventTypeInfo>;
  devices: Device[];
  onFiltersChange: (filters: EventFilters) => void;
  onClearFilters: () => void;
  loading?: boolean;
  compact?: boolean;
}

const EventFiltersComponent: React.FC<EventFiltersProps> = ({
  filters,
  eventTypes,
  eventTypeInfo,
  devices,
  onFiltersChange,
  onClearFilters,
  loading = false,
  compact = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [localFilters, setLocalFilters] = useState<EventFilters>(filters);
  const [expanded, setExpanded] = useState(!compact);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Handle filter changes
  const handleFilterChange = (key: keyof EventFilters, value: any) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
  };

  // Apply filters
  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
  };

  // Clear all filters
  const handleClearFilters = () => {
    const clearedFilters: EventFilters = {
      page: 1,
      size: 50,
    };
    setLocalFilters(clearedFilters);
    onClearFilters();
  };

  // Quick filter presets
  const quickFilters = [
    {
      label: 'Last 24h',
      filters: {
        ...localFilters,
        start_time: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
        end_time: new Date().toISOString().slice(0, 16),
      },
    },
    {
      label: 'Last 7 days',
      filters: {
        ...localFilters,
        start_time: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
        end_time: new Date().toISOString().slice(0, 16),
      },
    },
    {
      label: 'Alarms only',
      filters: {
        ...localFilters,
        event_type: 'alarm',
      },
    },
    {
      label: 'Overspeed only',
      filters: {
        ...localFilters,
        event_type: 'deviceOverspeed',
      },
    },
    {
      label: 'Geofence events',
      filters: {
        ...localFilters,
        event_type: 'geofenceEnter',
      },
    },
  ];

  // Get active filters count
  const getActiveFiltersCount = () => {
    let count = 0;
    if (localFilters.device_id) count++;
    if (localFilters.event_type) count++;
    if (localFilters.start_time) count++;
    if (localFilters.end_time) count++;
    return count;
  };

  const activeFiltersCount = getActiveFiltersCount();

  const filterContent = (
    <Box sx={{ p: 2 }}>
      {/* Quick Filters */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <SearchIcon fontSize="small" />
          Quick Filters
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {quickFilters.map((quickFilter, index) => (
            <Chip
              key={index}
              label={quickFilter.label}
              onClick={() => {
                setLocalFilters(quickFilter.filters);
                onFiltersChange(quickFilter.filters);
              }}
              variant="outlined"
              size="small"
            />
          ))}
        </Box>
      </Box>

      {/* Main Filters */}
      <Grid container spacing={2}>
        {/* Device Filter */}
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Device</InputLabel>
            <Select
              value={localFilters.device_id || ''}
              label="Device"
              onChange={(e) => handleFilterChange('device_id', e.target.value || undefined)}
            >
              <MenuItem value="">All Devices</MenuItem>
              {devices.map((device) => (
                <MenuItem key={device.id} value={device.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <DeviceIcon fontSize="small" />
                    {device.name}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Event Type Filter */}
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Event Type</InputLabel>
            <Select
              value={localFilters.event_type || ''}
              label="Event Type"
              onChange={(e) => handleFilterChange('event_type', e.target.value || undefined)}
            >
              <MenuItem value="">All Types</MenuItem>
              {eventTypes.map((type) => (
                <MenuItem key={type} value={type}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CategoryIcon fontSize="small" />
                    {eventTypeInfo[type]?.name || type}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Start Time Filter */}
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            size="small"
            label="Start Time"
            type="datetime-local"
            value={localFilters.start_time || ''}
            onChange={(e) => handleFilterChange('start_time', e.target.value || undefined)}
            InputLabelProps={{ shrink: true }}
            InputProps={{
              startAdornment: <CalendarIcon fontSize="small" sx={{ mr: 1, color: 'action.active' }} />,
            }}
          />
        </Grid>

        {/* End Time Filter */}
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            size="small"
            label="End Time"
            type="datetime-local"
            value={localFilters.end_time || ''}
            onChange={(e) => handleFilterChange('end_time', e.target.value || undefined)}
            InputLabelProps={{ shrink: true }}
            InputProps={{
              startAdornment: <CalendarIcon fontSize="small" sx={{ mr: 1, color: 'action.active' }} />,
            }}
          />
        </Grid>

        {/* Page Size Filter */}
        <Grid item xs={12} sm={6} md={3}>
          <FormControl fullWidth size="small">
            <InputLabel>Page Size</InputLabel>
            <Select
              value={localFilters.size || 50}
              label="Page Size"
              onChange={(e) => handleFilterChange('size', e.target.value)}
            >
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
              <MenuItem value={200}>200</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Filter Actions */}
      <Box sx={{ display: 'flex', gap: 1, mt: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          startIcon={<ClearIcon />}
          onClick={handleClearFilters}
          disabled={loading}
        >
          Clear All
        </Button>
        <Button
          variant="contained"
          startIcon={<FilterIcon />}
          onClick={handleApplyFilters}
          disabled={loading}
        >
          Apply Filters
        </Button>
      </Box>
    </Box>
  );

  if (compact) {
    return (
      <Paper sx={{ mb: 2 }}>
        <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              '& .MuiAccordionSummary-content': {
                alignItems: 'center',
                gap: 1,
              },
            }}
          >
            <FilterIcon />
            <Typography variant="subtitle1">Filters</Typography>
            {activeFiltersCount > 0 && (
              <Chip
                label={activeFiltersCount}
                size="small"
                color="primary"
                sx={{ ml: 1 }}
              />
            )}
          </AccordionSummary>
          <AccordionDetails sx={{ p: 0 }}>
            {filterContent}
          </AccordionDetails>
        </Accordion>
      </Paper>
    );
  }

  return (
    <Paper sx={{ mb: 2 }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <FilterIcon />
          <Typography variant="h6">Filters</Typography>
          {activeFiltersCount > 0 && (
            <Chip
              label={`${activeFiltersCount} active`}
              size="small"
              color="primary"
            />
          )}
        </Box>
      </Box>
      {filterContent}
    </Paper>
  );
};

export default EventFiltersComponent;
