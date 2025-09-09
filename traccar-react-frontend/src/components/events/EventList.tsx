import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Box,
  Chip,
  Paper,
  Pagination,
  CircularProgress,
  Alert,
  Tooltip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  LocationOn as LocationIcon,
  Speed as SpeedIcon,
  Schedule as ScheduleIcon,
  DeviceHub as DeviceIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Event as EventIcon,
} from '@mui/icons-material';
import { Event, EventTypeInfo } from '../../types/events';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface EventListProps {
  events: Event[];
  eventTypeInfo: Record<string, EventTypeInfo>;
  loading: boolean;
  error: string | null;
  total: number;
  page: number;
  size: number;
  hasNext: boolean;
  hasPrev: boolean;
  onEventSelect: (event: Event) => void;
  onPageChange: (page: number) => void;
  showPagination?: boolean;
  showDeviceInfo?: boolean;
  showLocationInfo?: boolean;
  compact?: boolean;
}

const EventList: React.FC<EventListProps> = ({
  events,
  eventTypeInfo,
  loading,
  error,
  total,
  page,
  size,
  hasNext,
  hasPrev,
  onEventSelect,
  onPageChange,
  showPagination = true,
  showDeviceInfo = true,
  showLocationInfo = true,
  compact = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Get event icon based on type
  const getEventIcon = (eventType: string) => {
    const typeInfo = eventTypeInfo[eventType];
    if (!typeInfo) return <EventIcon />;

    switch (typeInfo.icon) {
      case 'online':
        return <CheckCircleIcon color="success" />;
      case 'offline':
        return <ErrorIcon color="error" />;
      case 'moving':
        return <SpeedIcon color="primary" />;
      case 'stopped':
        return <CheckCircleIcon color="warning" />;
      case 'speed':
        return <SpeedIcon color="error" />;
      case 'fuel':
        return <WarningIcon color="warning" />;
      case 'ignition':
        return <CheckCircleIcon color="info" />;
      case 'maintenance':
        return <WarningIcon color="warning" />;
      case 'command':
        return <CheckCircleIcon color="primary" />;
      case 'driver':
        return <DeviceIcon color="secondary" />;
      case 'geofence':
        return <CheckCircleIcon color="primary" />;
      case 'alarm':
        return <WarningIcon color="error" />;
      default:
        return <EventIcon />;
    }
  };

  // Get event severity color
  const getEventSeverityColor = (eventType: string) => {
    const typeInfo = eventTypeInfo[eventType];
    if (!typeInfo) return 'default';

    switch (typeInfo.severity) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  // Format event time
  const formatEventTime = (eventTime: string) => {
    try {
      if (compact) {
        return format(new Date(eventTime), 'dd/MM HH:mm', { locale: ptBR });
      }
      return format(new Date(eventTime), 'dd/MM/yyyy HH:mm:ss', { locale: ptBR });
    } catch {
      return eventTime;
    }
  };

  // Format relative time
  const formatRelativeTime = (eventTime: string) => {
    try {
      const now = new Date();
      const eventDate = new Date(eventTime);
      const diffInMinutes = Math.floor((now.getTime() - eventDate.getTime()) / (1000 * 60));

      if (diffInMinutes < 1) return 'Just now';
      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
      if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
      return `${Math.floor(diffInMinutes / 1440)}d ago`;
    } catch {
      return '';
    }
  };

  // Handle pagination change
  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    onPageChange(value);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (events.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <Typography color="textSecondary">No events found</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <List sx={{ width: '100%' }}>
        {events.map((event) => (
          <ListItem
            key={event.id}
            button
            onClick={() => onEventSelect(event)}
            sx={{
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              mb: 1,
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
          >
            <ListItemIcon>
              {getEventIcon(event.event_type)}
            </ListItemIcon>
            
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant={compact ? 'body2' : 'subtitle1'}>
                    {eventTypeInfo[event.event_type]?.name || event.event_type}
                  </Typography>
                  <Chip
                    label={eventTypeInfo[event.event_type]?.severity || 'unknown'}
                    size="small"
                    color={getEventSeverityColor(event.event_type) as any}
                  />
                  {!compact && (
                    <Chip
                      label={eventTypeInfo[event.event_type]?.category || 'unknown'}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  )}
                </Box>
              }
              secondary={
                <Box>
                  {showDeviceInfo && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <DeviceIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="textSecondary">
                        {event.device_name || `Device ID: ${event.device_id}`}
                      </Typography>
                    </Box>
                  )}
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                    <ScheduleIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="textSecondary">
                      {formatEventTime(event.event_time)}
                    </Typography>
                    {!compact && (
                      <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
                        ({formatRelativeTime(event.event_time)})
                      </Typography>
                    )}
                  </Box>
                  
                  {showLocationInfo && event.position_data && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                      <LocationIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="textSecondary">
                        {event.position_data.latitude.toFixed(6)}, {event.position_data.longitude.toFixed(6)}
                      </Typography>
                    </Box>
                  )}
                  
                  {showLocationInfo && event.position_data && event.position_data.speed > 0 && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <SpeedIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="textSecondary">
                        {event.position_data.speed} km/h
                      </Typography>
                    </Box>
                  )}
                </Box>
              }
            />
            
            <ListItemSecondaryAction>
              <Tooltip title="View Details">
                <IconButton edge="end" onClick={() => onEventSelect(event)}>
                  <VisibilityIcon />
                </IconButton>
              </Tooltip>
            </ListItemSecondaryAction>
          </ListItem>
        ))}
      </List>

      {/* Pagination */}
      {showPagination && total > size && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={Math.ceil(total / size)}
            page={page}
            onChange={handlePageChange}
            color="primary"
            size={isMobile ? 'small' : 'medium'}
            showFirstButton
            showLastButton
          />
        </Box>
      )}
    </Box>
  );
};

export default EventList;
