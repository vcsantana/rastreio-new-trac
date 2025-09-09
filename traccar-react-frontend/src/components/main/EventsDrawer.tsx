import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Toolbar,
  Typography,
  Box,
} from '@mui/material';
import {
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useEvents } from '../../hooks/useEvents';
import { useDevices } from '../../hooks/useDevices';
import { formatDistanceToNow } from 'date-fns';

interface EventsDrawerProps {
  open: boolean;
  onClose: () => void;
}

const EventsDrawer: React.FC<EventsDrawerProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { events, deleteEvent, clearAllEvents } = useEvents();
  const { devices } = useDevices();

  const handleEventClick = (eventId: number) => {
    navigate(`/events/${eventId}`);
  };

  const handleDeleteEvent = (eventId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteEvent(eventId);
  };

  const handleClearAll = () => {
    clearAllEvents();
  };

  const formatEventType = (event: any) => {
    // Simple event type formatting
    if (event.type) {
      return event.type.replace(/([A-Z])/g, ' $1').trim();
    }
    return 'Event';
  };

  const getDeviceName = (deviceId: number) => {
    const device = devices.find(d => d.id === deviceId);
    return device?.name || `Device ${deviceId}`;
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: 320,
        },
      }}
    >
      <Toolbar 
        sx={{ 
          paddingLeft: theme.spacing(2),
          paddingRight: theme.spacing(2),
          minHeight: '48px !important',
        }}
      >
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Events
        </Typography>
        <IconButton 
          size="small" 
          color="inherit" 
          onClick={handleClearAll}
          disabled={events.length === 0}
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      </Toolbar>

      <List dense sx={{ width: '100%' }}>
        {events.length === 0 ? (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            height: 200,
            color: 'text.secondary',
          }}>
            <Typography variant="body2">
              No events available
            </Typography>
          </Box>
        ) : (
          events.map((event) => (
            <ListItemButton
              key={event.id}
              onClick={() => handleEventClick(event.id)}
              disabled={!event.id}
            >
              <ListItemText
                primary={`${getDeviceName(event.deviceId)} • ${formatEventType(event)}`}
                secondary={formatDistanceToNow(new Date(event.eventTime), { addSuffix: true })}
                primaryTypographyProps={{ noWrap: true }}
                secondaryTypographyProps={{ noWrap: true }}
              />
              <IconButton
                size="small"
                onClick={(e) => handleDeleteEvent(event.id, e)}
                sx={{ ml: 1 }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </ListItemButton>
          ))
        )}
      </List>
    </Drawer>
  );
};

export default EventsDrawer;
