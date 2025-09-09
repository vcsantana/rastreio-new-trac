import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Rnd } from 'react-rnd';
import {
  Card,
  CardContent,
  Typography,
  CardActions,
  IconButton,
  Table,
  TableBody,
  TableRow,
  TableCell,
  Menu,
  MenuItem,
  CardMedia,
  TableFooter,
  Link,
  Tooltip,
  Box,
} from '@mui/material';
import {
  Close as CloseIcon,
  Replay as ReplayIcon,
  Send as SendIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { Device } from '../../types/devices';
import { Position } from '../../types/positions';
import { formatDistanceToNow } from 'date-fns';

interface StatusCardProps {
  deviceId: number;
  device?: Device;
  position?: Position;
  onClose: () => void;
  desktopPadding?: number;
}

const StatusCard: React.FC<StatusCardProps> = ({
  deviceId,
  device,
  position,
  onClose,
  desktopPadding = 0,
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleReplay = () => {
    navigate(`/reports?deviceId=${deviceId}`);
  };

  const handleCommand = () => {
    navigate(`/commands?deviceId=${deviceId}`);
  };

  const handleEdit = () => {
    navigate(`/devices/${deviceId}/edit`);
  };

  const handleDelete = () => {
    // TODO: Implement delete functionality
    console.log('Delete device:', deviceId);
  };

  const handleGeofence = () => {
    if (position) {
      navigate(`/geofences?lat=${position.latitude}&lng=${position.longitude}`);
    }
  };

  const formatValue = (key: string, value: any) => {
    switch (key) {
      case 'fixTime':
        return formatDistanceToNow(new Date(value), { addSuffix: true });
      case 'speed':
        return `${value} km/h`;
      case 'course':
        return `${value}°`;
      case 'altitude':
        return `${value} m`;
      case 'address':
        return value || 'Unknown';
      default:
        return value?.toString() || 'N/A';
    }
  };

  const getPositionItems = () => {
    if (!position) return [];
    
    const items = [
      { key: 'fixTime', label: 'Last Update', value: position.fixTime },
      { key: 'address', label: 'Address', value: position.address },
      { key: 'speed', label: 'Speed', value: position.speed },
      { key: 'course', label: 'Course', value: position.course },
      { key: 'altitude', label: 'Altitude', value: position.altitude },
    ];

    // Add attributes
    if (position.attributes) {
      Object.entries(position.attributes).forEach(([key, value]) => {
        if (key !== 'alarm' && key !== 'ignition' && key !== 'batteryLevel') {
          items.push({ key, label: key, value });
        }
      });
    }

    return items.filter(item => item.value !== undefined && item.value !== null);
  };

  if (!device) return null;

  return (
    <Box
      sx={{
        position: 'fixed',
        zIndex: 5,
        left: '50%',
        [theme.breakpoints.up('md')]: {
          left: `calc(50% + ${desktopPadding} / 2)`,
          bottom: theme.spacing(3),
        },
        [theme.breakpoints.down('md')]: {
          left: '50%',
          bottom: theme.spacing(3),
        },
        transform: 'translateX(-50%)',
        pointerEvents: 'none',
      }}
    >
      <Rnd
        default={{ x: 0, y: 0, width: 'auto', height: 'auto' }}
        enableResizing={false}
        dragHandleClassName="draggable-header"
        style={{ position: 'relative' }}
      >
        <Card 
          elevation={3}
          sx={{ 
            width: 320,
            pointerEvents: 'auto',
          }}
        >
          {/* Header */}
          <Box
            className="draggable-header"
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: theme.spacing(1, 1, 0, 2),
              cursor: 'move',
            }}
          >
            <Typography variant="body2" color="textSecondary">
              {device.name}
            </Typography>
            <IconButton
              size="small"
              onClick={onClose}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>

          {/* Content */}
          {position && (
            <CardContent sx={{ paddingTop: 1, paddingBottom: 1 }}>
              <Table size="small">
                <TableBody>
                  {getPositionItems().map((item) => (
                    <TableRow key={item.key}>
                      <TableCell sx={{ borderBottom: 'none', paddingLeft: 0, paddingRight: 1 }}>
                        <Typography variant="body2">{item.label}</Typography>
                      </TableCell>
                      <TableCell sx={{ borderBottom: 'none', paddingLeft: 0, paddingRight: 0 }}>
                        <Typography variant="body2" color="textSecondary">
                          {formatValue(item.key, item.value)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
                <TableFooter>
                  <TableRow>
                    <TableCell colSpan={2} sx={{ borderBottom: 'none', paddingLeft: 0 }}>
                      <Link 
                        component="button" 
                        variant="body2"
                        onClick={() => navigate(`/positions/${position.id}`)}
                      >
                        Show Details
                      </Link>
                    </TableCell>
                  </TableRow>
                </TableFooter>
              </Table>
            </CardContent>
          )}

          {/* Actions */}
          <CardActions sx={{ justifyContent: 'space-between' }}>
            <Tooltip title="More Options">
              <IconButton
                color="secondary"
                onClick={handleMenuOpen}
                disabled={!position}
              >
                <MoreVertIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Replay">
              <IconButton
                onClick={handleReplay}
                disabled={!position}
              >
                <ReplayIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Send Command">
              <IconButton
                onClick={handleCommand}
              >
                <SendIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Edit Device">
              <IconButton
                onClick={handleEdit}
              >
                <EditIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Delete Device">
              <IconButton
                color="error"
                onClick={handleDelete}
              >
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          </CardActions>
        </Card>
      </Rnd>

      {/* Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleGeofence}>
          Create Geofence
        </MenuItem>
        {position && (
          <>
            <MenuItem 
              component="a" 
              target="_blank" 
              href={`https://www.google.com/maps/search/?api=1&query=${position.latitude}%2C${position.longitude}`}
            >
              Google Maps
            </MenuItem>
            <MenuItem 
              component="a" 
              target="_blank" 
              href={`http://maps.apple.com/?ll=${position.latitude},${position.longitude}`}
            >
              Apple Maps
            </MenuItem>
          </>
        )}
      </Menu>
    </Box>
  );
};

export default StatusCard;
