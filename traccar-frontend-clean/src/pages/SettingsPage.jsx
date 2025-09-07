import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Box,
  Paper,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  Alert
} from '@mui/material';
import { useSelector } from 'react-redux';

const SettingsPage = () => {
  const user = useSelector((state) => state.auth.user);
  const [settings, setSettings] = useState({
    notifications: true,
    emailAlerts: false,
    smsAlerts: false,
    mapProvider: 'openstreetmap',
    language: 'en',
    timezone: 'UTC',
    units: 'metric'
  });

  const [serverSettings, setServerSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchServerSettings = async () => {
      try {
        const response = await fetch('/health');
        if (response.ok) {
          const data = await response.json();
          setServerSettings(data);
        }
      } catch (err) {
        console.error('Failed to fetch server settings:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchServerSettings();
  }, []);

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveSettings = () => {
    // Save settings logic
    console.log('Saving settings:', settings);
    // Here you would typically send the settings to the API
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              User Preferences
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notifications}
                    onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                  />
                }
                label="Enable Notifications"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.emailAlerts}
                    onChange={(e) => handleSettingChange('emailAlerts', e.target.checked)}
                  />
                }
                label="Email Alerts"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.smsAlerts}
                    onChange={(e) => handleSettingChange('smsAlerts', e.target.checked)}
                  />
                }
                label="SMS Alerts"
              />

              <TextField
                fullWidth
                label="Language"
                select
                value={settings.language}
                onChange={(e) => handleSettingChange('language', e.target.value)}
              >
                <option value="en">English</option>
                <option value="pt">Português</option>
                <option value="es">Español</option>
              </TextField>

              <TextField
                fullWidth
                label="Timezone"
                select
                value={settings.timezone}
                onChange={(e) => handleSettingChange('timezone', e.target.value)}
              >
                <option value="UTC">UTC</option>
                <option value="America/Sao_Paulo">São Paulo</option>
                <option value="America/New_York">New York</option>
              </TextField>

              <TextField
                fullWidth
                label="Units"
                select
                value={settings.units}
                onChange={(e) => handleSettingChange('units', e.target.value)}
              >
                <option value="metric">Metric</option>
                <option value="imperial">Imperial</option>
              </TextField>

              <Button
                variant="contained"
                onClick={handleSaveSettings}
                sx={{ mt: 2 }}
              >
                Save Settings
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Server Information
              </Typography>
              {serverSettings ? (
                <Box>
                  <Typography variant="body2">
                    <strong>Status:</strong> {serverSettings.status}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Version:</strong> {serverSettings.version}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Active Protocols:</strong> {serverSettings.protocols_active}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Cache:</strong> {serverSettings.cache?.connected ? 'Connected' : 'Disconnected'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Celery:</strong> {serverSettings.celery?.connected ? 'Connected' : 'Disconnected'}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Loading server information...
                </Typography>
              )}
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                API Information
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button 
                  variant="outlined" 
                  fullWidth
                  onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                >
                  API Documentation
                </Button>
                <Button 
                  variant="outlined" 
                  fullWidth
                  onClick={() => window.open('http://localhost:8000/health', '_blank')}
                >
                  Health Check
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SettingsPage;
