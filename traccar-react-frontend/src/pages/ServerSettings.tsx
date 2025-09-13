import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Snackbar,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Info as InfoIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Map as MapIcon,
  Language as LanguageIcon,
  Notifications as NotificationsIcon,
  RestartAlt as RestartIcon,
  Backup as BackupIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useServerSettings, ServerConfigUpdate } from '../hooks/useServerSettings';
import { useAuth } from '../contexts/AuthContext';

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
      id={`server-tabpanel-${index}`}
      aria-labelledby={`server-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ServerSettings: React.FC = () => {
  const { user } = useAuth();
  const {
    config,
    stats,
    health,
    info,
    loading,
    error,
    setError,
    updateServerConfig,
    restartServer,
    createBackup,
    getServerLogs,
    loadServerData,
  } = useServerSettings();

  const [activeTab, setActiveTab] = useState(0);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success');
  const [logs, setLogs] = useState<string[]>([]);
  const [logsDialogOpen, setLogsDialogOpen] = useState(false);
  const [restartDialogOpen, setRestartDialogOpen] = useState(false);
  const [backupDialogOpen, setBackupDialogOpen] = useState(false);

  // Form state for server configuration
  const [formData, setFormData] = useState<ServerConfigUpdate>({});

  // Check if user is admin
  if (!user?.is_admin) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Access denied. Admin privileges required to manage server settings.
        </Alert>
      </Box>
    );
  }

  // Update form data when config changes
  useEffect(() => {
    if (config) {
      setFormData({
        name: config.name,
        registration_enabled: config.registration_enabled,
        limit_commands: config.limit_commands,
        map_provider: config.map_provider,
        map_url: config.map_url,
        bing_key: config.bing_key,
        mapbox_key: config.mapbox_key,
        google_key: config.google_key,
        coordinate_format: config.coordinate_format,
        timezone: config.timezone,
        language: config.language,
        distance_unit: config.distance_unit,
        speed_unit: config.speed_unit,
        volume_unit: config.volume_unit,
        latitude: config.latitude,
        longitude: config.longitude,
        zoom: config.zoom,
        poi_layer: config.poi_layer,
        traffic_layer: config.traffic_layer,
      });
    }
  }, [config]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleFormChange = (field: keyof ServerConfigUpdate, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSaveConfig = async () => {
    const success = await updateServerConfig(formData);
    if (success) {
      setSnackbarMessage('Server configuration updated successfully');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } else {
      setSnackbarMessage('Failed to update server configuration');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  const handleRestartServer = async () => {
    const success = await restartServer();
    if (success) {
      setSnackbarMessage('Server restart initiated');
      setSnackbarSeverity('info');
      setSnackbarOpen(true);
      setRestartDialogOpen(false);
    } else {
      setSnackbarMessage('Failed to restart server');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  const handleCreateBackup = async () => {
    const result = await createBackup();
    if (result.success) {
      setSnackbarMessage(`Backup created successfully: ${result.filename}`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      setBackupDialogOpen(false);
    } else {
      setSnackbarMessage('Failed to create backup');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  const handleViewLogs = async () => {
    const serverLogs = await getServerLogs(100);
    setLogs(serverLogs);
    setLogsDialogOpen(true);
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'unhealthy':
        return 'error';
      default:
        return 'warning';
    }
  };

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'unhealthy':
        return <ErrorIcon color="error" />;
      default:
        return <WarningIcon color="warning" />;
    }
  };

  if (loading && !config) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Server Settings
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RestartIcon />}
            onClick={() => setRestartDialogOpen(true)}
            color="warning"
          >
            Restart Server
          </Button>
          <Button
            variant="outlined"
            startIcon={<BackupIcon />}
            onClick={() => setBackupDialogOpen(true)}
            color="primary"
          >
            Create Backup
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleViewLogs}
            color="info"
          >
            View Logs
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="server settings tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<SettingsIcon />} label="General" />
          <Tab icon={<MapIcon />} label="Map & Location" />
          <Tab icon={<LanguageIcon />} label="Localization" />
          <Tab icon={<SecurityIcon />} label="Security" />
          <Tab icon={<NotificationsIcon />} label="Notifications" />
          <Tab icon={<InfoIcon />} label="System Info" />
        </Tabs>

        {/* General Settings Tab */}
        <TabPanel value={activeTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Server Name"
                value={formData.name || ''}
                onChange={(e) => handleFormChange('name', e.target.value)}
                margin="normal"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Map Provider</InputLabel>
                <Select
                  value={formData.map_provider || 'openstreetmap'}
                  label="Map Provider"
                  onChange={(e) => handleFormChange('map_provider', e.target.value)}
                >
                  <MenuItem value="openstreetmap">OpenStreetMap</MenuItem>
                  <MenuItem value="mapbox">Mapbox</MenuItem>
                  <MenuItem value="bing">Bing Maps</MenuItem>
                  <MenuItem value="google">Google Maps</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.registration_enabled || false}
                    onChange={(e) => handleFormChange('registration_enabled', e.target.checked)}
                  />
                }
                label="Enable User Registration"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.limit_commands || false}
                    onChange={(e) => handleFormChange('limit_commands', e.target.checked)}
                  />
                }
                label="Limit Commands to Admin Users"
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={handleSaveConfig}
                disabled={loading}
                sx={{ mt: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Save Configuration'}
              </Button>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Map & Location Settings Tab */}
        <TabPanel value={activeTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Custom Map URL"
                value={formData.map_url || ''}
                onChange={(e) => handleFormChange('map_url', e.target.value)}
                margin="normal"
                helperText="Optional custom map tile server URL"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Default Latitude"
                type="number"
                value={formData.latitude || ''}
                onChange={(e) => handleFormChange('latitude', parseFloat(e.target.value) || undefined)}
                margin="normal"
                inputProps={{ step: 0.000001, min: -90, max: 90 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Default Longitude"
                type="number"
                value={formData.longitude || ''}
                onChange={(e) => handleFormChange('longitude', parseFloat(e.target.value) || undefined)}
                margin="normal"
                inputProps={{ step: 0.000001, min: -180, max: 180 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Default Zoom Level"
                type="number"
                value={formData.zoom || 6}
                onChange={(e) => handleFormChange('zoom', parseInt(e.target.value) || 6)}
                margin="normal"
                inputProps={{ min: 1, max: 20 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Bing Maps API Key"
                value={formData.bing_key || ''}
                onChange={(e) => handleFormChange('bing_key', e.target.value)}
                margin="normal"
                type="password"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Mapbox API Key"
                value={formData.mapbox_key || ''}
                onChange={(e) => handleFormChange('mapbox_key', e.target.value)}
                margin="normal"
                type="password"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Google Maps API Key"
                value={formData.google_key || ''}
                onChange={(e) => handleFormChange('google_key', e.target.value)}
                margin="normal"
                type="password"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.poi_layer || false}
                    onChange={(e) => handleFormChange('poi_layer', e.target.checked)}
                  />
                }
                label="Enable POI Layer"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.traffic_layer || false}
                    onChange={(e) => handleFormChange('traffic_layer', e.target.checked)}
                  />
                }
                label="Enable Traffic Layer"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Localization Settings Tab */}
        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={formData.timezone || 'UTC'}
                  label="Timezone"
                  onChange={(e) => handleFormChange('timezone', e.target.value)}
                >
                  <MenuItem value="UTC">UTC</MenuItem>
                  <MenuItem value="America/New_York">America/New_York</MenuItem>
                  <MenuItem value="America/Chicago">America/Chicago</MenuItem>
                  <MenuItem value="America/Denver">America/Denver</MenuItem>
                  <MenuItem value="America/Los_Angeles">America/Los_Angeles</MenuItem>
                  <MenuItem value="Europe/London">Europe/London</MenuItem>
                  <MenuItem value="Europe/Paris">Europe/Paris</MenuItem>
                  <MenuItem value="Asia/Tokyo">Asia/Tokyo</MenuItem>
                  <MenuItem value="Asia/Shanghai">Asia/Shanghai</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Language</InputLabel>
                <Select
                  value={formData.language || 'en'}
                  label="Language"
                  onChange={(e) => handleFormChange('language', e.target.value)}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="pt">Português</MenuItem>
                  <MenuItem value="es">Español</MenuItem>
                  <MenuItem value="fr">Français</MenuItem>
                  <MenuItem value="de">Deutsch</MenuItem>
                  <MenuItem value="it">Italiano</MenuItem>
                  <MenuItem value="ru">Русский</MenuItem>
                  <MenuItem value="zh">中文</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Distance Unit</InputLabel>
                <Select
                  value={formData.distance_unit || 'km'}
                  label="Distance Unit"
                  onChange={(e) => handleFormChange('distance_unit', e.target.value)}
                >
                  <MenuItem value="km">Kilometers</MenuItem>
                  <MenuItem value="mi">Miles</MenuItem>
                  <MenuItem value="nmi">Nautical Miles</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Speed Unit</InputLabel>
                <Select
                  value={formData.speed_unit || 'kmh'}
                  label="Speed Unit"
                  onChange={(e) => handleFormChange('speed_unit', e.target.value)}
                >
                  <MenuItem value="kmh">km/h</MenuItem>
                  <MenuItem value="mph">mph</MenuItem>
                  <MenuItem value="kn">knots</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Volume Unit</InputLabel>
                <Select
                  value={formData.volume_unit || 'l'}
                  label="Volume Unit"
                  onChange={(e) => handleFormChange('volume_unit', e.target.value)}
                >
                  <MenuItem value="l">Liters</MenuItem>
                  <MenuItem value="gal">Gallons (US)</MenuItem>
                  <MenuItem value="impgal">Gallons (Imperial)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Coordinate Format</InputLabel>
                <Select
                  value={formData.coordinate_format || 'decimal'}
                  label="Coordinate Format"
                  onChange={(e) => handleFormChange('coordinate_format', e.target.value)}
                >
                  <MenuItem value="decimal">Decimal Degrees</MenuItem>
                  <MenuItem value="ddm">Degrees Decimal Minutes</MenuItem>
                  <MenuItem value="dms">Degrees Minutes Seconds</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Security Settings Tab */}
        <TabPanel value={activeTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Access Control
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.registration_enabled || false}
                    onChange={(e) => handleFormChange('registration_enabled', e.target.checked)}
                  />
                }
                label="Allow User Registration"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.limit_commands || false}
                    onChange={(e) => handleFormChange('limit_commands', e.target.checked)}
                  />
                }
                label="Restrict Commands to Admin Users Only"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notifications Settings Tab */}
        <TabPanel value={activeTab} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Email Notifications
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info">
                Email notification settings will be implemented in a future update.
              </Alert>
            </Grid>
          </Grid>
        </TabPanel>

        {/* System Info Tab */}
        <TabPanel value={activeTab} index={5}>
          <Grid container spacing={3}>
            {/* Server Health */}
            {health && (
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Server Health
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      {getHealthStatusIcon(health.status)}
                      <Typography variant="body1" sx={{ ml: 1 }}>
                        Status: {health.status}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Version: {health.version}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Database: {health.database_status}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Uptime: {formatUptime(health.uptime)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Memory Usage: {health.memory_usage.toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      CPU Usage: {health.cpu_usage.toFixed(1)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Server Statistics */}
            {stats && (
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Statistics
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Total Users
                        </Typography>
                        <Typography variant="h4" color="primary">
                          {stats.total_users}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Total Devices
                        </Typography>
                        <Typography variant="h4" color="primary">
                          {stats.total_devices}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Online Devices
                        </Typography>
                        <Typography variant="h4" color="success.main">
                          {stats.online_devices}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Offline Devices
                        </Typography>
                        <Typography variant="h4" color="error.main">
                          {stats.offline_devices}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* System Information */}
            {info && (
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      System Information
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="text.secondary">
                          Server Name
                        </Typography>
                        <Typography variant="body1">
                          {info.name}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="text.secondary">
                          Version
                        </Typography>
                        <Typography variant="body1">
                          {info.version}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="text.secondary">
                          Operating System
                        </Typography>
                        <Typography variant="body1">
                          {info.os_name} {info.os_version} ({info.os_arch})
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="text.secondary">
                          CPU Cores
                        </Typography>
                        <Typography variant="body1">
                          {info.cpu_count}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="text.secondary">
                          Total Memory
                        </Typography>
                        <Typography variant="body1">
                          {info.memory_total ? formatBytes(info.memory_total) : 'N/A'}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="text.secondary">
                          Used Memory
                        </Typography>
                        <Typography variant="body1">
                          {info.memory_used ? formatBytes(info.memory_used) : 'N/A'}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        </TabPanel>
      </Paper>

      {/* Restart Server Dialog */}
      <Dialog open={restartDialogOpen} onClose={() => setRestartDialogOpen(false)}>
        <DialogTitle>Restart Server</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to restart the server? This will temporarily interrupt service.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRestartDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRestartServer} color="warning" variant="contained">
            Restart Server
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Backup Dialog */}
      <Dialog open={backupDialogOpen} onClose={() => setBackupDialogOpen(false)}>
        <DialogTitle>Create Backup</DialogTitle>
        <DialogContent>
          <Typography>
            Create a backup of the server database? This may take a few minutes.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBackupDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateBackup} color="primary" variant="contained">
            Create Backup
          </Button>
        </DialogActions>
      </Dialog>

      {/* Server Logs Dialog */}
      <Dialog open={logsDialogOpen} onClose={() => setLogsDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Server Logs</DialogTitle>
        <DialogContent>
          <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
            {logs.map((log, index) => (
              <Typography key={index} variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                {log}
              </Typography>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={() => setSnackbarOpen(false)} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ServerSettings;
