import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  useTheme,
  Alert,
  CircularProgress,
  Button,
} from '@mui/material';
import {
  DeviceHub as DevicesIcon,
  LocationOn as LocationIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import MapView from '../components/map/MapView';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactElement;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => {
  return (
    <Card sx={{ 
      height: '100%',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(15px)',
      border: '1px solid rgba(255, 255, 255, 0.3)',
      boxShadow: '0 6px 24px rgba(0, 0, 0, 0.15)',
      '&:hover': {
        backgroundColor: 'rgba(255, 255, 255, 1)',
        transform: 'translateY(-1px)',
        transition: 'all 0.3s ease',
        boxShadow: '0 8px 28px rgba(0, 0, 0, 0.2)',
      }
    }}>
      <CardContent sx={{ p: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              backgroundColor: color,
              borderRadius: '50%',
              width: 28,
              height: 28,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
            }}
          >
            {icon}
          </Box>
          <Box>
            <Typography variant="body1" component="div" fontWeight="bold" color="rgba(0, 0, 0, 0.87)">
              {value}
            </Typography>
            <Typography variant="caption" color="rgba(0, 0, 0, 0.6)" fontWeight="medium" sx={{ fontSize: '0.7rem' }}>
              {title}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const DashboardTest: React.FC = () => {
  const theme = useTheme();
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | undefined>();
  const [devices, setDevices] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

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

      setDevices(devicesData);
      setPositions(positionsData);
      setError(null);
      setLoading(false);
      console.log('✅ Data fetch completed successfully - loading set to false');
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

  // Transform data for map display
  const mapDevices = useMemo(() => {
    const converted = devices.map(device => ({
      id: device.id,
      name: device.name,
      status: device.status || 'unknown',
      category: device.category || 'unknown',
      lastUpdate: device.last_update || new Date().toISOString(),
    }));
    console.log('📱 Converted devices for map:', converted);
    return converted;
  }, [devices]);

  const mapPositions = useMemo(() => {
    const converted = positions.map(position => ({
      id: position.id,
      deviceId: position.device_id || position.unknown_device_id,
      latitude: position.latitude,
      longitude: position.longitude,
      course: position.course || 0,
      speed: position.speed || 0,
      fixTime: position.device_time || position.server_time,
      attributes: position.attributes || {},
    }));
    console.log('🗺️ Converted positions for map:', converted);
    return converted;
  }, [positions]);

  // Calculate stats
  const stats = useMemo(() => {
    const onlineDevices = mapDevices.filter(d => d.status === 'online').length;
    const avgSpeed = mapPositions.length > 0 
      ? Math.round(mapPositions.reduce((sum, pos) => sum + (pos.speed || 0), 0) / mapPositions.length)
      : 0;
    const totalDistance = mapPositions.reduce((sum, pos) => sum + (pos.speed || 0) * 0.5, 0);

    return [
      {
        title: 'Total Devices',
        value: mapDevices.length,
        icon: <DevicesIcon />,
        color: theme.palette.primary.main,
      },
      {
        title: 'Online Devices',
        value: onlineDevices,
        icon: <LocationIcon />,
        color: theme.palette.success.main,
      },
      /*{
        title: 'Avg Speed',
        value: `${avgSpeed} km/h`,
        icon: <SpeedIcon />,
        color: theme.palette.warning.main,
      },
      {
        title: 'Total Distance',
        value: `${Math.round(totalDistance)} km`,
        icon: <TimelineIcon />,
        color: theme.palette.info.main,
      },*/
    ];
  }, [mapDevices, mapPositions, theme.palette]);

  // Debug logs
  console.log('🎯 DashboardTest render - token:', !!token, 'loading:', loading, 'error:', error, 'devices:', devices.length, 'positions:', positions.length);

  // Show login button if not authenticated
  if (!token) {
    console.log('🔐 No token, showing login button');
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
    console.log('⏳ Loading state, showing spinner');
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
    console.log('❌ Error state, showing error message');
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

  console.log('🗺️ Rendering map with', mapPositions.length, 'positions and', mapDevices.length, 'devices');
  
  return (
    <Box sx={{ 
      position: 'relative', 
      height: '100vh', 
      overflow: 'hidden',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      {/* Full-screen Map */}
      <Box sx={{ 
        position: 'absolute', 
        top: 0, 
        left: 0, 
        right: 0, 
        bottom: 0,
        zIndex: 1
      }}>
        {mapPositions.length > 0 ? (
          <MapView
            positions={mapPositions}
            devices={mapDevices}
            selectedDeviceId={selectedDeviceId}
            onDeviceSelect={setSelectedDeviceId}
            style={{ width: '100%', height: '100%' }}
          />
        ) : (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%',
            flexDirection: 'column',
            gap: 2,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
          }}>
            <LocationIcon sx={{ fontSize: 64, color: 'rgba(255, 255, 255, 0.7)' }} />
            <Typography variant="h4" color="rgba(255, 255, 255, 0.9)" fontWeight="bold">
              No device positions available
            </Typography>
            <Typography variant="h6" color="rgba(255, 255, 255, 0.7)">
              Connect devices to see them on the map
            </Typography>
          </Box>
        )}
      </Box>

      {/* Statistics Cards - Overlay */}
      <Box sx={{ 
        position: 'absolute', 
        top: 10, 
        left: 20, 
        right: 20, 
        zIndex: 10 
      }}>
        <Grid container spacing={2}>
          {stats.map((stat, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
              <StatCard {...stat} />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
};

export default DashboardTest;
