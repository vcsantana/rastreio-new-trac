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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  Link as LinkIcon,
  Add as AddIcon,
  NetworkCheck as NetworkIcon,
  Schedule as ScheduleIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import { useUnknownDevices, UnknownDevice, UnknownDeviceFilters } from '../hooks/useUnknownDevices';
import { useDevices } from '../hooks/useDevices';
import ConfirmDialog from '../components/common/ConfirmDialog';

const UnknownDevices: React.FC = () => {
  const {
    unknownDevices,
    stats,
    loading,
    error,
    fetchUnknownDevices,
    updateUnknownDevice,
    deleteUnknownDevice,
    registerUnknownDevice,
    createDeviceFromUnknown,
  } = useUnknownDevices();

  // Debug logs
  console.log('UnknownDevices component rendered');
  console.log('unknownDevices:', unknownDevices);
  console.log('loading:', loading);
  console.log('error:', error);

  const { devices } = useDevices();

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [protocolFilter, setProtocolFilter] = useState<string>('all');
  const [portFilter, setPortFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [hoursFilter, setHoursFilter] = useState<number>(24);
  const [filtersExpanded, setFiltersExpanded] = useState(false);

  // Dialog states
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<UnknownDevice | null>(null);
  const [selectedDeviceToLink, setSelectedDeviceToLink] = useState<number | null>(null);
  const [createDeviceData, setCreateDeviceData] = useState({
    name: '',
    model: '',
    contact: '',
    category: 'other',
    phone: '',
    license_plate: '',
    group_id: undefined as number | undefined,
    person_id: undefined as number | undefined,
  });

  // Get unique values for filter options
  const uniqueProtocols = useMemo(() => {
    const protocols = unknownDevices.map(d => d.protocol).filter(Boolean);
    return Array.from(new Set(protocols));
  }, [unknownDevices]);

  const uniquePorts = useMemo(() => {
    const ports = unknownDevices.map(d => d.port).filter(Boolean);
    return Array.from(new Set(ports)).sort((a, b) => a - b);
  }, [unknownDevices]);

  // Filter devices based on current filters
  const filteredDevices = useMemo(() => {
    return unknownDevices.filter(device => {
      // Search term filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = 
          device.unique_id.toLowerCase().includes(searchLower) ||
          device.protocol.toLowerCase().includes(searchLower) ||
          (device.client_address && device.client_address.toLowerCase().includes(searchLower));
        if (!matchesSearch) return false;
      }

      // Protocol filter
      if (protocolFilter !== 'all' && device.protocol !== protocolFilter) {
        return false;
      }

      // Port filter
      if (portFilter !== 'all' && device.port.toString() !== portFilter) {
        return false;
      }

      // Status filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'registered' && !device.is_registered) return false;
        if (statusFilter === 'unregistered' && device.is_registered) return false;
      }

      return true;
    });
  }, [unknownDevices, searchTerm, protocolFilter, portFilter, statusFilter]);

  // Clear all filters
  const clearFilters = () => {
    setSearchTerm('');
    setProtocolFilter('all');
    setPortFilter('all');
    setStatusFilter('all');
    setHoursFilter(24);
  };

  // Check if any filters are active
  const hasActiveFilters = searchTerm || protocolFilter !== 'all' || portFilter !== 'all' || 
                          statusFilter !== 'all' || hoursFilter !== 24;

  const handleViewDevice = (device: UnknownDevice) => {
    setSelectedDevice(device);
    setViewDialogOpen(true);
  };

  const handleLinkDevice = (device: UnknownDevice) => {
    setSelectedDevice(device);
    setLinkDialogOpen(true);
  };

  const handleCreateDevice = (device: UnknownDevice) => {
    setSelectedDevice(device);
    setCreateDeviceData({
      name: `Device ${device.unique_id}`,
      model: '',
      contact: '',
      category: 'other',
      phone: '',
      license_plate: '',
      group_id: undefined,
      person_id: undefined,
    });
    setCreateDialogOpen(true);
  };

  const handleDeleteDevice = (device: UnknownDevice) => {
    setSelectedDevice(device);
    setConfirmDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (selectedDevice) {
      try {
        await deleteUnknownDevice(selectedDevice.id);
        setConfirmDialogOpen(false);
        setSelectedDevice(null);
      } catch (error) {
        console.error('Failed to delete unknown device:', error);
      }
    }
  };

  const handleConfirmLink = async () => {
    if (selectedDevice && selectedDeviceToLink) {
      try {
        await registerUnknownDevice(selectedDevice.id, selectedDeviceToLink);
        setLinkDialogOpen(false);
        setSelectedDevice(null);
        setSelectedDeviceToLink(null);
      } catch (error) {
        console.error('Failed to link unknown device:', error);
      }
    }
  };

  const handleConfirmCreate = async () => {
    if (selectedDevice) {
      try {
        await createDeviceFromUnknown(selectedDevice.id, createDeviceData);
        setCreateDialogOpen(false);
        setSelectedDevice(null);
        setCreateDeviceData({
          name: '',
          model: '',
          contact: '',
          category: 'other',
          phone: '',
          license_plate: '',
          group_id: undefined,
          person_id: undefined,
        });
      } catch (error) {
        console.error('Failed to create device from unknown device:', error);
      }
    }
  };

  const getStatusColor = (isRegistered: boolean) => {
    return isRegistered ? 'success' : 'warning';
  };

  const getStatusIcon = (isRegistered: boolean) => {
    return isRegistered ? <LinkIcon color="success" /> : <NetworkIcon color="warning" />;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Unknown Devices ({filteredDevices.length})
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
              protocolFilter !== 'all' && 'Protocol',
              portFilter !== 'all' && 'Port',
              statusFilter !== 'all' && 'Status'
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
        </Box>
      </Box>

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {stats.total_count}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Unknown Devices
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {stats.registration_stats['false'] || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Unregistered
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {stats.registration_stats['true'] || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Registered
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="info.main">
                  {Object.keys(stats.protocol_stats).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Protocols
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters Section */}
      <Collapse in={filtersExpanded}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filter Unknown Devices
          </Typography>
          <Grid container spacing={2}>
            {/* Search */}
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search devices"
                placeholder="Search by unique ID, protocol, or IP..."
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

            {/* Port Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Port</InputLabel>
                <Select
                  value={portFilter}
                  label="Port"
                  onChange={(e) => setPortFilter(e.target.value)}
                >
                  <MenuItem value="all">All Ports</MenuItem>
                  {uniquePorts.map(port => (
                    <MenuItem key={port} value={port.toString()}>
                      {port}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
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
                  <MenuItem value="unregistered">Unregistered</MenuItem>
                  <MenuItem value="registered">Registered</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Hours Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Time Period</InputLabel>
                <Select
                  value={hoursFilter}
                  label="Time Period"
                  onChange={(e) => setHoursFilter(Number(e.target.value))}
                >
                  <MenuItem value={1}>Last Hour</MenuItem>
                  <MenuItem value={24}>Last 24 Hours</MenuItem>
                  <MenuItem value={168}>Last Week</MenuItem>
                  <MenuItem value={720}>Last Month</MenuItem>
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
              <TableCell>Device ID</TableCell>
              <TableCell>Protocol</TableCell>
              <TableCell>Port</TableCell>
              <TableCell>Client Address</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Connections</TableCell>
              <TableCell>Last Seen</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredDevices.map((device) => (
              <TableRow key={device.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(device.is_registered)}
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {device.unique_id}
                        {device.parsed_data?.real_device_id && device.parsed_data.real_device_id !== device.unique_id && (
                          <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                            ({device.parsed_data.real_device_id})
                          </Typography>
                        )}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        First seen: {formatDateTime(device.first_seen)}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={device.protocol}
                    variant="outlined"
                    size="small"
                    color="primary"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={device.port}
                    variant="outlined"
                    size="small"
                    color="secondary"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {device.client_address || '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={device.is_registered ? 'Registered' : 'Unregistered'}
                    color={getStatusColor(device.is_registered) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {device.connection_count}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2">
                      {formatDateTime(device.last_seen)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {getTimeAgo(device.last_seen)}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => handleViewDevice(device)}
                    >
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                  
                  {!device.is_registered && (
                    <>
                      <Tooltip title="Create Device">
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => handleCreateDevice(device)}
                        >
                          <AddIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Link to Device">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleLinkDevice(device)}
                        >
                          <LinkIcon />
                        </IconButton>
                      </Tooltip>
                    </>
                  )}
                  
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteDevice(device)}
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
              ? 'No unknown devices match the current filters. Try adjusting your search criteria.'
              : 'No unknown devices found. Devices will appear here when they connect to protocol ports but are not registered in the system.'
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

      {/* View Device Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Unknown Device Details</DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Device ID</Typography>
                  <Typography variant="body2">{selectedDevice.unique_id}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Protocol</Typography>
                  <Typography variant="body2">{selectedDevice.protocol}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Port</Typography>
                  <Typography variant="body2">{selectedDevice.port}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Client Address</Typography>
                  <Typography variant="body2">{selectedDevice.client_address || '-'}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>First Seen</Typography>
                  <Typography variant="body2">{formatDateTime(selectedDevice.first_seen)}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Last Seen</Typography>
                  <Typography variant="body2">{formatDateTime(selectedDevice.last_seen)}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Connection Count</Typography>
                  <Typography variant="body2">{selectedDevice.connection_count}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>Status</Typography>
                  <Chip
                    label={selectedDevice.is_registered ? 'Registered' : 'Unregistered'}
                    color={getStatusColor(selectedDevice.is_registered) as any}
                    size="small"
                  />
                </Grid>
                {selectedDevice.raw_data && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>Raw Data</Typography>
                    <Paper sx={{ p: 2, backgroundColor: 'grey.100' }}>
                      <Typography variant="body2" component="pre" sx={{ fontSize: '0.8rem' }}>
                        {selectedDevice.raw_data}
                      </Typography>
                    </Paper>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Link Device Dialog */}
      <Dialog open={linkDialogOpen} onClose={() => setLinkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Link Unknown Device to Registered Device</DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                Link unknown device <strong>{selectedDevice.unique_id}</strong> to a registered device:
              </Typography>
              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>Select Device</InputLabel>
                <Select
                  value={selectedDeviceToLink || ''}
                  label="Select Device"
                  onChange={(e) => setSelectedDeviceToLink(Number(e.target.value))}
                >
                  {devices.length > 0 ? (
                    devices.map(device => (
                      <MenuItem key={device.id} value={device.id}>
                        {device.name} ({device.unique_id})
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem disabled>
                      No devices available
                    </MenuItem>
                  )}
                </Select>
              </FormControl>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleConfirmLink} 
            variant="contained"
            disabled={!selectedDeviceToLink}
          >
            Link Device
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Device Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Device from Unknown Device</DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                Create a new device from unknown device <strong>{selectedDevice.unique_id}</strong>:
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Device Name"
                    value={createDeviceData.name}
                    onChange={(e) => setCreateDeviceData(prev => ({ ...prev, name: e.target.value }))}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Model"
                    value={createDeviceData.model}
                    onChange={(e) => setCreateDeviceData(prev => ({ ...prev, model: e.target.value }))}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Contact"
                    value={createDeviceData.contact}
                    onChange={(e) => setCreateDeviceData(prev => ({ ...prev, contact: e.target.value }))}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={createDeviceData.category}
                      label="Category"
                      onChange={(e) => setCreateDeviceData(prev => ({ ...prev, category: e.target.value }))}
                    >
                      <MenuItem value="car">Car</MenuItem>
                      <MenuItem value="truck">Truck</MenuItem>
                      <MenuItem value="motorcycle">Motorcycle</MenuItem>
                      <MenuItem value="van">Van</MenuItem>
                      <MenuItem value="bus">Bus</MenuItem>
                      <MenuItem value="boat">Boat</MenuItem>
                      <MenuItem value="iphone">iPhone</MenuItem>
                      <MenuItem value="android">Android</MenuItem>
                      <MenuItem value="other">Other</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Phone"
                    value={createDeviceData.phone}
                    onChange={(e) => setCreateDeviceData(prev => ({ ...prev, phone: e.target.value }))}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="License Plate"
                    value={createDeviceData.license_plate}
                    onChange={(e) => setCreateDeviceData(prev => ({ ...prev, license_plate: e.target.value }))}
                  />
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleConfirmCreate} 
            variant="contained"
            disabled={!createDeviceData.name}
          >
            Create Device
          </Button>
        </DialogActions>
      </Dialog>

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        open={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        onConfirm={handleConfirmDelete}
        title="Delete Unknown Device"
        message={`Are you sure you want to delete the unknown device "${selectedDevice?.unique_id}"? This action cannot be undone.`}
        confirmText="Delete"
        severity="error"
      />
    </Box>
  );
};

export default UnknownDevices;
