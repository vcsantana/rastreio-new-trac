import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Divider
} from '@mui/material';
import {
  Close,
  Speed as SpeedIcon,
  Navigation as NavigationIcon,
  AccessTime as AccessTimeIcon,
  BatteryFull,
  SignalCellular4Bar as SignalIcon
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';

interface Position {
  id: number;
  deviceId: number;
  latitude: number;
  longitude: number;
  course?: number;
  speed?: number;
  fixTime?: string;
  attributes?: Record<string, any>;
}

interface Device {
  id: number;
  name: string;
  status: string;
  category?: string;
  lastUpdate?: string;
}

interface DeviceInfoCardProps {
  device: Device;
  position?: Position;
  onClose: () => void;
}

const DeviceInfoCard: React.FC<DeviceInfoCardProps> = ({
  device,
  position,
  onClose
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatSpeed = (speed?: number) => {
    if (speed === undefined) return 'N/A';
    return `${Math.round(speed * 1.852)} km/h`; // Convert knots to km/h
  };

  const formatCourse = (course?: number) => {
    if (course === undefined) return 'N/A';
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(course / 45) % 8;
    return `${Math.round(course)}° (${directions[index]})`;
  };

  const formatLastUpdate = (timestamp?: string) => {
    if (!timestamp) return 'Unknown';
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
    } catch {
      return 'Unknown';
    }
  };

  const getBatteryLevel = () => {
    return position?.attributes?.battery || position?.attributes?.batteryLevel;
  };

  const getSignalStrength = () => {
    return position?.attributes?.rssi || position?.attributes?.signal;
  };

  return (
    <Card
      sx={{
        position: 'absolute',
        top: 16,
        right: 16,
        width: 320,
        maxWidth: '90vw',
        zIndex: 1000,
        maxHeight: '80vh',
        overflow: 'auto'
      }}
      elevation={4}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="div" gutterBottom>
              {device.name}
            </Typography>
            <Chip 
              label={device.status} 
              color={getStatusColor(device.status) as any}
              size="small"
            />
          </Box>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Position Info */}
        {position && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Current Position
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <SpeedIcon sx={{ mr: 1, fontSize: 18 }} />
              <Typography variant="body2">
                Speed: {formatSpeed(position.speed)}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <NavigationIcon sx={{ mr: 1, fontSize: 18 }} />
              <Typography variant="body2">
                Direction: {formatCourse(position.course)}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <AccessTimeIcon sx={{ mr: 1, fontSize: 18 }} />
              <Typography variant="body2">
                Last Update: {formatLastUpdate(position.fixTime)}
              </Typography>
            </Box>
          </Box>
        )}

        <Divider sx={{ mb: 2 }} />

        {/* Device Details */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Device Details
          </Typography>
          
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>ID:</strong> {device.id}
          </Typography>
          
          {device.category && (
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>Category:</strong> {device.category}
            </Typography>
          )}

          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Coordinates:</strong> {position ? `${position.latitude.toFixed(6)}, ${position.longitude.toFixed(6)}` : 'N/A'}
          </Typography>
        </Box>

        {/* Additional Attributes */}
        {position?.attributes && Object.keys(position.attributes).length > 0 && (
          <>
            <Divider sx={{ mb: 2 }} />
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Additional Info
              </Typography>
              
              {getBatteryLevel() && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <BatteryFull sx={{ mr: 1, fontSize: 18 }} />
                  <Typography variant="body2">
                    Battery: {getBatteryLevel()}%
                  </Typography>
                </Box>
              )}

              {getSignalStrength() && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <SignalIcon sx={{ mr: 1, fontSize: 18 }} />
                  <Typography variant="body2">
                    Signal: {getSignalStrength()} dBm
                  </Typography>
                </Box>
              )}

              {/* Show other attributes */}
              {Object.entries(position.attributes)
                .filter(([key]) => !['battery', 'batteryLevel', 'rssi', 'signal'].includes(key))
                .slice(0, 5) // Limit to 5 additional attributes
                .map(([key, value]) => (
                  <Typography key={key} variant="body2" sx={{ mb: 0.5 }}>
                    <strong>{key}:</strong> {String(value)}
                  </Typography>
                ))}
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default DeviceInfoCard;
