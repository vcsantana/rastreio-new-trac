import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  Snackbar,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Badge,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Event as EventIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Notifications as NotificationsIcon,
  NotificationsActive as NotificationsActiveIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Close as CloseIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Search as SearchIcon,
  CalendarToday as CalendarIcon,
  DeviceHub as DeviceIcon,
  Category as CategoryIcon,
} from '@mui/icons-material';
import { useEvents } from '../hooks/useEvents';
import { useDevices } from '../hooks/useDevices';
import { Event, EventFilters, EventNotification } from '../types/events';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`events-tabpanel-${index}`}
      aria-labelledby={`events-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Events: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const {
    events,
    eventStats,
    eventTypes,
    eventTypeInfo,
    notifications,
    loading,
    loadingStats,
    error,
    total,
    page,
    size,
    hasNext,
    hasPrev,
    fetchEvents,
    fetchEventStats,
    exportEventsCSV,
    markNotificationAsRead,
    clearNotifications,
    refreshEvents,
  } = useEvents();

  const { devices } = useDevices();

  const [tabValue, setTabValue] = useState(0);
  const [filters, setFilters] = useState<EventFilters>({
    page: 1,
    size: 50,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [showEventDetails, setShowEventDetails] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // Load initial data
  useEffect(() => {
    fetchEvents(filters);
    fetchEventStats(7);
  }, [fetchEvents, fetchEventStats]);

  // Handle filter changes
  const handleFilterChange = (newFilters: Partial<EventFilters>) => {
    const updatedFilters = { ...filters, ...newFilters, page: 1 };
    setFilters(updatedFilters);
    fetchEvents(updatedFilters);
  };

  // Handle pagination
  const handlePageChange = (newPage: number) => {
    const updatedFilters = { ...filters, page: newPage };
    setFilters(updatedFilters);
    fetchEvents(updatedFilters);
  };

  // Handle export
  const handleExport = async () => {
    try {
      await exportEventsCSV(filters);
      setSnackbar({
        open: true,
        message: 'Events exported successfully',
        severity: 'success',
      });
    } catch (err) {
      setSnackbar({
        open: true,
        message: 'Failed to export events',
        severity: 'error',
      });
    }
  };

  // Handle refresh
  const handleRefresh = async () => {
    await refreshEvents();
    setSnackbar({
      open: true,
      message: 'Events refreshed',
      severity: 'info',
    });
  };

  // Handle event selection
  const handleEventSelect = (event: Event) => {
    setSelectedEvent(event);
    setShowEventDetails(true);
  };

  // Handle notification click
  const handleNotificationClick = (notification: EventNotification) => {
    markNotificationAsRead(notification.id);
    handleEventSelect(notification.event);
  };

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

  // Get unread notifications count
  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EventIcon />
          Events
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh Events">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export to CSV">
            <IconButton onClick={handleExport} disabled={loading}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Filters">
            <IconButton onClick={() => setShowFilters(!showFilters)}>
              <FilterIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={`Notifications ${unreadCount > 0 ? `(${unreadCount})` : ''}`}>
            <IconButton onClick={() => setShowNotifications(!showNotifications)}>
              <Badge badgeContent={unreadCount} color="error">
                {unreadCount > 0 ? <NotificationsActiveIcon /> : <NotificationsIcon />}
              </Badge>
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => {}}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      {eventStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <EventIcon color="primary" />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Total Events
                    </Typography>
                    <Typography variant="h5">
                      {eventStats.total_events.toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <WarningIcon color="error" />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Alarms
                    </Typography>
                    <Typography variant="h5">
                      {(eventStats.events_by_type.alarm || 0).toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SpeedIcon color="warning" />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Overspeed
                    </Typography>
                    <Typography variant="h5">
                      {(eventStats.events_by_type.deviceOverspeed || 0).toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircleIcon color="success" />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Geofences
                    </Typography>
                    <Typography variant="h5">
                      {((eventStats.events_by_type.geofenceEnter || 0) + 
                        (eventStats.events_by_type.geofenceExit || 0)).toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Main Content */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Events List" icon={<EventIcon />} />
            <Tab label="Recent Events" icon={<TimelineIcon />} />
            <Tab label="Event Types" icon={<CategoryIcon />} />
          </Tabs>
        </Box>

        {/* Events List Tab */}
        <TabPanel value={tabValue} index={0}>
          {/* Filters */}
          {showFilters && (
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Device</InputLabel>
                    <Select
                      value={filters.device_id || ''}
                      label="Device"
                      onChange={(e) => handleFilterChange({ device_id: e.target.value as number })}
                    >
                      <MenuItem value="">All Devices</MenuItem>
                      {devices.map((device) => (
                        <MenuItem key={device.id} value={device.id}>
                          {device.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Event Type</InputLabel>
                    <Select
                      value={filters.event_type || ''}
                      label="Event Type"
                      onChange={(e) => handleFilterChange({ event_type: e.target.value })}
                    >
                      <MenuItem value="">All Types</MenuItem>
                      {eventTypes.map((type) => (
                        <MenuItem key={type} value={type}>
                          {eventTypeInfo[type]?.name || type}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Start Time"
                    type="datetime-local"
                    value={filters.start_time || ''}
                    onChange={(e) => handleFilterChange({ start_time: e.target.value })}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    label="End Time"
                    type="datetime-local"
                    value={filters.end_time || ''}
                    onChange={(e) => handleFilterChange({ end_time: e.target.value })}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </Grid>
            </Box>
          )}

          {/* Events List */}
          <Box sx={{ p: 2 }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <Typography>Loading events...</Typography>
              </Box>
            ) : events.length === 0 ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <Typography color="textSecondary">No events found</Typography>
              </Box>
            ) : (
              <List>
                {events.map((event) => (
                  <ListItem
                    key={event.id}
                    button
                    onClick={() => handleEventSelect(event)}
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
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">
                            {eventTypeInfo[event.event_type]?.name || event.event_type}
                          </Typography>
                          <Chip
                            label={eventTypeInfo[event.event_type]?.severity || 'unknown'}
                            size="small"
                            color={getEventSeverityColor(event.event_type) as any}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Device: {event.device_name || `ID: ${event.device_id}`}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Time: {formatEventTime(event.event_time)}
                          </Typography>
                          {event.position_data && (
                            <Typography variant="body2" color="textSecondary">
                              Location: {event.position_data.latitude.toFixed(6)}, {event.position_data.longitude.toFixed(6)}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    
                    <ListItemSecondaryAction>
                      <IconButton edge="end" onClick={() => handleEventSelect(event)}>
                        <VisibilityIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}

            {/* Pagination */}
            {total > size && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Button
                  disabled={!hasPrev || loading}
                  onClick={() => handlePageChange(page - 1)}
                >
                  Previous
                </Button>
                <Typography sx={{ mx: 2, alignSelf: 'center' }}>
                  Page {page} of {Math.ceil(total / size)}
                </Typography>
                <Button
                  disabled={!hasNext || loading}
                  onClick={() => handlePageChange(page + 1)}
                >
                  Next
                </Button>
              </Box>
            )}
          </Box>
        </TabPanel>

        {/* Recent Events Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ p: 2 }}>
            {eventStats?.recent_events && eventStats.recent_events.length > 0 ? (
              <List>
                {eventStats.recent_events.map((event) => (
                  <ListItem
                    key={event.id}
                    button
                    onClick={() => handleEventSelect(event)}
                    sx={{
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1,
                    }}
                  >
                    <ListItemIcon>
                      {getEventIcon(event.event_type)}
                    </ListItemIcon>
                    
                    <ListItemText
                      primary={eventTypeInfo[event.event_type]?.name || event.event_type}
                      secondary={`${event.device_name || `Device ${event.device_id}`} - ${formatEventTime(event.event_time)}`}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography color="textSecondary" sx={{ textAlign: 'center', p: 4 }}>
                No recent events
              </Typography>
            )}
          </Box>
        </TabPanel>

        {/* Event Types Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ p: 2 }}>
            <Grid container spacing={2}>
              {Object.entries(eventTypeInfo).map(([type, info]) => (
                <Grid item xs={12} sm={6} md={4} key={type}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        {getEventIcon(type)}
                        <Typography variant="h6">{info.name}</Typography>
                      </Box>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                        {info.description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip
                          label={info.category}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                        <Chip
                          label={info.severity}
                          size="small"
                          color={getEventSeverityColor(type) as any}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        </TabPanel>
      </Paper>

      {/* Notifications Panel */}
      <Dialog
        open={showNotifications}
        onClose={() => setShowNotifications(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Event Notifications</Typography>
            <Box>
              <IconButton onClick={clearNotifications} size="small">
                <DeleteIcon />
              </IconButton>
              <IconButton onClick={() => setShowNotifications(false)} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {notifications.length === 0 ? (
            <Typography color="textSecondary" sx={{ textAlign: 'center', p: 2 }}>
              No notifications
            </Typography>
          ) : (
            <List>
              {notifications.map((notification) => (
                <ListItem
                  key={notification.id}
                  button
                  onClick={() => handleNotificationClick(notification)}
                  sx={{
                    backgroundColor: notification.read ? 'transparent' : 'action.hover',
                    borderRadius: 1,
                    mb: 1,
                  }}
                >
                  <ListItemIcon>
                    {getEventIcon(notification.event.event_type)}
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={eventTypeInfo[notification.event.event_type]?.name || notification.event.event_type}
                    secondary={`${notification.event.device_name || `Device ${notification.event.device_id}`} - ${formatEventTime(notification.event.event_time)}`}
                  />
                  
                  {!notification.read && (
                    <ListItemSecondaryAction>
                      <Chip label="New" size="small" color="error" />
                    </ListItemSecondaryAction>
                  )}
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
      </Dialog>

      {/* Event Details Dialog */}
      <Dialog
        open={showEventDetails}
        onClose={() => setShowEventDetails(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Event Details</Typography>
            <IconButton onClick={() => setShowEventDetails(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedEvent && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Event Type
                  </Typography>
                  <Typography variant="body1">
                    {eventTypeInfo[selectedEvent.event_type]?.name || selectedEvent.event_type}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Device
                  </Typography>
                  <Typography variant="body1">
                    {selectedEvent.device_name || `ID: ${selectedEvent.device_id}`}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Event Time
                  </Typography>
                  <Typography variant="body1">
                    {formatEventTime(selectedEvent.event_time)}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Severity
                  </Typography>
                  <Chip
                    label={eventTypeInfo[selectedEvent.event_type]?.severity || 'unknown'}
                    color={getEventSeverityColor(selectedEvent.event_type) as any}
                  />
                </Grid>
                
                {selectedEvent.position_data && (
                  <>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Latitude
                      </Typography>
                      <Typography variant="body1">
                        {selectedEvent.position_data.latitude.toFixed(6)}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Longitude
                      </Typography>
                      <Typography variant="body1">
                        {selectedEvent.position_data.longitude.toFixed(6)}
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Speed
                      </Typography>
                      <Typography variant="body1">
                        {selectedEvent.position_data.speed} km/h
                      </Typography>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Course
                      </Typography>
                      <Typography variant="body1">
                        {selectedEvent.position_data.course}°
                      </Typography>
                    </Grid>
                  </>
                )}
                
                {selectedEvent.attributes && Object.keys(selectedEvent.attributes).length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Attributes
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      {Object.entries(selectedEvent.attributes).map(([key, value]) => (
                        <Chip
                          key={key}
                          label={`${key}: ${value}`}
                          size="small"
                          sx={{ mr: 1, mb: 1 }}
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setShowEventDetails(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Events;
