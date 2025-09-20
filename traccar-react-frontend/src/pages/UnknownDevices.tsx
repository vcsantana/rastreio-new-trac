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
} from '@mui/icons-material';
import { useUnknownDevices, UnknownDevice } from '../hooks/useUnknownDevices';
import { useDevices } from '../hooks/useDevices';
import { useTranslation } from '../hooks/useTranslation';
import ConfirmDialog from '../components/common/ConfirmDialog';

const UnknownDevices: React.FC = () => {
  const {
    unknownDevices,
    stats,
    loading,
    error,
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
  const { t } = useTranslation();

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
      return `${diffDays} ${t('unknownDevices.daysAgo')}`;
    } else if (diffHours > 0) {
      return `${diffHours} ${t('unknownDevices.hoursAgo')}`;
    } else {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return `${diffMinutes} ${t('unknownDevices.minutesAgo')}`;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          {t('unknownDevices.title')} ({filteredDevices.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setFiltersExpanded(!filtersExpanded)}
            color={hasActiveFilters ? 'primary' : 'inherit'}
          >
            {t('unknownDevices.filters')} {hasActiveFilters && `(${[
              searchTerm && t('unknownDevices.searchDevices'),
              protocolFilter !== 'all' && t('unknownDevices.protocol'),
              portFilter !== 'all' && t('unknownDevices.port'),
              statusFilter !== 'all' && t('unknownDevices.status')
            ].filter(Boolean).length})`}
          </Button>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={clearFilters}
              size="small"
            >
              {t('unknownDevices.clear')}
            </Button>
          )}
        </Box>
      </Box>

      {/* Stats Cards */}
      {stats && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2, mb: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {stats.total_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('unknownDevices.totalUnknownDevices')}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main">
                {stats.registration_stats['false'] || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('unknownDevices.unregistered')}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {stats.registration_stats['true'] || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('unknownDevices.registered')}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {Object.keys(stats.protocol_stats).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('unknownDevices.protocols')}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Filters Section */}
      <Collapse in={filtersExpanded}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            {t('unknownDevices.filterUnknownDevices')}
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
            {/* Search */}
            <TextField
              fullWidth
              label={t('unknownDevices.searchDevices')}
              placeholder={t('unknownDevices.searchPlaceholder')}
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

            {/* Protocol Filter */}
            <FormControl fullWidth size="small">
              <InputLabel>{t('unknownDevices.protocol')}</InputLabel>
              <Select
                value={protocolFilter}
                label={t('unknownDevices.protocol')}
                onChange={(e) => setProtocolFilter(e.target.value)}
              >
                <MenuItem value="all">{t('unknownDevices.allProtocols')}</MenuItem>
                {uniqueProtocols.map(protocol => (
                  <MenuItem key={protocol} value={protocol}>
                    {protocol}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Port Filter */}
            <FormControl fullWidth size="small">
              <InputLabel>{t('unknownDevices.port')}</InputLabel>
              <Select
                value={portFilter}
                label={t('unknownDevices.port')}
                onChange={(e) => setPortFilter(e.target.value)}
              >
                <MenuItem value="all">{t('unknownDevices.allPorts')}</MenuItem>
                {uniquePorts.map(port => (
                  <MenuItem key={port} value={port.toString()}>
                    {port}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Status Filter */}
            <FormControl fullWidth size="small">
              <InputLabel>{t('unknownDevices.status')}</InputLabel>
              <Select
                value={statusFilter}
                label={t('unknownDevices.status')}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">{t('unknownDevices.allStatus')}</MenuItem>
                <MenuItem value="unregistered">{t('unknownDevices.unregistered')}</MenuItem>
                <MenuItem value="registered">{t('unknownDevices.registered')}</MenuItem>
              </Select>
            </FormControl>

            {/* Hours Filter */}
            <FormControl fullWidth size="small">
              <InputLabel>{t('unknownDevices.timePeriod')}</InputLabel>
              <Select
                value={hoursFilter}
                label={t('unknownDevices.timePeriod')}
                onChange={(e) => setHoursFilter(Number(e.target.value))}
              >
                <MenuItem value={1}>{t('unknownDevices.lastHour')}</MenuItem>
                <MenuItem value={24}>{t('unknownDevices.last24Hours')}</MenuItem>
                <MenuItem value={168}>{t('unknownDevices.lastWeek')}</MenuItem>
                <MenuItem value={720}>{t('unknownDevices.lastMonth')}</MenuItem>
              </Select>
            </FormControl>
          </Box>
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
              <TableCell>{t('unknownDevices.deviceId')}</TableCell>
              <TableCell>{t('unknownDevices.protocol')}</TableCell>
              <TableCell>{t('unknownDevices.port')}</TableCell>
              <TableCell>{t('unknownDevices.clientAddress')}</TableCell>
              <TableCell>{t('unknownDevices.status')}</TableCell>
              <TableCell>{t('unknownDevices.connections')}</TableCell>
              <TableCell>{t('unknownDevices.lastSeen')}</TableCell>
              <TableCell align="right">{t('unknownDevices.actions')}</TableCell>
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
                        {t('unknownDevices.firstSeen')} {formatDateTime(device.first_seen)}
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
                    label={device.is_registered ? t('unknownDevices.registered') : t('unknownDevices.unregistered')}
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
                  <Tooltip title={t('unknownDevices.viewDetails')}>
                    <IconButton
                      size="small"
                      onClick={() => handleViewDevice(device)}
                    >
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                  
                  {!device.is_registered && (
                    <>
                      <Tooltip title={t('unknownDevices.createDevice')}>
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => handleCreateDevice(device)}
                        >
                          <AddIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={t('unknownDevices.linkToDevice')}>
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
                  
                  <Tooltip title={t('unknownDevices.delete')}>
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
              ? t('unknownDevices.noDevicesMatchFilters')
              : t('unknownDevices.noDevicesFound')
            }
          </Typography>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              onClick={clearFilters}
              sx={{ mt: 2 }}
            >
              {t('unknownDevices.clearFilters')}
            </Button>
          )}
        </Paper>
      )}

      {/* View Device Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('unknownDevices.unknownDeviceDetails')}</DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.deviceId')}</Typography>
                  <Typography variant="body2">{selectedDevice.unique_id}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.protocol')}</Typography>
                  <Typography variant="body2">{selectedDevice.protocol}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.port')}</Typography>
                  <Typography variant="body2">{selectedDevice.port}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.clientAddress')}</Typography>
                  <Typography variant="body2">{selectedDevice.client_address || '-'}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.firstSeen')}</Typography>
                  <Typography variant="body2">{formatDateTime(selectedDevice.first_seen)}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.lastSeen')}</Typography>
                  <Typography variant="body2">{formatDateTime(selectedDevice.last_seen)}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.connectionCount')}</Typography>
                  <Typography variant="body2">{selectedDevice.connection_count}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.status')}</Typography>
                  <Chip
                    label={selectedDevice.is_registered ? t('unknownDevices.registered') : t('unknownDevices.unregistered')}
                    color={getStatusColor(selectedDevice.is_registered) as any}
                    size="small"
                  />
                </Box>
                {selectedDevice.raw_data && (
                  <Box sx={{ gridColumn: '1 / -1' }}>
                    <Typography variant="subtitle2" gutterBottom>{t('unknownDevices.rawData')}</Typography>
                    <Paper sx={{ p: 2, backgroundColor: 'grey.100' }}>
                      <Typography variant="body2" component="pre" sx={{ fontSize: '0.8rem' }}>
                        {selectedDevice.raw_data}
                      </Typography>
                    </Paper>
                  </Box>
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>{t('unknownDevices.close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Link Device Dialog */}
      <Dialog open={linkDialogOpen} onClose={() => setLinkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('unknownDevices.linkUnknownDevice')}</DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                {t('unknownDevices.linkUnknownDeviceDescription')} <strong>{selectedDevice.unique_id}</strong>:
              </Typography>
              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>{t('unknownDevices.selectDevice')}</InputLabel>
                <Select
                  value={selectedDeviceToLink || ''}
                  label={t('unknownDevices.selectDevice')}
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
                      {t('unknownDevices.noDevicesAvailable')}
                    </MenuItem>
                  )}
                </Select>
              </FormControl>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkDialogOpen(false)}>{t('unknownDevices.cancel')}</Button>
          <Button 
            onClick={handleConfirmLink} 
            variant="contained"
            disabled={!selectedDeviceToLink}
          >
            {t('unknownDevices.linkDevice')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Device Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{t('unknownDevices.createDeviceFromUnknown')}</DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                {t('unknownDevices.createDeviceDescription')} <strong>{selectedDevice.unique_id}</strong>:
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2, mt: 1 }}>
                <TextField
                  fullWidth
                  label={t('unknownDevices.deviceName')}
                  value={createDeviceData.name}
                  onChange={(e) => setCreateDeviceData(prev => ({ ...prev, name: e.target.value }))}
                  required
                />
                <TextField
                  fullWidth
                  label={t('unknownDevices.model')}
                  value={createDeviceData.model}
                  onChange={(e) => setCreateDeviceData(prev => ({ ...prev, model: e.target.value }))}
                />
                <TextField
                  fullWidth
                  label={t('unknownDevices.contact')}
                  value={createDeviceData.contact}
                  onChange={(e) => setCreateDeviceData(prev => ({ ...prev, contact: e.target.value }))}
                />
                <FormControl fullWidth>
                  <InputLabel>{t('unknownDevices.category')}</InputLabel>
                  <Select
                    value={createDeviceData.category}
                    label={t('unknownDevices.category')}
                    onChange={(e) => setCreateDeviceData(prev => ({ ...prev, category: e.target.value }))}
                  >
                    <MenuItem value="car">{t('unknownDevices.car')}</MenuItem>
                    <MenuItem value="truck">{t('unknownDevices.truck')}</MenuItem>
                    <MenuItem value="motorcycle">{t('unknownDevices.motorcycle')}</MenuItem>
                    <MenuItem value="van">{t('unknownDevices.van')}</MenuItem>
                    <MenuItem value="bus">{t('unknownDevices.bus')}</MenuItem>
                    <MenuItem value="boat">{t('unknownDevices.boat')}</MenuItem>
                    <MenuItem value="iphone">{t('unknownDevices.iphone')}</MenuItem>
                    <MenuItem value="android">{t('unknownDevices.android')}</MenuItem>
                    <MenuItem value="other">{t('unknownDevices.other')}</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  label={t('unknownDevices.phone')}
                  value={createDeviceData.phone}
                  onChange={(e) => setCreateDeviceData(prev => ({ ...prev, phone: e.target.value }))}
                />
                <TextField
                  fullWidth
                  label={t('unknownDevices.licensePlate')}
                  value={createDeviceData.license_plate}
                  onChange={(e) => setCreateDeviceData(prev => ({ ...prev, license_plate: e.target.value }))}
                />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>{t('unknownDevices.cancel')}</Button>
          <Button 
            onClick={handleConfirmCreate} 
            variant="contained"
            disabled={!createDeviceData.name}
          >
            {t('unknownDevices.createDevice')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        open={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        onConfirm={handleConfirmDelete}
        title={t('unknownDevices.deleteUnknownDevice')}
        message={`${t('unknownDevices.deleteConfirmation')} "${selectedDevice?.unique_id}"?`}
        confirmText={t('unknownDevices.delete')}
        severity="error"
      />
    </Box>
  );
};

export default UnknownDevices;
