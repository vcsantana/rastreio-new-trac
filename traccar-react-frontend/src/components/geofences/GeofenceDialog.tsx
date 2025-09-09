/**
 * Geofence Dialog Component
 * Dialog for creating, editing, and viewing geofences
 */

import React, { useState, useEffect } from 'react';
import {
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
  Grid,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Chip,
  Divider
} from '@mui/material';
import {
  Map as MapIcon,
  Info as InfoIcon,
  Settings as SettingsIcon,
  Circle as CircleIcon,
  Square as SquareIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { useGeofences } from '../../hooks/useGeofences';
import { Geofence, GeofenceCreate, GeofenceUpdate } from '../../types/geofences';
import GeofenceMap from './GeofenceMap';
import GeofenceGeometryEditor from './GeofenceGeometryEditor';

interface GeofenceDialogProps {
  open: boolean;
  mode: 'create' | 'edit' | 'view';
  geofence?: Geofence;
  onClose: () => void;
}

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
      id={`geofence-tabpanel-${index}`}
      aria-labelledby={`geofence-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const GeofenceDialog: React.FC<GeofenceDialogProps> = ({
  open,
  mode,
  geofence,
  onClose
}) => {
  const {
    loading,
    error,
    createGeofence,
    updateGeofence,
    clearError
  } = useGeofences();

  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState<GeofenceCreate>({
    name: '',
    description: '',
    geometry: '',
    type: 'polygon',
    disabled: false,
    attributes: ''
  });
  const [geometryData, setGeometryData] = useState<any>(null);
  const [isValid, setIsValid] = useState(false);

  // Reset form when dialog opens/closes or geofence changes
  useEffect(() => {
    if (open) {
      if (mode === 'create') {
        setFormData({
          name: '',
          description: '',
          geometry: '',
          type: 'polygon',
          disabled: false,
          attributes: ''
        });
        setGeometryData(null);
      } else if (geofence) {
        setFormData({
          name: geofence.name,
          description: geofence.description || '',
          geometry: geofence.geometry,
          type: geofence.type,
          disabled: geofence.disabled,
          attributes: geofence.attributes || ''
        });
        setGeometryData(geofence.geometry_data || null);
      }
      setTabValue(0);
      clearError();
    }
  }, [open, mode, geofence, clearError]);

  // Validate form
  useEffect(() => {
    const valid = formData.name.trim() !== '' && 
                  formData.geometry.trim() !== '' && 
                  geometryData !== null;
    setIsValid(valid);
  }, [formData, geometryData]);

  const handleInputChange = (field: keyof GeofenceCreate, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleGeometryChange = (geometry: string, geometryData: any) => {
    setFormData(prev => ({
      ...prev,
      geometry
    }));
    setGeometryData(geometryData);
  };

  const handleSubmit = async () => {
    if (!isValid) return;

    try {
      if (mode === 'create') {
        await createGeofence(formData);
      } else if (mode === 'edit' && geofence) {
        const updateData: GeofenceUpdate = {
          name: formData.name,
          description: formData.description,
          geometry: formData.geometry,
          type: formData.type,
          disabled: formData.disabled,
          attributes: formData.attributes
        };
        await updateGeofence(geofence.id, updateData);
      }
      onClose();
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'circle':
        return <CircleIcon />;
      case 'polygon':
        return <SquareIcon />;
      case 'polyline':
        return <TimelineIcon />;
      default:
        return <MapIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'circle':
        return 'primary';
      case 'polygon':
        return 'secondary';
      case 'polyline':
        return 'success';
      default:
        return 'default';
    }
  };

  const formatArea = (area?: number) => {
    if (!area) return 'N/A';
    
    if (area < 1000) {
      return `${area.toFixed(0)} m²`;
    } else if (area < 1000000) {
      return `${(area / 1000).toFixed(1)} km²`;
    } else {
      return `${(area / 1000000).toFixed(2)} km²`;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '600px' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <MapIcon />
          {mode === 'create' && 'Create Geofence'}
          {mode === 'edit' && 'Edit Geofence'}
          {mode === 'view' && 'View Geofence'}
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {error && (
          <Alert severity="error" sx={{ m: 2 }} onClose={clearError}>
            {error}
          </Alert>
        )}

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="geofence tabs">
            <Tab icon={<InfoIcon />} label="Information" />
            <Tab icon={<MapIcon />} label="Geometry" />
            <Tab icon={<SettingsIcon />} label="Settings" />
          </Tabs>
        </Box>

        {/* Information Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                disabled={mode === 'view'}
                required
                helperText="Unique name for the geofence"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                disabled={mode === 'view'}
                multiline
                rows={3}
                helperText="Optional description of the geofence"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={mode === 'view'}>
                <InputLabel>Type</InputLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => handleInputChange('type', e.target.value)}
                  label="Type"
                >
                  <MenuItem value="polygon">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SquareIcon />
                      Polygon
                    </Box>
                  </MenuItem>
                  <MenuItem value="circle">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CircleIcon />
                      Circle
                    </Box>
                  </MenuItem>
                  <MenuItem value="polyline">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TimelineIcon />
                      Polyline
                    </Box>
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.disabled}
                    onChange={(e) => handleInputChange('disabled', e.target.checked)}
                    disabled={mode === 'view'}
                  />
                }
                label="Disabled"
              />
            </Grid>

            {/* View mode - show additional info */}
            {mode === 'view' && geofence && (
              <>
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    ID
                  </Typography>
                  <Typography variant="body1">
                    {geofence.id}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Area
                  </Typography>
                  <Typography variant="body1">
                    {formatArea(geofence.area)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(geofence.created_at)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Last Updated
                  </Typography>
                  <Typography variant="body1">
                    {geofence.updated_at ? formatDate(geofence.updated_at) : 'Never'}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    label={geofence.disabled ? 'Disabled' : 'Active'}
                    color={geofence.disabled ? 'error' : 'success'}
                    size="small"
                    icon={getTypeIcon(geofence.type)}
                  />
                </Grid>
              </>
            )}
          </Grid>
        </TabPanel>

        {/* Geometry Tab */}
        <TabPanel value={tabValue} index={1}>
          <GeofenceGeometryEditor
            type={formData.type}
            geometry={formData.geometry}
            geometryData={geometryData}
            onChange={handleGeometryChange}
            disabled={mode === 'view'}
          />
        </TabPanel>

        {/* Settings Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Attributes (JSON)"
                value={formData.attributes}
                onChange={(e) => handleInputChange('attributes', e.target.value)}
                disabled={mode === 'view'}
                multiline
                rows={6}
                helperText="Additional attributes in JSON format"
                placeholder='{"color": "#ff0000", "priority": "high"}'
              />
            </Grid>
          </Grid>
        </TabPanel>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose}>
          {mode === 'view' ? 'Close' : 'Cancel'}
        </Button>
        {mode !== 'view' && (
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!isValid || loading}
            startIcon={loading ? <CircularProgress size={16} /> : null}
          >
            {mode === 'create' ? 'Create' : 'Save'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default GeofenceDialog;
