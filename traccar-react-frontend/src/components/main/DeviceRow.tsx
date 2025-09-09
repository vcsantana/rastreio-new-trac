import React from 'react';
import { useDispatch } from 'react-redux';
import {
  IconButton,
  Tooltip,
  Avatar,
  ListItemAvatar,
  ListItemText,
  ListItemButton,
  Typography,
} from '@mui/material';
import {
  BatteryFull as BatteryFullIcon,
  BatteryChargingFull as BatteryChargingFullIcon,
  Battery60 as Battery60Icon,
  BatteryCharging60 as BatteryCharging60Icon,
  Battery20 as Battery20Icon,
  BatteryCharging20 as BatteryCharging20Icon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { formatDistanceToNow } from 'date-fns';
import { Device } from '../../types/devices';
import { Position } from '../../types/positions';

interface DeviceRowProps {
  device: Device;
  index: number;
  data: Device[];
  style?: React.CSSProperties;
  position?: Position;
  selected?: boolean;
  onSelect?: (deviceId: number) => void;
}

const DeviceRow: React.FC<DeviceRowProps> = ({
  device,
  index,
  data,
  style,
  position,
  selected = false,
  onSelect,
}) => {
  const theme = useTheme();
  const dispatch = useDispatch();

  const handleClick = () => {
    if (onSelect) {
      onSelect(device.id);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return theme.palette.success.main;
      case 'offline':
        return theme.palette.error.main;
      default:
        return theme.palette.warning.main;
    }
  };

  const formatStatus = (status: string) => {
    switch (status) {
      case 'online':
        return 'Online';
      case 'offline':
        return 'Offline';
      default:
        return 'Unknown';
    }
  };

  const getSecondaryText = () => {
    if (device.status === 'online' || !device.last_update) {
      return formatStatus(device.status);
    } else {
      return formatDistanceToNow(new Date(device.last_update), { addSuffix: true });
    }
  };

  const getBatteryIcon = (batteryLevel: number, charging: boolean) => {
    if (batteryLevel > 70) {
      return charging ? <BatteryChargingFullIcon /> : <BatteryFullIcon />;
    } else if (batteryLevel > 30) {
      return charging ? <BatteryCharging60Icon /> : <Battery60Icon />;
    } else {
      return charging ? <BatteryCharging20Icon /> : <Battery20Icon />;
    }
  };

  const getBatteryColor = (batteryLevel: number) => {
    if (batteryLevel > 70) return theme.palette.success.main;
    if (batteryLevel > 30) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  return (
    <div style={style}>
      <ListItemButton
        key={device.id}
        onClick={handleClick}
        selected={selected}
        sx={{
          '&.Mui-selected': {
            backgroundColor: theme.palette.action.selected,
          },
        }}
      >
        <ListItemAvatar>
          <Avatar sx={{ 
            backgroundColor: getStatusColor(device.status),
            width: 32,
            height: 32,
          }}>
            <Typography variant="caption" sx={{ color: 'white', fontWeight: 'bold' }}>
              {device.name.charAt(0).toUpperCase()}
            </Typography>
          </Avatar>
        </ListItemAvatar>
        
        <ListItemText
          primary={device.name}
          secondary={
            <Typography 
              variant="body2" 
              sx={{ 
                color: getStatusColor(device.status),
                fontSize: '0.75rem',
              }}
            >
              {getSecondaryText()}
            </Typography>
          }
        />

        {position && (
          <>
            {position.attributes?.alarm && (
              <Tooltip title={`Alarm: ${position.attributes.alarm}`}>
                <IconButton size="small">
                  <ErrorIcon 
                    fontSize="small" 
                    sx={{ color: theme.palette.error.main }} 
                  />
                </IconButton>
              </Tooltip>
            )}
            
            {position.attributes?.ignition !== undefined && (
              <Tooltip title={`Ignition: ${position.attributes.ignition ? 'On' : 'Off'}`}>
                <IconButton size="small">
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      color: position.attributes.ignition ? 
                        theme.palette.success.main : 
                        theme.palette.grey[500],
                      fontSize: '0.7rem',
                      fontWeight: 'bold',
                    }}
                  >
                    🔧
                  </Typography>
                </IconButton>
              </Tooltip>
            )}
            
            {position.attributes?.batteryLevel && (
              <Tooltip title={`Battery: ${position.attributes.batteryLevel}%`}>
                <IconButton size="small">
                  <span style={{ color: getBatteryColor(position.attributes.batteryLevel) }}>
                    {getBatteryIcon(
                      position.attributes.batteryLevel, 
                      position.attributes.charge || false
                    )}
                  </span>
                </IconButton>
              </Tooltip>
            )}
          </>
        )}
      </ListItemButton>
    </div>
  );
};

export default DeviceRow;
