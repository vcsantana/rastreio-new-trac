import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Badge,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  useTheme,
  useMediaQuery,
  Slide,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  NotificationsActive as NotificationsActiveIcon,
  Close as CloseIcon,
  Delete as DeleteIcon,
  MarkEmailRead as MarkReadIcon,
  Event as EventIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  DeviceHub as DeviceIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
  Speed as SpeedIcon,
  Settings as SettingsIcon,
  Category as CategoryIcon,
} from '@mui/icons-material';
import { EventNotification, EventTypeInfo } from '../../types/events';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface EventNotificationsProps {
  notifications: EventNotification[];
  eventTypeInfo: Record<string, EventTypeInfo>;
  onNotificationClick: (notification: EventNotification) => void;
  onMarkAsRead: (notificationId: string) => void;
  onClearAll: () => void;
  onClearRead: () => void;
  maxNotifications?: number;
  showBadge?: boolean;
  compact?: boolean;
}

const EventNotifications: React.FC<EventNotificationsProps> = ({
  notifications,
  eventTypeInfo,
  onNotificationClick,
  onMarkAsRead,
  onClearAll,
  onClearRead,
  maxNotifications = 10,
  showBadge = true,
  compact = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [open, setOpen] = useState(false);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Get unread notifications count
  const unreadCount = notifications.filter(n => !n.read).length;

  // Get recent notifications (limited by maxNotifications)
  const recentNotifications = notifications.slice(0, maxNotifications);

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

  // Format notification time
  const formatNotificationTime = (eventTime: string) => {
    try {
      return format(new Date(eventTime), 'dd/MM HH:mm', { locale: ptBR });
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

  // Handle notification click
  const handleNotificationClick = (notification: EventNotification) => {
    onNotificationClick(notification);
    if (!notification.read) {
      onMarkAsRead(notification.id);
    }
  };

  // Handle mark all as read
  const handleMarkAllAsRead = () => {
    notifications.forEach(notification => {
      if (!notification.read) {
        onMarkAsRead(notification.id);
      }
    });
    setSnackbarMessage('All notifications marked as read');
    setShowSnackbar(true);
  };

  // Handle clear all
  const handleClearAll = () => {
    onClearAll();
    setSnackbarMessage('All notifications cleared');
    setShowSnackbar(true);
  };

  // Handle clear read
  const handleClearRead = () => {
    onClearRead();
    setSnackbarMessage('Read notifications cleared');
    setShowSnackbar(true);
  };

  // Show notification badge
  const notificationButton = (
    <Tooltip title={`Event Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}>
      <IconButton onClick={() => setOpen(true)}>
        {showBadge ? (
          <Badge badgeContent={unreadCount} color="error">
            {unreadCount > 0 ? <NotificationsActiveIcon /> : <NotificationsIcon />}
          </Badge>
        ) : (
          unreadCount > 0 ? <NotificationsActiveIcon /> : <NotificationsIcon />
        )}
      </IconButton>
    </Tooltip>
  );

  if (compact) {
    return (
      <>
        {notificationButton}
        
        <Dialog
          open={open}
          onClose={() => setOpen(false)}
          maxWidth="sm"
          fullWidth
          fullScreen={isMobile}
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">Event Notifications</Typography>
              <Box>
                <IconButton onClick={handleClearAll} size="small">
                  <DeleteIcon />
                </IconButton>
                <IconButton onClick={() => setOpen(false)} size="small">
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
                {recentNotifications.map((notification) => (
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
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle2">
                            {eventTypeInfo[notification.event.event_type]?.name || notification.event.event_type}
                          </Typography>
                          <Chip
                            label={eventTypeInfo[notification.event.event_type]?.severity || 'unknown'}
                            size="small"
                            color={getEventSeverityColor(notification.event.event_type) as any}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            {notification.event.device_name || `Device ${notification.event.device_id}`}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {formatNotificationTime(notification.event.event_time)} ({formatRelativeTime(notification.event.event_time)})
                          </Typography>
                        </Box>
                      }
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
          
          <DialogActions>
            <Button onClick={handleMarkAllAsRead} disabled={unreadCount === 0}>
              Mark All Read
            </Button>
            <Button onClick={handleClearRead} disabled={notifications.filter(n => n.read).length === 0}>
              Clear Read
            </Button>
            <Button onClick={() => setOpen(false)}>
              Close
            </Button>
          </DialogActions>
        </Dialog>
      </>
    );
  }

  return (
    <Box>
      {notificationButton}
      
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth="md"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <NotificationsIcon />
              <Typography variant="h6">Event Notifications</Typography>
              {unreadCount > 0 && (
                <Chip
                  label={`${unreadCount} unread`}
                  size="small"
                  color="error"
                />
              )}
            </Box>
            <Box>
              <IconButton onClick={handleClearAll} size="small">
                <DeleteIcon />
              </IconButton>
              <IconButton onClick={() => setOpen(false)} size="small">
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {notifications.length === 0 ? (
            <Box sx={{ textAlign: 'center', p: 4 }}>
              <NotificationsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography color="textSecondary">
                No notifications
              </Typography>
            </Box>
          ) : (
            <List>
              {recentNotifications.map((notification) => (
                <ListItem
                  key={notification.id}
                  button
                  onClick={() => handleNotificationClick(notification)}
                  sx={{
                    backgroundColor: notification.read ? 'transparent' : 'action.hover',
                    borderRadius: 1,
                    mb: 1,
                    border: 1,
                    borderColor: 'divider',
                  }}
                >
                  <ListItemIcon>
                    {getEventIcon(notification.event.event_type)}
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <Typography variant="subtitle1">
                          {eventTypeInfo[notification.event.event_type]?.name || notification.event.event_type}
                        </Typography>
                        <Chip
                          label={eventTypeInfo[notification.event.event_type]?.severity || 'unknown'}
                          size="small"
                          color={getEventSeverityColor(notification.event.event_type) as any}
                        />
                        <Chip
                          label={eventTypeInfo[notification.event.event_type]?.category || 'unknown'}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <DeviceIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="textSecondary">
                            {notification.event.device_name || `Device ID: ${notification.event.device_id}`}
                          </Typography>
                        </Box>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                          <ScheduleIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="textSecondary">
                            {formatNotificationTime(notification.event.event_time)}
                          </Typography>
                          <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
                            ({formatRelativeTime(notification.event.event_time)})
                          </Typography>
                        </Box>
                        
                        {notification.event.position_data && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <LocationIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="textSecondary">
                              {notification.event.position_data.latitude.toFixed(6)}, {notification.event.position_data.longitude.toFixed(6)}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    }
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
        
        <DialogActions>
          <Button onClick={handleMarkAllAsRead} disabled={unreadCount === 0}>
            Mark All Read
          </Button>
          <Button onClick={handleClearRead} disabled={notifications.filter(n => n.read).length === 0}>
            Clear Read
          </Button>
          <Button onClick={() => setOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for feedback */}
      <Snackbar
        open={showSnackbar}
        autoHideDuration={3000}
        onClose={() => setShowSnackbar(false)}
      >
        <Alert
          onClose={() => setShowSnackbar(false)}
          severity="success"
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EventNotifications;
