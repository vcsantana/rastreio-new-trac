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
  Tab,
  Tabs,
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
  Description as DescriptionIcon,
  GetApp as GetAppIcon,
  Route as RouteIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import MapView from '../components/map/MapView';
import { useAuth } from '../contexts/AuthContext';
import { useReports } from '../hooks/useReports';

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

  // Reports hook
  const {
    reports,
    loading: reportsLoading,
    error: reportsError,
    createReport,
    fetchReports,
    getReportData,
    downloadReport,
  } = useReports();

  // Tab state
  const [activeTab, setActiveTab] = useState(0);

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

  // Report creation state
  const [reportName, setReportName] = useState('');
  const [reportDescription, setReportDescription] = useState('');
  const [reportType, setReportType] = useState<'route' | 'summary' | 'events' | 'stops' | 'trips'>('route');
  const [reportFormat, setReportFormat] = useState<'json' | 'csv' | 'pdf' | 'xlsx'>('json');

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
    fetchReports(); // Load existing reports
  }, [fetchDevices, fetchReports]);

  // Create report from current filters
  const handleCreateReport = async () => {
    if (!selectedDeviceId || !reportName.trim()) {
      setError('Please select a device and enter a report name');
      return;
    }

    try {
      const { from, to } = getDateRange();
      await createReport({
        name: reportName.trim(),
        description: reportDescription.trim() || undefined,
        report_type: reportType,
        format: reportFormat,
        period: period as any,
        from_date: period === 'custom' ? customFrom : undefined,
        to_date: period === 'custom' ? customTo : undefined,
        device_ids: [selectedDeviceId],
        include_attributes: true,
        include_addresses: true,
        include_events: true,
        include_geofences: true,
      });

      setReportName('');
      setReportDescription('');
      setActiveTab(0); // Switch to reports list tab
      await fetchReports(); // Refresh reports list
    } catch (err) {
      console.error('Failed to create report:', err);
      setError('Failed to create report');
    }
  };

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
            Reports & Route Replay
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RouteIcon />}
            onClick={() => navigate('/replay')}
            sx={{ mr: 1 }}
          >
            Replay
          </Button>
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

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="My Reports" icon={<DescriptionIcon />} iconPosition="start" />
          <Tab label="Route Replay" icon={<PlayCircleIcon />} iconPosition="start" />
          <Tab label="Create Report" icon={<GetAppIcon />} iconPosition="start" />
        </Tabs>
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
          {/* My Reports Tab */}
          {activeTab === 0 && (
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                My Reports
              </Typography>

              {reportsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                  <CircularProgress />
                </Box>
              ) : reports.length === 0 ? (
                <Typography variant="body2" color="text.secondary" align="center" sx={{ p: 2 }}>
                  No reports found. Create your first report using the "Create Report" tab.
                </Typography>
              ) : (
                <Stack spacing={2}>
                  {reports.map((report) => (
                    <Paper key={report.id} elevation={1} sx={{ p: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        {report.name}
                      </Typography>
                      {report.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {report.description}
                        </Typography>
                      )}
                      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                        <Chip
                          label={report.report_type}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                        <Chip
                          label={report.status}
                          size="small"
                          color={
                            report.status === 'completed' ? 'success' :
                            report.status === 'processing' ? 'warning' :
                            report.status === 'failed' ? 'error' : 'default'
                          }
                        />
                      </Stack>
                      <Typography variant="caption" color="text.secondary">
                        Created: {new Date(report.created_at).toLocaleString()}
                      </Typography>
                      {report.completed_at && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          Completed: {new Date(report.completed_at).toLocaleString()}
                        </Typography>
                      )}
                      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                        {report.status === 'completed' && (
                          <>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => getReportData(report.id)}
                              disabled={loading}
                            >
                              View Data
                            </Button>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => downloadReport(report.id)}
                              disabled={loading}
                            >
                              Download
                            </Button>
                          </>
                        )}
                      </Stack>
                    </Paper>
                  ))}
                </Stack>
              )}

              {reportsError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {reportsError}
                </Alert>
              )}
            </Box>
          )}

          {/* Route Replay Tab */}
          {activeTab === 1 && (
            <>
              {expanded ? (
                <Box sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Route Replay Filters
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

                  {/* Show Route Button */}
                  <Button
                    variant="contained"
                    fullWidth
                    onClick={handleShowReport}
                    disabled={loading || !selectedDeviceId}
                    sx={{ mb: 2 }}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Load Route for Replay'}
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
            </>
          )}

          {/* Create Report Tab */}
          {activeTab === 2 && (
            <Box sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Create New Report
              </Typography>

              <TextField
                label="Report Name"
                value={reportName}
                onChange={(e) => setReportName(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
                placeholder="Enter report name"
              />

              <TextField
                label="Description (Optional)"
                value={reportDescription}
                onChange={(e) => setReportDescription(e.target.value)}
                fullWidth
                multiline
                rows={2}
                sx={{ mb: 2 }}
                placeholder="Enter report description"
              />

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Report Type</InputLabel>
                <Select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value as any)}
                  label="Report Type"
                >
                  <MenuItem value="route">Route Report</MenuItem>
                  <MenuItem value="summary">Summary Report</MenuItem>
                  <MenuItem value="events">Events Report</MenuItem>
                  <MenuItem value="stops">Stops Report</MenuItem>
                  <MenuItem value="trips">Trips Report</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Format</InputLabel>
                <Select
                  value={reportFormat}
                  onChange={(e) => setReportFormat(e.target.value as any)}
                  label="Format"
                >
                  <MenuItem value="json">JSON</MenuItem>
                  <MenuItem value="csv">CSV</MenuItem>
                  <MenuItem value="pdf">PDF</MenuItem>
                  <MenuItem value="xlsx">Excel</MenuItem>
                </Select>
              </FormControl>

              {/* Use same device and period filters as replay */}
              <FormControl fullWidth sx={{ mb: 2 }}>
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

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Period</InputLabel>
                <Select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  label="Period"
                >
                  <MenuItem value="today">Today</MenuItem>
                  <MenuItem value="yesterday">Yesterday</MenuItem>
                  <MenuItem value="this_week">This Week</MenuItem>
                  <MenuItem value="last_week">Last Week</MenuItem>
                  <MenuItem value="this_month">This Month</MenuItem>
                  <MenuItem value="last_month">Last Month</MenuItem>
                  <MenuItem value="this_year">This Year</MenuItem>
                  <MenuItem value="last_year">Last Year</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>

              {/* Custom Date Range */}
              {period === 'custom' && (
                <>
                  <TextField
                    label="From Date"
                    type="datetime-local"
                    value={customFrom}
                    onChange={(e) => setCustomFrom(e.target.value)}
                    fullWidth
                    sx={{ mb: 2 }}
                    InputLabelProps={{ shrink: true }}
                  />
                  <TextField
                    label="To Date"
                    type="datetime-local"
                    value={customTo}
                    onChange={(e) => setCustomTo(e.target.value)}
                    fullWidth
                    sx={{ mb: 2 }}
                    InputLabelProps={{ shrink: true }}
                  />
                </>
              )}

              <Button
                variant="contained"
                fullWidth
                onClick={handleCreateReport}
                disabled={reportsLoading || !selectedDeviceId || !reportName.trim()}
                sx={{ mb: 2 }}
              >
                {reportsLoading ? <CircularProgress size={24} /> : 'Create Report'}
              </Button>

              {reportsError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {reportsError}
                </Alert>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Reports are processed in the background. You can check the status in the "My Reports" tab.
              </Typography>
            </Box>
          )}
        </Paper>

        {/* Map - Only show for Route Replay tab or when we have positions loaded */}
        <Box sx={{ flex: 1, position: 'relative' }}>
          {activeTab === 1 || (positions && positions.length > 0) ? (
            <MapView
              devices={mapDevices}
              positions={mapPositions}
              selectedDeviceId={selectedDeviceId || undefined}
              currentReplayPosition={currentReplayPosition}
              isReplaying={positions && positions.length > 0 && activeTab === 1}
            />
          ) : (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                bgcolor: 'grey.50'
              }}
            >
              <Typography variant="h6" color="text.secondary">
                {activeTab === 0 ? 'Select a report to view data' : 'Load a route in the Route Replay tab to see the map'}
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default ReportsPage;
