import React, { useState, useMemo } from 'react';
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  InputAdornment,
  Collapse,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Circle as StatusIcon,
  Block as DisableIcon,
  CheckCircle as EnableIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
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

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [protocolFilter, setProtocolFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [groupFilter, setGroupFilter] = useState<string>('all');
  const [filtersExpanded, setFiltersExpanded] = useState(false);

  // Get unique values for filter options
  const uniqueProtocols = useMemo(() => {
    const protocols = devices.map(d => d.protocol).filter(Boolean);
    return Array.from(new Set(protocols));
  }, [devices]);

  const uniqueCategories = useMemo(() => {
    const categories = devices.map(d => d.category).filter(Boolean);
    return Array.from(new Set(categories));
  }, [devices]);

  const uniqueGroups = useMemo(() => {
    const groups = devices.map(d => d.group_name).filter(Boolean);
    return Array.from(new Set(groups));
  }, [devices]);

  // Filter devices based on current filters
  const filteredDevices = useMemo(() => {
    return devices.filter(device => {
      // Search term filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = 
          device.name.toLowerCase().includes(searchLower) ||
          device.unique_id.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      // Status filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'disabled' && !device.disabled) return false;
        if (statusFilter === 'enabled' && device.disabled) return false;
        if (statusFilter === 'online' && (device.disabled || device.status !== 'online')) return false;
        if (statusFilter === 'offline' && (device.disabled || device.status !== 'offline')) return false;
      }

      // Protocol filter
      if (protocolFilter !== 'all' && device.protocol !== protocolFilter) {
        return false;
      }

      // Category filter
      if (categoryFilter !== 'all' && device.category !== categoryFilter) {
        return false;
      }

      // Group filter
      if (groupFilter !== 'all' && device.group_name !== groupFilter) {
        return false;
      }

      return true;
    });
  }, [devices, searchTerm, statusFilter, protocolFilter, categoryFilter, groupFilter]);

  // Clear all filters
  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setProtocolFilter('all');
    setCategoryFilter('all');
    setGroupFilter('all');
  };

  // Check if any filters are active
  const hasActiveFilters = searchTerm || statusFilter !== 'all' || protocolFilter !== 'all' || 
                          categoryFilter !== 'all' || groupFilter !== 'all';

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
          Devices ({filteredDevices.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setFiltersExpanded(!filtersExpanded)}
            color={hasActiveFilters ? 'primary' : 'inherit'}
          >
            Filters {hasActiveFilters && `(${[
              searchTerm && 'Search',
              statusFilter !== 'all' && 'Status',
              protocolFilter !== 'all' && 'Protocol',
              categoryFilter !== 'all' && 'Category',
              groupFilter !== 'all' && 'Group'
            ].filter(Boolean).length})`}
          </Button>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={clearFilters}
              size="small"
            >
              Clear
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddDevice}
            disabled={loading}
          >
            Add Device
          </Button>
        </Box>
      </Box>

      {/* Filters Section */}
      <Collapse in={filtersExpanded}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filter Devices
          </Typography>
          <Grid container spacing={2}>
            {/* Search */}
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search devices"
                placeholder="Search by name or unique ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                size="small"
              />
            </Grid>

            {/* Status Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="online">Online</MenuItem>
                  <MenuItem value="offline">Offline</MenuItem>
                  <MenuItem value="enabled">Enabled</MenuItem>
                  <MenuItem value="disabled">Disabled</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Protocol Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Protocol</InputLabel>
                <Select
                  value={protocolFilter}
                  label="Protocol"
                  onChange={(e) => setProtocolFilter(e.target.value)}
                >
                  <MenuItem value="all">All Protocols</MenuItem>
                  {uniqueProtocols.map(protocol => (
                    <MenuItem key={protocol} value={protocol}>
                      {protocol}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Category Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Category</InputLabel>
                <Select
                  value={categoryFilter}
                  label="Category"
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <MenuItem value="all">All Categories</MenuItem>
                  {uniqueCategories.map(category => (
                    <MenuItem key={category} value={category}>
                      {category}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Group Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Group</InputLabel>
                <Select
                  value={groupFilter}
                  label="Group"
                  onChange={(e) => setGroupFilter(e.target.value)}
                >
                  <MenuItem value="all">All Groups</MenuItem>
                  {uniqueGroups.map(group => (
                    <MenuItem key={group} value={group}>
                      {group}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
      </Collapse>

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
              <TableCell>Group</TableCell>
              <TableCell>Last Update</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredDevices.map((device) => (
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
                <TableCell>
                  {device.group_name ? (
                    <Chip
                      label={device.group_name}
                      variant="outlined"
                      size="small"
                      color="secondary"
                    />
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No Group
                    </Typography>
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

      {filteredDevices.length === 0 && !loading && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 2 }}>
          <Typography variant="body1" color="text.secondary">
            {hasActiveFilters 
              ? 'No devices match the current filters. Try adjusting your search criteria.'
              : 'No devices found. Click "Add Device" to get started.'
            }
          </Typography>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              onClick={clearFilters}
              sx={{ mt: 2 }}
            >
              Clear Filters
            </Button>
          )}
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
