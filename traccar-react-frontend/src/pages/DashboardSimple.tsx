import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  useTheme,
  useMediaQuery,
  Fab,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  DeviceHub as DevicesIcon,
  Event as EventsIcon,
  Settings as SettingsIcon,
  NotificationsActive as NotificationsActiveIcon,
} from '@mui/icons-material';
import MapView from '../components/map/MapView';
import { useDevices } from '../hooks/useDevices';
import { usePositions } from '../hooks/usePositions';
import { useEvents } from '../hooks/useEvents';
import { useGeofences } from '../hooks/useGeofences';
import { useNavigate } from 'react-router-dom';

const DashboardSimple: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  
  const { devices, loading: devicesLoading } = useDevices();
  const { positions } = usePositions();
  const { events, notifications } = useEvents();
  const { geofences } = useGeofences();

  const [selectedDeviceId, setSelectedDeviceId] = useState<number | undefined>();
  const [showEvents, setShowEvents] = useState(false);
  const [showGeofences, setShowGeofences] = useState(true);

  // Get unread notifications count
  const unreadCount = notifications?.filter(n => !n.read).length || 0;

  // Handle device selection
  const handleDeviceSelect = (deviceId: number) => {
    setSelectedDeviceId(deviceId);
  };

  // Handle event selection
  const handleEventSelect = (event: any) => {
    console.log('Event selected:', event);
    // Navigate to events page or show event details
    navigate('/events');
  };

  // Handle geofence selection
  const handleGeofenceSelect = (geofence: any) => {
    console.log('Geofence selected:', geofence);
  };

  return (
    <Box sx={{ height: '100%', position: 'relative' }}>
      {/* Main Map View */}
      <MapView
        positions={positions}
        devices={devices.map(device => ({
          id: device.id,
          name: device.name,
          status: device.status || 'offline',
          category: device.category,
          lastUpdate: device.last_update,
        }))}
        selectedDeviceId={selectedDeviceId}
        onDeviceSelect={handleDeviceSelect}
        showGeofences={showGeofences}
        showEvents={showEvents}
        onEventSelect={handleEventSelect}
        onGeofenceSelect={handleGeofenceSelect}
        style={{ height: '100%', width: '100%' }}
      />

      {/* Floating Action Buttons */}
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
          zIndex: 1000,
        }}
      >
        {/* Events Toggle */}
        <Tooltip title={showEvents ? 'Hide Events' : 'Show Events'}>
          <Fab
            size="small"
            color={showEvents ? 'primary' : 'default'}
            onClick={() => setShowEvents(!showEvents)}
            sx={{ mb: 1 }}
          >
            <Badge badgeContent={unreadCount} color="error">
              {unreadCount > 0 ? <NotificationsActiveIcon /> : <EventsIcon />}
            </Badge>
          </Fab>
        </Tooltip>

        {/* Geofences Toggle */}
        <Tooltip title={showGeofences ? 'Hide Geofences' : 'Show Geofences'}>
          <Fab
            size="small"
            color={showGeofences ? 'primary' : 'default'}
            onClick={() => setShowGeofences(!showGeofences)}
          >
            <SettingsIcon />
          </Fab>
        </Tooltip>
      </Box>

      {/* Quick Stats (Desktop only) */}
      {!isMobile && (
        <Paper
          sx={{
            position: 'absolute',
            top: 16,
            left: 16,
            p: 2,
            minWidth: 200,
            zIndex: 1000,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <Typography variant="h6" gutterBottom>
            Dashboard
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <DevicesIcon color="primary" />
              <Typography variant="body2">
                {devices.length} Devices
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <EventsIcon color="secondary" />
              <Typography variant="body2">
                {events.length} Recent Events
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SettingsIcon color="action" />
              <Typography variant="body2">
                {geofences.length} Geofences
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}

      {/* Loading Overlay */}
      {devicesLoading && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000,
          }}
        >
          <Typography>Loading...</Typography>
        </Box>
      )}
    </Box>
  );
};

export default DashboardSimple;