import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  useTheme,
  Alert,
  CircularProgress,
  Button,
  useMediaQuery,
  Typography,
} from '@mui/material';
import MapView from '../components/map/MapView';
import MainToolbar from '../components/main/MainToolbar';
import DeviceList from '../components/main/DeviceList';
import StatusCard from '../components/main/StatusCard';
import EventsDrawer from '../components/main/EventsDrawer';
import BottomMenu from '../components/common/BottomMenu';
import { useGeofences } from '../hooks/useGeofences';
import { useFilter } from '../hooks/useFilter';
import { Geofence } from '../types/geofences';

// Define interfaces locally for now
interface Device {
  id: number;
  name: string;
  unique_id: string;
  status: 'online' | 'offline' | 'unknown';
  category: string;
  last_update: string;
  group_id: number | null;
  disabled: boolean;
  protocol?: string;
  attributes?: Record<string, any>;
}

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const desktop = useMediaQuery(theme.breakpoints.up('md'));

  const [selectedDeviceId, setSelectedDeviceId] = useState<number | undefined>();
  const [selectedGeofenceId, setSelectedGeofenceId] = useState<number | undefined>();
  const [positions, setPositions] = useState<any[]>([]);
  const [filteredDevices, setFilteredDevices] = useState<Device[]>([]);
  const [filteredPositions, setFilteredPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  
  // Filter states
  const [keyword, setKeyword] = useState('');
  const [filter, setFilter] = useState({
    statuses: [] as string[],
    groups: [] as number[],
  });
  const [filterSort, setFilterSort] = useState('');
  const [filterMap, setFilterMap] = useState(false);
  
  // UI states
  const [devicesOpen, setDevicesOpen] = useState(desktop);
  const [eventsOpen, setEventsOpen] = useState(false);
  
  // Geofences hook
  const { fetchGeofences } = useGeofences();

  // Filter hook
  useFilter({
    keyword,
    filter,
    filterSort,
    filterMap,
    positions,
    setFilteredDevices,
    setFilteredPositions,
  });

  // Callbacks
  const onDeviceSelect = useCallback((deviceId: number) => {
    setSelectedDeviceId(deviceId);
  }, []);

  // Update devicesOpen when desktop changes
  useEffect(() => {
    setDevicesOpen(desktop);
  }, [desktop]);

  // Login function
  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'admin@traccar.com',
          password: 'admin123'
        }),
      });

      if (!response.ok) {
        throw new Error(`Login failed: ${response.statusText}`);
      }

      const data = await response.json();
      setToken(data.access_token);
      localStorage.setItem('access_token', data.access_token);
      
      // Fetch data after login
      await fetchData(data.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  // Fetch data function
  const fetchData = async (authToken: string) => {
    try {
      console.log('🔍 Starting fetchData with token:', authToken ? 'Token exists' : 'No token');
      
      const headers = {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      };

      console.log('📡 Fetching devices...');
      // Fetch devices
      const devicesResponse = await fetch('http://localhost:8000/api/devices', { headers });
      console.log('📡 Devices response status:', devicesResponse.status);
      if (!devicesResponse.ok) {
        throw new Error(`Failed to fetch devices: ${devicesResponse.statusText}`);
      }
      const devicesData = await devicesResponse.json();
      console.log('📱 Devices data:', devicesData.length, 'devices');

      console.log('📡 Fetching unknown devices...');
      // Fetch unknown devices
      const unknownDevicesResponse = await fetch('http://localhost:8000/api/unknown-devices', { headers });
      console.log('📡 Unknown devices response status:', unknownDevicesResponse.status);
      if (unknownDevicesResponse.ok) {
        const unknownDevicesData = await unknownDevicesResponse.json();
        console.log('📱 Unknown devices data:', unknownDevicesData.length, 'unknown devices');
        
        // Convert unknown devices to device format for compatibility
        const convertedUnknownDevices = unknownDevicesData.map((unknownDevice: any) => ({
          id: unknownDevice.id,
          name: `Unknown ${unknownDevice.unique_id}`,
          unique_id: unknownDevice.unique_id,
          protocol: unknownDevice.protocol,
          status: 'online', // Assume unknown devices are online if they have recent data
          category: 'unknown',
          last_update: unknownDevice.last_seen,
          is_unknown: true
        }));
        
        console.log('🔍 Converted unknown devices:', convertedUnknownDevices);
        
        // Combine registered and unknown devices
        devicesData.push(...convertedUnknownDevices);
        console.log('📱 Total devices (registered + unknown):', devicesData.length);
        console.log('📱 All devices:', devicesData);
      } else {
        console.log('⚠️ Failed to fetch unknown devices, continuing with registered devices only');
      }

      console.log('📍 Fetching positions...');
      // Fetch positions
      const positionsResponse = await fetch('http://localhost:8000/api/positions/latest', { headers });
      console.log('📍 Positions response status:', positionsResponse.status);
      if (!positionsResponse.ok) {
        throw new Error(`Failed to fetch positions: ${positionsResponse.statusText}`);
      }
      const positionsData = await positionsResponse.json();
      console.log('📍 Positions data:', positionsData.length, 'positions');
      console.log('📍 All positions:', positionsData);

      // Transform positions to match the expected format
      const transformedPositions = positionsData.map((position: any) => ({
        ...position,
        deviceId: position.device_id || position.unknown_device_id,
        server_time: position.server_time || position.device_time,
        valid: position.valid !== false,
        protocol: position.protocol || 'unknown',
      }));

      // Devices are stored in filteredDevices
      setPositions(transformedPositions);
      setError(null);
      setLoading(false);
      console.log('✅ Data fetch completed successfully - loading set to false');
      
      // Fetch geofences
      fetchGeofences();
    } catch (err) {
      console.error('❌ Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      setLoading(false);
    }
  };

  // Check if already logged in
  useEffect(() => {
    console.log('🚀 DashboardTest useEffect running...');
    const storedToken = localStorage.getItem('access_token');
    console.log('🔑 Stored token:', storedToken ? 'Token exists' : 'No token');
    
    if (storedToken) {
      console.log('✅ Token found, setting token and fetching data');
      setToken(storedToken);
      setLoading(true); // Set loading to true before fetching
      fetchData(storedToken);
    } else {
      console.log('❌ No token found, setting loading to false');
      setLoading(false);
    }
  }, []);

  // Get selected position
  const selectedPosition = filteredPositions.find(
    (position) => selectedDeviceId && position.deviceId === selectedDeviceId
  );

  // Get selected device
  const selectedDevice = filteredDevices.find(
    (device) => device.id === selectedDeviceId
  );

  // Show login button if not authenticated
  if (!token) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: 2,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Typography variant="h4" color="rgba(255, 255, 255, 0.9)" fontWeight="bold">
          Traccar Dashboard
        </Typography>
        <Typography variant="h6" color="rgba(255, 255, 255, 0.7)">
          Clique no botão para fazer login automaticamente
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={handleLogin}
          disabled={loading}
          sx={{ mt: 2 }}
        >
          {loading ? 'Fazendo Login...' : 'Login Automático'}
        </Button>
        {error && (
          <Alert severity="error" sx={{ mt: 2, maxWidth: 400 }}>
            {error}
          </Alert>
        )}
      </Box>
    );
  }

  // Show loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading dashboard data...
        </Typography>
      </Box>
    );
  }

  // Show error state
  if (error) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Alert severity="error" sx={{ mb: 3 }}>
          Error loading dashboard data: {error}
        </Alert>
        <Button variant="contained" onClick={handleLogin}>
          Tentar Novamente
        </Button>
      </Box>
    );
  }
  
  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Toolbar - Always visible */}
      {desktop && (
        <Box sx={{ zIndex: 10, position: 'relative' }}>
          <Paper
            square
            elevation={3}
            sx={{
              pointerEvents: 'auto',
              zIndex: 6,
            }}
          >
            <MainToolbar
              filteredDevices={filteredDevices}
              devicesOpen={devicesOpen}
              setDevicesOpen={setDevicesOpen}
              keyword={keyword}
              setKeyword={setKeyword}
              filter={filter}
              setFilter={setFilter}
              filterSort={filterSort}
              setFilterSort={setFilterSort}
              filterMap={filterMap}
              setFilterMap={setFilterMap}
            />
          </Paper>
        </Box>
      )}

      {/* Main Content Area */}
      <Box sx={{ flex: 1, display: 'flex', position: 'relative' }}>
        {/* Desktop Map - Full screen */}
        {desktop && (
          <MapView
            positions={filteredPositions}
            devices={filteredDevices.map(device => ({
              id: device.id,
              name: device.name,
              status: device.status || 'unknown',
              category: device.category || 'unknown',
              lastUpdate: device.last_update || new Date().toISOString(),
            }))}
            selectedDeviceId={selectedDeviceId}
            onDeviceSelect={onDeviceSelect}
            showGeofences={true}
            selectedGeofenceId={selectedGeofenceId}
            onGeofenceSelect={(geofence: Geofence) => setSelectedGeofenceId(geofence.id)}
            style={{ width: '100%', height: '100%' }}
          />
        )}

        {/* Desktop Overlay Panels */}
        {desktop && (
          <>
            {/* Left Sidebar Panel */}
            <Box
              sx={{
                position: 'absolute',
                left: 16,
                top: 80,
                width: 320,
                height: 'calc(100% - 120px)',
                zIndex: 100,
                pointerEvents: 'none',
                display: 'flex',
                flexDirection: 'column',
                gap: 1,
              }}
            >
              {/* Device List Panel */}
              <Paper
                square
                elevation={3}
                sx={{
                  pointerEvents: 'auto',
                  flex: 1,
                  maxHeight: devicesOpen ? '60%' : 60,
                  overflow: 'hidden',
                  transition: 'max-height 0.3s ease',
                }}
              >
                <DeviceList
                  devices={filteredDevices}
                  selectedDeviceId={selectedDeviceId}
                  onDeviceSelect={onDeviceSelect}
                />
              </Paper>
            </Box>

            {/* Bottom Menu Panel - Desktop */}
            <Box
              sx={{
                position: 'absolute',
                bottom: 16,
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 100,
                pointerEvents: 'auto',
              }}
            >
              <BottomMenu />
            </Box>
          </>
        )}

        {/* Mobile Layout */}
        {!desktop && (
          <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Mobile Toolbar */}
            <Paper
              square
              elevation={3}
              sx={{
                pointerEvents: 'auto',
                zIndex: 6,
              }}
            >
              <MainToolbar
                filteredDevices={filteredDevices}
                devicesOpen={devicesOpen}
                setDevicesOpen={setDevicesOpen}
                keyword={keyword}
                setKeyword={setKeyword}
                filter={filter}
                setFilter={setFilter}
                filterSort={filterSort}
                setFilterSort={setFilterSort}
                filterMap={filterMap}
                setFilterMap={setFilterMap}
              />
            </Paper>

            {/* Mobile Content */}
            <Box sx={{ flex: 1, display: 'grid', position: 'relative' }}>
              {/* Mobile Map */}
              <Box
                sx={{
                  pointerEvents: 'auto',
                  gridArea: '1 / 1',
                }}
              >
                <MapView
                  positions={filteredPositions}
                  devices={filteredDevices.map(device => ({
                    id: device.id,
                    name: device.name,
                    status: device.status || 'unknown',
                    category: device.category || 'unknown',
                    lastUpdate: device.last_update || new Date().toISOString(),
                  }))}
                  selectedDeviceId={selectedDeviceId}
                  onDeviceSelect={onDeviceSelect}
                  showGeofences={true}
                  selectedGeofenceId={selectedGeofenceId}
                  onGeofenceSelect={(geofence: Geofence) => setSelectedGeofenceId(geofence.id)}
                  style={{ width: '100%', height: '100%' }}
                />
              </Box>

              {/* Mobile Device List Overlay */}
              <Paper
                square
                sx={{
                  pointerEvents: 'auto',
                  gridArea: '1 / 1',
                  zIndex: 4,
                  ...(devicesOpen ? {} : { visibility: 'hidden' }),
                }}
              >
                <DeviceList
                  devices={filteredDevices}
                  selectedDeviceId={selectedDeviceId}
                  onDeviceSelect={onDeviceSelect}
                />
              </Paper>
            </Box>

            {/* Mobile Bottom Menu */}
            <Box sx={{ pointerEvents: 'auto', zIndex: 5 }}>
              <BottomMenu />
            </Box>
          </Box>
        )}
      </Box>

      {/* Events Drawer */}
      <EventsDrawer open={eventsOpen} onClose={() => setEventsOpen(false)} />

      {/* Status Card */}
      {selectedDeviceId && selectedDevice && (
        <StatusCard
          deviceId={selectedDeviceId}
          device={selectedDevice}
          position={selectedPosition}
          onClose={() => setSelectedDeviceId(undefined)}
          desktopPadding={320} // drawerWidthDesktop
        />
      )}
    </Box>
  );
};

export default Dashboard;
