import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Slider,
  Toolbar,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  Stack,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  FastRewind as RewindIcon,
  FastForward as ForwardIcon,
  Tune as TuneIcon,
  Download as DownloadIcon,
  ArrowBack as BackIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';

import MapView from '../components/map/MapView';
import { usePositions } from '../hooks/usePositions';
import { useDevices } from '../hooks/useDevices';
import { API_ENDPOINTS, getAuthHeaders } from '../api/apiConfig';

interface ReplayPosition {
  id: number;
  device_id: number;
  server_time: string;
  device_time?: string;
  fix_time?: string;
  latitude: number;
  longitude: number;
  altitude?: number;
  speed?: number;
  course?: number;
  address?: string;
  accuracy?: number;
  valid: boolean;
  protocol: string;
  attributes?: Record<string, any>;
}

const Replay: React.FC = () => {
  const { devices, fetchDevices } = useDevices();
  const { fetchPositions } = usePositions();
  
  const [positions, setPositions] = useState<ReplayPosition[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | ''>('');
  const [fromDate, setFromDate] = useState<Dayjs | null>(dayjs().subtract(1, 'day'));
  const [toDate, setToDate] = useState<Dayjs | null>(dayjs());
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(true);
  const [showCard, setShowCard] = useState(false);
  
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const playbackSpeed = 500; // milliseconds between positions

  // Load devices on mount
  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  // Auto-play timer
  useEffect(() => {
    if (isPlaying && positions.length > 0) {
      timerRef.current = setInterval(() => {
        setCurrentIndex((prevIndex) => {
          if (prevIndex >= positions.length - 1) {
            setIsPlaying(false);
            return prevIndex;
          }
          return prevIndex + 1;
        });
      }, playbackSpeed);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isPlaying, positions.length, playbackSpeed]);

  // Stop playing when reaching the end
  useEffect(() => {
    if (currentIndex >= positions.length - 1 && isPlaying) {
      setIsPlaying(false);
    }
  }, [currentIndex, positions.length, isPlaying]);

  const handleLoadPositions = useCallback(async () => {
    if (!selectedDeviceId || !fromDate || !toDate) {
      setError('Please select a device and date range');
      return;
    }

    setLoading(true);
    setError(null);
    setCurrentIndex(0);
    setIsPlaying(false);

    try {
      const params = new URLSearchParams({
        device_id: selectedDeviceId.toString(),
        from_time: fromDate.toISOString(),
        to_time: toDate.toISOString(),
      });

      const response = await fetch(`${API_ENDPOINTS.POSITIONS}?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch positions: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.length === 0) {
        setError('No positions found for the selected device and date range');
        setPositions([]);
      } else {
        setPositions(data);
        setShowFilters(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch positions');
      console.error('Error fetching positions:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedDeviceId, fromDate, toDate]);

  const handlePlayPause = useCallback(() => {
    if (positions.length === 0) return;
    
    if (currentIndex >= positions.length - 1) {
      setCurrentIndex(0);
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying, currentIndex, positions.length]);

  const handleRewind = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  }, [currentIndex]);

  const handleForward = useCallback(() => {
    if (currentIndex < positions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  }, [currentIndex, positions.length]);

  const handleSliderChange = useCallback((event: Event, newValue: number | number[]) => {
    setCurrentIndex(newValue as number);
  }, []);

  const handleDownload = useCallback(() => {
    if (!selectedDeviceId || !fromDate || !toDate) return;
    
    const params = new URLSearchParams({
      device_id: selectedDeviceId.toString(),
      from_time: fromDate.toISOString(),
      to_time: toDate.toISOString(),
    });
    
    window.open(`${API_ENDPOINTS.POSITIONS}/kml?${params}`, '_blank');
  }, [selectedDeviceId, fromDate, toDate]);

  const currentPosition = positions[currentIndex];
  const selectedDevice = devices.find(d => d.id === selectedDeviceId);

  const formatTime = (timeString: string) => {
    return dayjs(timeString).format('HH:mm:ss');
  };

  const formatDate = (timeString: string) => {
    return dayjs(timeString).format('DD/MM/YYYY');
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Map View */}
        <Box sx={{ flex: 1, position: 'relative' }}>
          <MapView
            positions={currentPosition ? [currentPosition] : []}
            devices={selectedDevice ? [selectedDevice] : []}
            selectedDeviceId={selectedDeviceId || undefined}
            currentReplayPosition={currentPosition}
            isReplaying={true}
            showGeofences={true}
            style={{ width: '100%', height: '100%' }}
          />
        </Box>

        {/* Controls Panel */}
        <Paper 
          elevation={3} 
          sx={{ 
            position: 'absolute', 
            top: 16, 
            left: 16, 
            right: 16, 
            zIndex: 1000,
            maxWidth: 400,
            margin: '0 auto'
          }}
        >
          <Toolbar>
            <IconButton edge="start" onClick={() => window.history.back()}>
              <BackIcon />
            </IconButton>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Replay
            </Typography>
            {!showFilters && (
              <>
                <IconButton onClick={handleDownload} disabled={!selectedDeviceId}>
                  <DownloadIcon />
                </IconButton>
                <IconButton onClick={() => setShowFilters(true)}>
                  <TuneIcon />
                </IconButton>
              </>
            )}
          </Toolbar>

          <Box sx={{ p: 2 }}>
            {showFilters ? (
              // Filter Panel
              <Stack spacing={2}>
                <FormControl fullWidth>
                  <InputLabel>Device</InputLabel>
                  <Select
                    value={selectedDeviceId}
                    onChange={(e) => setSelectedDeviceId(e.target.value as number)}
                    label="Device"
                  >
                    {devices.map((device) => (
                      <MenuItem key={device.id} value={device.id}>
                        {device.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <DatePicker
                  label="From Date"
                  value={fromDate}
                  onChange={(newValue) => setFromDate(newValue)}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />

                <DatePicker
                  label="To Date"
                  value={toDate}
                  onChange={(newValue) => setToDate(newValue)}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />

                {error && <Alert severity="error">{error}</Alert>}

                <Button
                  variant="contained"
                  onClick={handleLoadPositions}
                  disabled={loading || !selectedDeviceId || !fromDate || !toDate}
                  startIcon={loading ? <CircularProgress size={20} /> : <ScheduleIcon />}
                  fullWidth
                >
                  {loading ? 'Loading...' : 'Load Positions'}
                </Button>
              </Stack>
            ) : (
              // Playback Controls
              <Stack spacing={2}>
                {selectedDevice && (
                  <Typography variant="subtitle1" align="center">
                    {selectedDevice.name}
                  </Typography>
                )}

                {positions.length > 0 && (
                  <>
                    <Box sx={{ px: 2 }}>
                      <Slider
                        value={currentIndex}
                        min={0}
                        max={positions.length - 1}
                        step={1}
                        marks={positions.map((_, index) => ({ value: index }))}
                        onChange={handleSliderChange}
                        disabled={isPlaying}
                        sx={{ width: '100%' }}
                      />
                    </Box>

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Chip 
                        label={`${currentIndex + 1}/${positions.length}`} 
                        size="small" 
                        color="primary" 
                      />
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton 
                          onClick={handleRewind} 
                          disabled={isPlaying || currentIndex <= 0}
                          size="small"
                        >
                          <RewindIcon />
                        </IconButton>
                        
                        <IconButton 
                          onClick={handlePlayPause} 
                          disabled={positions.length === 0}
                          color="primary"
                        >
                          {isPlaying ? <PauseIcon /> : <PlayIcon />}
                        </IconButton>
                        
                        <IconButton 
                          onClick={handleForward} 
                          disabled={isPlaying || currentIndex >= positions.length - 1}
                          size="small"
                        >
                          <ForwardIcon />
                        </IconButton>
                      </Box>

                      {currentPosition && (
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(currentPosition.server_time)}
                        </Typography>
                      )}
                    </Box>

                    {currentPosition && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(currentPosition.server_time)}
                        </Typography>
                        {currentPosition.speed !== undefined && (
                          <Typography variant="body2" color="text.secondary">
                            {Math.round(currentPosition.speed * 3.6)} km/h
                          </Typography>
                        )}
                      </Box>
                    )}
                  </>
                )}
              </Stack>
            )}
          </Box>
        </Paper>
      </Box>
    </LocalizationProvider>
  );
};

export default Replay;
