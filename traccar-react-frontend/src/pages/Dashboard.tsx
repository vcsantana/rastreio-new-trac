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

      {/* Recent Activity Panel - Right Side */}
      <Box sx={{ 
        position: 'absolute', 
        top: 200, 
        right: 20, 
        width: 300,
        zIndex: 10 
      }}>
        <Paper sx={{ 
          p: 1.5,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(15px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 6px 24px rgba(0, 0, 0, 0.15)',
          borderRadius: '8px'
        }}>
          <Typography variant="body1" gutterBottom fontWeight="bold" color="rgba(0, 0, 0, 0.87)">
            Recent Activity
          </Typography>
          <Box sx={{ mt: 1.5, maxHeight: 200, overflowY: 'auto' }}>
            {mapPositions.length > 0 ? (
              <Box>
                {mapPositions.slice(0, 4).map((position) => {
                  const device = mapDevices.find(d => d.id === position.deviceId);
                  return (
                    <Box 
                      key={position.id} 
                      sx={{ 
                        mb: 1.5, 
                        p: 1.5, 
                        border: '1px solid rgba(0, 0, 0, 0.1)', 
                        borderRadius: '6px',
                        backgroundColor: 'rgba(255, 255, 255, 0.7)',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 255, 255, 0.9)',
                          transform: 'translateY(-1px)',
                          transition: 'all 0.2s ease',
                          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                        }
                      }}
                    >
                      <Typography variant="body2" fontWeight="bold" color="rgba(0, 0, 0, 0.87)" sx={{ fontSize: '0.8rem' }}>
                        {device?.name || 'Unknown Device'}
                      </Typography>
                      <Typography variant="caption" color="rgba(0, 0, 0, 0.6)" sx={{ fontSize: '0.7rem' }}>
                        {position.speed} km/h • {new Date(position.fixTime).toLocaleTimeString()}
                      </Typography>
                    </Box>
                  );
                })}
              </Box>
            ) : (
              <Typography variant="body2" color="rgba(0, 0, 0, 0.6)" sx={{ fontSize: '0.8rem' }}>
                No recent activity to display
              </Typography>
            )}
          </Box>
        </Paper>
      </Box>
    </Box>
  );
};

export default Dashboard;
