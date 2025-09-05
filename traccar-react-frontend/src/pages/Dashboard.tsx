import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  useTheme,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  DeviceHub as DevicesIcon,
  LocationOn as LocationIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import MapView from '../components/map/MapView';
import { useWebSocket, usePositionUpdates, useDeviceStatusUpdates } from '../hooks/useWebSocket';
import { useDevices } from '../hooks/useDevices';
import { usePositions } from '../hooks/usePositions';
import { WebSocketTestPanel } from '../components/common/WebSocketTestPanel';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactElement;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              backgroundColor: color,
              borderRadius: '50%',
              width: 56,
              height: 56,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
            }}
          >
            {icon}
          </Box>
          <Box>
            <Typography variant="h4" component="div" fontWeight="bold">
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | undefined>();
  
  // Real data hooks
  const { devices, loading: devicesLoading, error: devicesError } = useDevices();
  const { latestPositions, loading: positionsLoading, error: positionsError } = usePositions();
  
  // WebSocket hooks for real-time updates
  const { connected, subscribe, unsubscribe } = useWebSocket();
  const { positions: wsPositions, lastPosition } = usePositionUpdates();
  const { deviceUpdates, lastDeviceUpdate } = useDeviceStatusUpdates();

  // Subscribe to real-time updates when component mounts
  useEffect(() => {
    if (connected) {
      subscribe('positions');
      subscribe('devices');
      subscribe('events');
      
      return () => {
        unsubscribe('positions');
        unsubscribe('devices');
        unsubscribe('events');
      };
    }
  }, [connected]); // Removed subscribe/unsubscribe from dependencies to prevent re-renders

  // Transform real data for map display (memoized to prevent re-renders)
  const mapDevices = useMemo(() => 
    devices.map(device => ({
      id: device.id,
      name: device.name,
      status: device.status,
      category: device.category || 'unknown',
      lastUpdate: device.last_update || new Date().toISOString(),
    })), 
    [devices]
  );

  const mapPositions = useMemo(() => 
    latestPositions.map(position => ({
      id: position.id,
      deviceId: position.device_id,
      latitude: position.latitude,
      longitude: position.longitude,
      course: position.course || 0,
      speed: position.speed || 0,
      fixTime: position.device_time || position.server_time,
      attributes: position.attributes || {},
    })), 
    [latestPositions]
  );

  // Calculate stats from real data (memoized to prevent re-renders)
  const stats = useMemo(() => {
    const onlineDevices = mapDevices.filter(d => d.status === 'online').length;
    const avgSpeed = mapPositions.length > 0 
      ? Math.round(mapPositions.reduce((sum, pos) => sum + (pos.speed || 0), 0) / mapPositions.length)
      : 0;
    const totalDistance = mapPositions.reduce((sum, pos) => sum + (pos.speed || 0) * 0.5, 0); // Mock calculation

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
      {
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
      },
    ];
  }, [mapDevices, mapPositions, theme.palette]);

  // Show loading state
  if (devicesLoading || positionsLoading) {
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
  if (devicesError || positionsError) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Alert severity="error" sx={{ mb: 3 }}>
          Error loading dashboard data: {devicesError || positionsError}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {stats.map((stat, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            <StatCard {...stat} />
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Paper sx={{ p: 2, height: 500 }}>
            <Typography variant="h6" gutterBottom>
              Live Map View
            </Typography>
            <Box sx={{ height: 'calc(100% - 40px)', borderRadius: 1, overflow: 'hidden' }}>
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
                  gap: 2
                }}>
                  <LocationIcon sx={{ fontSize: 48, color: 'text.secondary' }} />
                  <Typography variant="h6" color="text.secondary">
                    No device positions available
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Connect devices to see them on the map
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
        
        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper sx={{ p: 3, height: 500 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ mt: 2 }}>
              {mapPositions.length > 0 ? (
                <Box>
                  {mapPositions.slice(0, 5).map((position) => {
                    const device = mapDevices.find(d => d.id === position.deviceId);
                    return (
                      <Box key={position.id} sx={{ mb: 2, p: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                        <Typography variant="body2" fontWeight="bold">
                          {device?.name || 'Unknown Device'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {position.speed} km/h • {new Date(position.fixTime).toLocaleTimeString()}
                        </Typography>
                      </Box>
                    );
                  })}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No recent activity to display
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* WebSocket Test Panel - Only show in development */}
      {process.env.NODE_ENV === 'development' && (
        <Box sx={{ mt: 3 }}>
          <WebSocketTestPanel />
        </Box>
      )}
    </Box>
  );
};

export default Dashboard;
