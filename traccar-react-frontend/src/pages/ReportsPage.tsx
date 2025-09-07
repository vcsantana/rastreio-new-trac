import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  TextField,
  Toolbar,
  CircularProgress,
  Alert,
  Chip,
  Stack,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  FastForward as FastForwardIcon,
  FastRewind as FastRewindIcon,
  ArrowBack as ArrowBackIcon,
  PlayCircle as PlayCircleIcon,
  Settings as SettingsIcon,
  FilterList as FilterListIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import MapView from '../components/map/MapView';
import { useAuth } from '../contexts/AuthContext';

interface Device {
  id: number;
  name: string;
  uniqueId: string;
  status: string;
  lastUpdate: string;
}

interface Position {
  id: number;
  device_id: number;
  server_time: string;
  device_time?: string;
  fix_time?: string;
  latitude: number;
  longitude: number;
  speed?: number;
  course?: number;
  address?: string;
  altitude?: number;
  accuracy?: number;
  valid: boolean;
  protocol: string;
  attributes?: Record<string, any>;
}

const ReportsPage: React.FC = () => {
  console.log('🚀 ReportsPage component started');
  const navigate = useNavigate();
  const { token } = useAuth();
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Debug token
  useEffect(() => {
    console.log('🔑 ReportsPage token:', token ? 'Token exists' : 'No token');
  }, [token]);

  // State for devices and positions
  const [devices, setDevices] = useState<Device[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // State for filters
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | ''>('');
  
  // Debug selectedDeviceId changes
  useEffect(() => {
    console.log('🔍 selectedDeviceId changed:', selectedDeviceId);
  }, [selectedDeviceId]);
  const [period, setPeriod] = useState('today');
  const [customFrom, setCustomFrom] = useState('');
  const [customTo, setCustomTo] = useState('');

  // State for replay
  const [replayIndex, setReplayIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [expanded, setExpanded] = useState(true);

  // Initialize date inputs
  useEffect(() => {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    
    setCustomFrom(oneHourAgo.toISOString().slice(0, 16));
    setCustomTo(now.toISOString().slice(0, 16));
  }, []);

  // Fetch devices
  const fetchDevices = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch('http://localhost:8000/api/devices', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch devices: ${response.statusText}`);
      }

      const devicesData = await response.json();
      setDevices(devicesData);
      console.log('📱 Devices loaded:', devicesData.length);
    } catch (err) {
      console.error('❌ Error fetching devices:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch devices');
    }
  }, [token]);

  // Fetch positions for selected device and period
  const fetchPositions = useCallback(async (deviceId: number, from: string, to: string) => {
    console.log('🔍 fetchPositions called with:', { deviceId, from, to, token: !!token });
    if (!token) {
      console.log('❌ No token available');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const query = new URLSearchParams({
        from_time: new Date(from).toISOString(),
        to_time: new Date(to).toISOString(),
        limit: '5000',
      });

      const url = `http://localhost:8000/api/positions/device/${deviceId}/history?${query.toString()}`;
      console.log('📡 Fetching from URL:', url);

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Failed to fetch positions: ${response.statusText}`);
      }

      const positionsData = await response.json();
      console.log('📍 Positions data received:', positionsData.length, 'positions');
      setPositions(positionsData);
      setReplayIndex(0);
      setIsPlaying(false);
      // Automatically switch to replay controls when positions are loaded
      if (positionsData.length > 0) {
        setExpanded(false);
      }
      console.log('✅ Positions loaded successfully:', positionsData.length);
    } catch (err) {
      console.error('❌ Error fetching positions:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch positions');
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Load devices on mount
  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  // Replay timer effect with better cleanup
  useEffect(() => {
    if (isPlaying && positions && positions.length > 0) {
      timerRef.current = setInterval(() => {
        setReplayIndex((prevIndex) => {
          const nextIndex = prevIndex + 1;
          if (nextIndex >= positions.length) {
            setIsPlaying(false);
            return prevIndex;
          }
          return nextIndex;
        });
      }, 1000); // 1 second interval
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isPlaying, positions?.length]);

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, []);

  // Get date range based on period
  const getDateRange = () => {
    const now = new Date();
    let from: Date;
    let to: Date;

    switch (period) {
      case 'today':
        from = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        to = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
        break;
      case 'yesterday':
        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        from = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
        to = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 23, 59, 59);
        break;
      case 'thisWeek':
        const startOfWeek = new Date(now);
        startOfWeek.setDate(now.getDate() - now.getDay());
        from = new Date(startOfWeek.getFullYear(), startOfWeek.getMonth(), startOfWeek.getDate());
        to = new Date(now);
        break;
      case 'lastHour':
        from = new Date(now.getTime() - 60 * 60 * 1000);
        to = now;
        break;
      case 'custom':
        from = new Date(customFrom);
        to = new Date(customTo);
        break;
      default:
        from = new Date(now.getTime() - 60 * 60 * 1000);
        to = now;
    }

    return {
      from: from.toISOString().slice(0, 16),
      to: to.toISOString().slice(0, 16),
    };
  };

  // Handle show report
  const handleShowReport = () => {
    console.log('🔍 handleShowReport called - selectedDeviceId:', selectedDeviceId, 'type:', typeof selectedDeviceId);
    if (!selectedDeviceId) {
      console.log('❌ No device selected');
      setError('Please select a device');
      return;
    }

    const { from, to } = getDateRange();
    console.log('📅 Date range:', { from, to });
    console.log('🚀 Calling fetchPositions...');
    fetchPositions(selectedDeviceId, from, to);
  };

  // Handle replay controls
  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleStepForward = () => {
    if (positions && replayIndex < positions.length - 1) {
      setReplayIndex(replayIndex + 1);
    }
  };

  const handleStepBackward = () => {
    if (replayIndex > 0) {
      setReplayIndex(replayIndex - 1);
    }
  };

  const handleSliderChange = (_: Event, value: number | number[]) => {
    setReplayIndex(value as number);
  };

  // Function to clear current report and go back to filters
  const handleClearReport = () => {
    setPositions([]);
    setReplayIndex(0);
    setIsPlaying(false);
    setExpanded(true);
    setError(null);
  };

  // Get current position for replay
  const currentPosition = positions[replayIndex];
  const selectedDevice = devices.find(d => d.id === selectedDeviceId);

  // Prepare data for map - convert positions to compatible format and include replay logic
  const mapPositions = useMemo(() => {
    if (!positions || positions.length === 0) return [];
    
    // For replay, show positions up to current replay index
    const positionsToShow = positions.slice(0, replayIndex + 1);
    
    return positionsToShow.map(position => ({
      ...position,
      deviceId: position.device_id, // Add deviceId for compatibility
    }));
  }, [positions, replayIndex]);
  
  const mapDevices = devices || [];
  
  // Current position for replay (the position at current replay index)
  const currentReplayPosition = useMemo(() => {
    if (!positions || positions.length === 0 || replayIndex < 0) return null;
    const pos = positions[replayIndex];
    return pos ? {
      ...pos,
      deviceId: pos.device_id,
    } : null;
  }, [positions, replayIndex]);
  
  // Debug map data
  console.log('🗺️ ReportsPage map data:', {
    mapPositions: mapPositions.length,
    mapDevices: mapDevices.length,
    selectedDeviceId,
    replayIndex,
    currentReplayPosition,
    totalPositions: positions?.length || 0,
    devices: devices?.length || 0,
    expanded,
    showingReplayControls: !expanded && positions && positions.length > 0
  });

  console.log('🚀 ReportsPage rendering...');
  
  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={3} square>
        <Toolbar>
          <IconButton 
            edge="start" 
            sx={{ mr: 2 }} 
            onClick={() => {
              // If we have positions loaded and we're in replay mode, go back to filters
              if (positions && positions.length > 0 && !expanded) {
                setExpanded(true);
                setIsPlaying(false); // Stop any ongoing replay
              } else {
                // Otherwise, navigate back to previous page (dashboard)
                navigate(-1);
              }
            }}
            title={
              positions && positions.length > 0 && !expanded 
                ? 'Back to Filters' 
                : 'Back to Dashboard'
            }
          >
            {positions && positions.length > 0 && !expanded ? <FilterListIcon /> : <ArrowBackIcon />}
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Route Reports & Replay
          </Typography>
          {positions && positions.length > 0 && (
            <>
              <IconButton 
                onClick={() => setExpanded(!expanded)}
                title={expanded ? 'Switch to Replay Mode' : 'Switch to Filter Mode'}
              >
                {expanded ? <PlayCircleIcon /> : <SettingsIcon />}
              </IconButton>
            </>
          )}
        </Toolbar>
      </Paper>

      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <Paper 
          elevation={3} 
          square 
          sx={{ 
            width: 350, 
            display: 'flex', 
            flexDirection: 'column',
            overflow: 'auto'
          }}
        >
          {expanded ? (
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Report Filters
              </Typography>

              {/* Device Selection */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Device</InputLabel>
                <Select
                  value={selectedDeviceId}
                  onChange={(e) => {
                    console.log('🔍 Device selection changed:', e.target.value);
                    setSelectedDeviceId(e.target.value as number);
                  }}
                  label="Device"
                >
                  {devices.map((device) => (
                    <MenuItem key={device.id} value={device.id}>
                      {device.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Period Selection */}
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Period</InputLabel>
                <Select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  label="Period"
                >
                  <MenuItem value="lastHour">Last Hour</MenuItem>
                  <MenuItem value="today">Today</MenuItem>
                  <MenuItem value="yesterday">Yesterday</MenuItem>
                  <MenuItem value="thisWeek">This Week</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>

              {/* Custom Date Range */}
              {period === 'custom' && (
                <>
                  <TextField
                    label="From"
                    type="datetime-local"
                    value={customFrom}
                    onChange={(e) => setCustomFrom(e.target.value)}
                    fullWidth
                    sx={{ mb: 2 }}
                    InputLabelProps={{ shrink: true }}
                  />
                  <TextField
                    label="To"
                    type="datetime-local"
                    value={customTo}
                    onChange={(e) => setCustomTo(e.target.value)}
                    fullWidth
                    sx={{ mb: 2 }}
                    InputLabelProps={{ shrink: true }}
                  />
                </>
              )}

              {/* Show Report Button */}
              <Button
                variant="contained"
                fullWidth
                onClick={handleShowReport}
                disabled={loading || !selectedDeviceId}
                sx={{ mb: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Show Report'}
              </Button>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
            </Box>
          ) : (
            /* Replay Controls */
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom align="center">
                {selectedDevice?.name || 'No Device Selected'}
              </Typography>
              
              {/* Debug info */}
              <Typography variant="caption" display="block" align="center" sx={{ mb: 1, color: 'text.secondary' }}>
                Debug: {positions?.length || 0} positions, expanded: {expanded.toString()}
              </Typography>

              {(() => {
                console.log('🎮 Checking replay controls render:', { 
                  hasPositions: !!positions, 
                  positionsLength: positions?.length || 0,
                  expanded 
                });
                return null;
              })()}

              {/* New Report Button */}
              <Button
                variant="outlined"
                fullWidth
                onClick={handleClearReport}
                sx={{ mb: 2 }}
                size="small"
              >
                New Report
              </Button>
              
              {positions && positions.length > 0 ? (
                <>
                  {/* Progress Slider */}
                  <Slider
                    value={replayIndex}
                    min={0}
                    max={positions ? positions.length - 1 : 0}
                    step={1}
                    onChange={handleSliderChange}
                    sx={{ mb: 2 }}
                    disabled={isPlaying}
                  />

                  {/* Position Info */}
                  <Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
                    <Chip 
                      label={`${replayIndex + 1}/${positions ? positions.length : 0}`} 
                      size="small" 
                    />
                    <Chip 
                      label={currentPosition ? new Date(currentPosition.server_time).toLocaleString() : 'No data'} 
                      size="small" 
                    />
                  </Stack>

                  {/* Replay Controls */}
                  <Stack direction="row" justifyContent="center" spacing={1}>
                    <IconButton 
                      onClick={handleStepBackward} 
                      disabled={isPlaying || replayIndex <= 0}
                    >
                      <FastRewindIcon />
                    </IconButton>
                    <IconButton 
                      onClick={handlePlayPause} 
                      disabled={positions ? replayIndex >= positions.length - 1 : true}
                    >
                      {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
                    </IconButton>
                    <IconButton 
                      onClick={handleStepForward} 
                      disabled={isPlaying || (positions ? replayIndex >= positions.length - 1 : true)}
                    >
                      <FastForwardIcon />
                    </IconButton>
                  </Stack>

                  {/* Speed Info */}
                  {currentPosition && (
                    <Box sx={{ mt: 2, textAlign: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Speed: {(currentPosition.speed || 0).toFixed(1)} km/h
                      </Typography>
                      {currentPosition.address && (
                        <Typography variant="body2" color="text.secondary">
                          {currentPosition.address}
                        </Typography>
                      )}
                    </Box>
                  )}
                </>
              ) : (
                <Typography variant="body2" align="center" color="text.secondary">
                  No positions available for replay
                </Typography>
              )}
            </Box>
          )}
        </Paper>

        {/* Map */}
        <Box sx={{ flex: 1, position: 'relative' }}>
          <MapView
            devices={mapDevices}
            positions={mapPositions}
            selectedDeviceId={selectedDeviceId || undefined}
            currentReplayPosition={currentReplayPosition}
            isReplaying={positions && positions.length > 0}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default ReportsPage;
