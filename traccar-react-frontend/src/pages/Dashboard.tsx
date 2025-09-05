import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  useTheme,
} from '@mui/material';
import {
  DeviceHub as DevicesIcon,
  LocationOn as LocationIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import MapView from '../components/map/MapView';
import { useWebSocket, usePositionUpdates, useDeviceStatusUpdates } from '../hooks/useWebSocket';
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
  
  // WebSocket hooks for real-time updates
  const { connected, subscribe, unsubscribe } = useWebSocket();
  const { positions, lastPosition } = usePositionUpdates();
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

  // Mock device data - replace with real API calls (memoized to prevent re-renders)
  const mockDevices = useMemo(() => [
    {
      id: 1,
      name: 'Vehicle 001',
      status: 'online',
      category: 'car',
      lastUpdate: new Date().toISOString(),
    },
    {
      id: 2,
      name: 'Truck 002',
      status: 'offline',
      category: 'truck',
      lastUpdate: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    },
    {
      id: 3,
      name: 'Motorcycle 003',
      status: 'online',
      category: 'motorcycle',
      lastUpdate: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
    },
    {
      id: 4,
      name: 'Delivery Van 004',
      status: 'online',
      category: 'van',
      lastUpdate: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
    },
  ], []);

  // Mock position data - replace with real API calls (memoized to prevent re-renders)
  const mockPositions = useMemo(() => [
    {
      id: 1,
      deviceId: 1,
      latitude: -23.5505,
      longitude: -46.6333,
      course: 45,
      speed: 60,
      fixTime: new Date().toISOString(),
      attributes: { battery: 85, signal: -65 },
    },
    {
      id: 2,
      deviceId: 2,
      latitude: -23.5485,
      longitude: -46.6365,
      course: 180,
      speed: 0,
      fixTime: new Date(Date.now() - 3600000).toISOString(),
      attributes: { battery: 45, signal: -78 },
    },
    {
      id: 3,
      deviceId: 3,
      latitude: -23.5525,
      longitude: -46.6355,
      course: 90,
      speed: 35,
      fixTime: new Date(Date.now() - 1800000).toISOString(),
      attributes: { battery: 92, signal: -58 },
    },
    {
      id: 4,
      deviceId: 4,
      latitude: -23.5495,
      longitude: -46.6345,
      course: 270,
      speed: 25,
      fixTime: new Date(Date.now() - 300000).toISOString(),
      attributes: { battery: 78, signal: -70 },
    },
  ], []);

  // Calculate stats from mock data (memoized to prevent re-renders)
  const stats = useMemo(() => {
    const onlineDevices = mockDevices.filter(d => d.status === 'online').length;
    const avgSpeed = Math.round(
      mockPositions.reduce((sum, pos) => sum + (pos.speed || 0), 0) / mockPositions.length
    );
    const totalDistance = mockPositions.reduce((sum, pos) => sum + (pos.speed || 0) * 0.5, 0); // Mock calculation

    return [
      {
        title: 'Total Devices',
        value: mockDevices.length,
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
  }, [mockDevices, mockPositions, theme.palette]);

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
              <MapView
                positions={mockPositions}
                devices={mockDevices}
                selectedDeviceId={selectedDeviceId}
                onDeviceSelect={setSelectedDeviceId}
                style={{ width: '100%', height: '100%' }}
              />
            </Box>
          </Paper>
        </Grid>
        
        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper sx={{ p: 3, height: 500 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                No recent activity to display
              </Typography>
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
