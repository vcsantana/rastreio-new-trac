import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Typography,
  Alert,
} from '@mui/material';
import { Device, CreateDeviceData, UpdateDeviceData } from '../../hooks/useDevices';
import { useGroups } from '../../hooks/useGroups';
import { usePersons } from '../../hooks/usePersons';

interface DeviceDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: CreateDeviceData | UpdateDeviceData) => Promise<boolean>;
  device?: Device | null;
  title: string;
}

const PROTOCOL_OPTIONS = [
  { value: 'suntech', label: 'Suntech' },
  { value: 'gt06', label: 'GT06' },
  { value: 'h02', label: 'H02' },
  { value: 'meiligao', label: 'Meiligao' },
  { value: 'teltonika', label: 'Teltonika' },
  { value: 'concox', label: 'Concox' },
  { value: 'queclink', label: 'Queclink' },
  { value: 'nmea', label: 'NMEA' },
];

const CATEGORY_OPTIONS = [
  { value: 'car', label: 'Car' },
  { value: 'truck', label: 'Truck' },
  { value: 'motorcycle', label: 'Motorcycle' },
  { value: 'van', label: 'Van' },
  { value: 'bus', label: 'Bus' },
  { value: 'boat', label: 'Boat' },
  { value: 'iphone', label: 'iPhone' },
  { value: 'android', label: 'Android' },
  { value: 'other', label: 'Other' },
];

const DeviceDialog: React.FC<DeviceDialogProps> = ({
  open,
  onClose,
  onSave,
  device,
  title,
}) => {
  const { groups, fetchGroups } = useGroups();
  const { persons, fetchPersons } = usePersons();
  const [formData, setFormData] = useState<CreateDeviceData>({
    name: '',
    unique_id: '',
    protocol: 'suntech',
    model: '',
    contact: '',
    category: 'car',
    phone: '',
    license_plate: '',
    group_id: undefined,
    person_id: undefined,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when dialog opens/closes or device changes
  useEffect(() => {
    if (open) {
      // Load groups and persons for selection
      fetchGroups();
      fetchPersons();
      
      if (device) {
        setFormData({
          name: device.name || '',
          unique_id: device.unique_id || '',
          protocol: device.protocol || 'suntech',
          model: device.model || '',
          contact: device.contact || '',
          category: device.category || 'car',
          phone: device.phone || '',
          license_plate: device.license_plate || '',
          group_id: device.group_id || undefined,
          person_id: device.person_id || undefined,
        });
      } else {
        setFormData({
          name: '',
          unique_id: '',
          protocol: 'suntech',
          model: '',
          contact: '',
          category: 'car',
          phone: '',
          license_plate: '',
          group_id: undefined,
          person_id: undefined,
        });
      }
      setError(null);
    }
  }, [open, device, fetchGroups, fetchPersons]);

  const handleInputChange = (field: keyof CreateDeviceData) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | any
  ) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = async () => {
    if (!formData.name.trim() || !formData.unique_id.trim()) {
      setError('Name and Unique ID are required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const success = await onSave(formData);
      if (success) {
        onClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save device');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ pt: 1 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Device Name"
                value={formData.name}
                onChange={handleInputChange('name')}
                required
                disabled={loading}
                helperText="A friendly name for the device"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Unique ID"
                value={formData.unique_id}
                onChange={handleInputChange('unique_id')}
                required
                disabled={loading}
                helperText="Unique identifier from the GPS device"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={loading}>
                <InputLabel>Protocol</InputLabel>
                <Select
                  value={formData.protocol}
                  label="Protocol"
                  onChange={handleInputChange('protocol')}
                >
                  {PROTOCOL_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={loading}>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  label="Category"
                  onChange={handleInputChange('category')}
                >
                  {CATEGORY_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Model"
                value={formData.model}
                onChange={handleInputChange('model')}
                disabled={loading}
                helperText="Device model (optional)"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Contact"
                value={formData.contact}
                onChange={handleInputChange('contact')}
                disabled={loading}
                helperText="Contact person (optional)"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={handleInputChange('phone')}
                disabled={loading}
                helperText="Phone number (optional)"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="License Plate"
                value={formData.license_plate}
                onChange={handleInputChange('license_plate')}
                disabled={loading}
                helperText="Vehicle license plate (optional)"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={loading}>
                <InputLabel>Group</InputLabel>
                <Select
                  value={formData.group_id || ''}
                  label="Group"
                  onChange={handleInputChange('group_id')}
                >
                  <MenuItem value="">
                    <em>No Group</em>
                  </MenuItem>
                  {groups.map((group) => (
                    <MenuItem key={group.id} value={group.id}>
                      {group.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={loading}>
                <InputLabel>Person</InputLabel>
                <Select
                  value={formData.person_id || ''}
                  label="Person"
                  onChange={handleInputChange('person_id')}
                >
                  <MenuItem value="">
                    <em>No Person</em>
                  </MenuItem>
                  {persons.map((person) => (
                    <MenuItem key={person.id} value={person.id}>
                      {person.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading}
        >
          {loading ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeviceDialog;
