import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Grid,
  Chip,
  Card,
  CardContent,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Close as CloseIcon,
  Event as EventIcon,
  DeviceHub as DeviceIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  Speed as SpeedIcon,
  Navigation as NavigationIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Settings as SettingsIcon,
  Category as CategoryIcon,
  Timeline as TimelineIcon,
  Map as MapIcon,
  Share as ShareIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { Event, EventTypeInfo } from '../../types/events';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface EventDetailsProps {
  event: Event | null;
  eventTypeInfo: Record<string, EventTypeInfo>;
  open: boolean;
  onClose: () => void;
  onEdit?: (event: Event) => void;
  onDelete?: (event: Event) => void;
  onViewOnMap?: (event: Event) => void;
  onShare?: (event: Event) => void;
  onExport?: (event: Event) => void;
}

const EventDetails: React.FC<EventDetailsProps> = ({
  event,
  eventTypeInfo,
  open,
  onClose,
  onEdit,
  onDelete,
  onViewOnMap,
  onShare,
  onExport,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  if (!event) return null;

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
        return <SettingsIcon color="warning" />;
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
      if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
      if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} hours ago`;
      return `${Math.floor(diffInMinutes / 1440)} days ago`;
    } catch {
      return '';
    }
  };

  const typeInfo = eventTypeInfo[event.event_type];

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      fullScreen={isMobile}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getEventIcon(event.event_type)}
            <Typography variant="h6">
              {typeInfo?.name || event.event_type}
            </Typography>
            <Chip
              label={typeInfo?.severity || 'unknown'}
              size="small"
              color={getEventSeverityColor(event.event_type) as any}
            />
          </Box>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Grid container spacing={3}>
          {/* Basic Information */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <InfoIcon />
                  Basic Information
                </Typography>
                
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <EventIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Event Type"
                      secondary={typeInfo?.name || event.event_type}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      <DeviceIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Device"
                      secondary={event.device_name || `ID: ${event.device_id}`}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      <ScheduleIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Event Time"
                      secondary={
                        <Box>
                          <Typography variant="body2">
                            {formatEventTime(event.event_time)}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            ({formatRelativeTime(event.event_time)})
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      <CategoryIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Category"
                      secondary={typeInfo?.category || 'Unknown'}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      <WarningIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary="Severity"
                      secondary={
                        <Chip
                          label={typeInfo?.severity || 'unknown'}
                          size="small"
                          color={getEventSeverityColor(event.event_type) as any}
                        />
                      }
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Location Information */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LocationIcon />
                  Location Information
                </Typography>
                
                {event.position_data ? (
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <LocationIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Coordinates"
                        secondary={`${event.position_data.latitude.toFixed(6)}, ${event.position_data.longitude.toFixed(6)}`}
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        <SpeedIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Speed"
                        secondary={`${event.position_data.speed} km/h`}
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        <NavigationIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary="Course"
                        secondary={`${event.position_data.course}°`}
                      />
                    </ListItem>
                  </List>
                ) : (
                  <Typography color="textSecondary">
                    No location data available
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Event Description */}
          {typeInfo?.description && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <InfoIcon />
                    Description
                  </Typography>
                  <Typography variant="body1">
                    {typeInfo.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Attributes */}
          {event.attributes && Object.keys(event.attributes).length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SettingsIcon />
                    Event Attributes
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {Object.entries(event.attributes).map(([key, value]) => (
                      <Chip
                        key={key}
                        label={`${key}: ${value}`}
                        variant="outlined"
                        size="small"
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Related Information */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TimelineIcon />
                  Related Information
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Event ID
                    </Typography>
                    <Typography variant="body1">
                      {event.id}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Position ID
                    </Typography>
                    <Typography variant="body1">
                      {event.position_id || 'N/A'}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Geofence ID
                    </Typography>
                    <Typography variant="body1">
                      {event.geofence_id || 'N/A'}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Maintenance ID
                    </Typography>
                    <Typography variant="body1">
                      {event.maintenance_id || 'N/A'}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Created At
                    </Typography>
                    <Typography variant="body1">
                      {formatEventTime(event.created_at)}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Updated At
                    </Typography>
                    <Typography variant="body1">
                      {formatEventTime(event.updated_at)}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {onViewOnMap && (
            <Button
              variant="outlined"
              startIcon={<MapIcon />}
              onClick={() => onViewOnMap(event)}
            >
              View on Map
            </Button>
          )}
          
          {onShare && (
            <Button
              variant="outlined"
              startIcon={<ShareIcon />}
              onClick={() => onShare(event)}
            >
              Share
            </Button>
          )}
          
          {onExport && (
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => onExport(event)}
            >
              Export
            </Button>
          )}
          
          {onEdit && (
            <Button
              variant="outlined"
              startIcon={<SettingsIcon />}
              onClick={() => onEdit(event)}
            >
              Edit
            </Button>
          )}
          
          {onDelete && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<CloseIcon />}
              onClick={() => onDelete(event)}
            >
              Delete
            </Button>
          )}
          
          <Button onClick={onClose}>
            Close
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
};

export default EventDetails;
