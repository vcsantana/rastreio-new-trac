import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Circle as StatusIcon,
  Block as DisableIcon,
  CheckCircle as EnableIcon,
} from '@mui/icons-material';
import { useDevices, Device } from '../hooks/useDevices';
import DeviceDialog from '../components/common/DeviceDialog';
import ConfirmDialog from '../components/common/ConfirmDialog';

const Devices: React.FC = () => {
  const {
    devices,
    loading,
    error,
    createDevice,
    updateDevice,
    deleteDevice,
    toggleDeviceStatus,
  } = useDevices();

  // Dialog states
  const [deviceDialogOpen, setDeviceDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [confirmAction, setConfirmAction] = useState<'delete' | 'disable' | 'enable'>('delete');

  const getStatusColor = (status: string, disabled?: boolean) => {
    if (disabled) return 'default';
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string, disabled?: boolean) => {
    if (disabled) {
      return <StatusIcon color="disabled" sx={{ fontSize: 16 }} />;
    }
    const color = status === 'online' ? 'success' : status === 'offline' ? 'error' : 'disabled';
    return <StatusIcon color={color} sx={{ fontSize: 16 }} />;
  };

  // Dialog handlers
  const handleAddDevice = () => {
    setDialogMode('create');
    setSelectedDevice(null);
    setDeviceDialogOpen(true);
  };

  const handleEditDevice = (device: Device) => {
    setDialogMode('edit');
    setSelectedDevice(device);
    setDeviceDialogOpen(true);
  };

  const handleDeleteDevice = (device: Device) => {
    setConfirmAction('delete');
    setSelectedDevice(device);
    setConfirmDialogOpen(true);
  };

  const handleToggleDeviceStatus = (device: Device) => {
    setConfirmAction(device.disabled ? 'enable' : 'disable');
    setSelectedDevice(device);
    setConfirmDialogOpen(true);
  };

  const handleSaveDevice = async (data: any) => {
    if (dialogMode === 'create') {
      return await createDevice(data);
    } else if (selectedDevice) {
      return await updateDevice(selectedDevice.id, data);
    }
    return false;
  };

  const handleConfirmAction = async () => {
    if (!selectedDevice) return;

    switch (confirmAction) {
      case 'delete':
        await deleteDevice(selectedDevice.id);
        break;
      case 'disable':
        await toggleDeviceStatus(selectedDevice.id, true);
        break;
      case 'enable':
        await toggleDeviceStatus(selectedDevice.id, false);
        break;
    }
  };

  const getConfirmDialogProps = () => {
    switch (confirmAction) {
      case 'delete':
        return {
          title: 'Delete Device',
          message: `Are you sure you want to delete "${selectedDevice?.name}"? This action cannot be undone.`,
          confirmText: 'Delete',
          severity: 'error' as const,
        };
      case 'disable':
        return {
          title: 'Disable Device',
          message: `Are you sure you want to disable "${selectedDevice?.name}"? The device will stop receiving GPS data.`,
          confirmText: 'Disable',
          severity: 'warning' as const,
        };
      case 'enable':
        return {
          title: 'Enable Device',
          message: `Are you sure you want to enable "${selectedDevice?.name}"? The device will start receiving GPS data again.`,
          confirmText: 'Enable',
          severity: 'info' as const,
        };
      default:
        return {
          title: 'Confirm Action',
          message: 'Are you sure?',
          confirmText: 'Confirm',
          severity: 'warning' as const,
        };
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Devices
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddDevice}
          disabled={loading}
        >
          Add Device
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Unique ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Protocol</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Last Update</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {devices.map((device) => (
              <TableRow key={device.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(device.status, device.disabled)}
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {device.name}
                      </Typography>
                      {device.disabled && (
                        <Typography variant="caption" color="text.secondary">
                          (Disabled)
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>{device.unique_id}</TableCell>
                <TableCell>
                  <Chip
                    label={device.disabled ? 'disabled' : device.status}
                    color={getStatusColor(device.status, device.disabled) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {device.protocol && (
                    <Chip
                      label={device.protocol}
                      variant="outlined"
                      size="small"
                    />
                  )}
                </TableCell>
                <TableCell>
                  {device.category && (
                    <Chip
                      label={device.category}
                      variant="outlined"
                      size="small"
                      color="info"
                    />
                  )}
                </TableCell>
                <TableCell>{device.last_update || 'Never'}</TableCell>
                <TableCell align="right">
                  <Tooltip title="Edit Device">
                    <IconButton
                      size="small"
                      onClick={() => handleEditDevice(device)}
                      disabled={loading}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title={device.disabled ? 'Enable Device' : 'Disable Device'}>
                    <IconButton
                      size="small"
                      color={device.disabled ? 'success' : 'warning'}
                      onClick={() => handleToggleDeviceStatus(device)}
                      disabled={loading}
                    >
                      {device.disabled ? <EnableIcon /> : <DisableIcon />}
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Delete Device">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteDevice(device)}
                      disabled={loading}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {devices.length === 0 && !loading && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 2 }}>
          <Typography variant="body1" color="text.secondary">
            No devices found. Click "Add Device" to get started.
          </Typography>
        </Paper>
      )}

      {/* Device Dialog */}
      <DeviceDialog
        open={deviceDialogOpen}
        onClose={() => setDeviceDialogOpen(false)}
        onSave={handleSaveDevice}
        device={selectedDevice}
        title={dialogMode === 'create' ? 'Add New Device' : 'Edit Device'}
      />

      {/* Confirm Dialog */}
      <ConfirmDialog
        open={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        onConfirm={handleConfirmAction}
        loading={loading}
        {...getConfirmDialogProps()}
      />
    </Box>
  );
};

export default Devices;
