import React, { useState, useMemo, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  Collapse,
} from '@mui/material';
import {
  Send as SendIcon,
  SendAndArchive as BulkSendIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { CommandDialog } from '../components/commands/CommandDialog';
import { BulkCommandDialog } from '../components/commands/BulkCommandDialog';
import { useCommands } from '../hooks/useCommands';
import { useDevices } from '../hooks/useDevices';
import { useTranslation } from '../hooks/useTranslation';

// Command status types
type CommandStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'cancelled';

interface Command {
  id: number;
  command_type: string;
  device_id: number;
  device_name?: string;
  status: CommandStatus;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  created_at: string;
  sent_at?: string;
  delivered_at?: string;
  parameters?: Record<string, any>;
  result?: string;
}

const Commands: React.FC = () => {
  const { commands, loading, error } = useCommands();
  const { devices } = useDevices();
  const { t } = useTranslation();

  // Dialog states
  const [commandDialogOpen, setCommandDialogOpen] = useState(false);
  const [bulkCommandDialogOpen, setBulkCommandDialogOpen] = useState(false);
  const [selectedCommand, setSelectedCommand] = useState<Command | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success');

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [deviceFilter, setDeviceFilter] = useState<string>('all');
  const [filtersExpanded, setFiltersExpanded] = useState(false);

  // Mock commands data for demonstration
  const mockCommands: Command[] = [
    {
      id: 1,
      command_type: 'engineStop',
      device_id: 1,
      device_name: 'Vehicle 001',
      status: 'delivered',
      priority: 'high',
      created_at: '2025-09-13T10:30:00Z',
      sent_at: '2025-09-13T10:30:05Z',
      delivered_at: '2025-09-13T10:30:15Z',
      parameters: { duration: 30 },
      result: 'Engine stopped successfully'
    },
    {
      id: 2,
      command_type: 'getLocation',
      device_id: 2,
      device_name: 'Vehicle 002',
      status: 'pending',
      priority: 'normal',
      created_at: '2025-09-13T11:15:00Z',
      parameters: {}
    },
    {
      id: 3,
      command_type: 'setSpeedLimit',
      device_id: 1,
      device_name: 'Vehicle 001',
      status: 'failed',
      priority: 'urgent',
      created_at: '2025-09-13T11:45:00Z',
      sent_at: '2025-09-13T11:45:10Z',
      parameters: { speed: 80 },
      result: 'Device not responding'
    }
  ];

  // Use mock data for now
  const allCommands = mockCommands;

  // Get unique values for filter options
  const uniqueDevices = useMemo(() => {
    return devices.map(d => ({ id: d.id, name: d.name }));
  }, [devices]);

  // Filter commands based on current filters
  const filteredCommands = useMemo(() => {
    return allCommands.filter(command => {
      // Search term filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = 
          command.command_type.toLowerCase().includes(searchLower) ||
          command.device_name?.toLowerCase().includes(searchLower) ||
          command.result?.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      // Status filter
      if (statusFilter !== 'all' && command.status !== statusFilter) {
        return false;
      }

      // Priority filter
      if (priorityFilter !== 'all' && command.priority !== priorityFilter) {
        return false;
      }

      // Device filter
      if (deviceFilter !== 'all' && command.device_id.toString() !== deviceFilter) {
        return false;
      }

      return true;
    });
  }, [allCommands, searchTerm, statusFilter, priorityFilter, deviceFilter]);

  // Clear all filters
  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setPriorityFilter('all');
    setDeviceFilter('all');
  };

  // Check if any filters are active
  const hasActiveFilters = searchTerm || statusFilter !== 'all' || priorityFilter !== 'all' || deviceFilter !== 'all';

  // Helper functions
  const getStatusColor = (status: CommandStatus) => {
    switch (status) {
      case 'delivered':
        return 'success';
      case 'sent':
        return 'info';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: CommandStatus) => {
    switch (status) {
      case 'delivered':
        return <SuccessIcon sx={{ fontSize: 16 }} />;
      case 'sent':
        return <SendIcon sx={{ fontSize: 16 }} />;
      case 'pending':
        return <PendingIcon sx={{ fontSize: 16 }} />;
      case 'failed':
        return <ErrorIcon sx={{ fontSize: 16 }} />;
      case 'cancelled':
        return <CancelIcon sx={{ fontSize: 16 }} />;
      default:
        return <PendingIcon sx={{ fontSize: 16 }} />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'normal':
        return 'info';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatDateTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('pt-BR');
    } catch {
      return dateString;
    }
  };

  // Event handlers
  const handleCommandSent = (command: any) => {
    setSnackbarMessage(t('commands.commandSentSuccess'));
    setSnackbarSeverity('success');
    setSnackbarOpen(true);
  };

  const handleBulkCommandsSent = (result: { created: number; failed: number }) => {
    if (result.failed === 0) {
      setSnackbarMessage(`${result.created} ${t('commands.commandsSentSuccess')}`);
      setSnackbarSeverity('success');
    } else {
      setSnackbarMessage(`${result.created} ${t('commands.commandsSentPartial')} ${result.failed}`);
      setSnackbarSeverity('warning');
    }
    setSnackbarOpen(true);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  const handleRefresh = () => {
    // Refresh commands - would call API here
    setSnackbarMessage(t('commands.commandsRefreshed'));
    setSnackbarSeverity('info');
    setSnackbarOpen(true);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          {t('commands.title')} ({filteredCommands.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setFiltersExpanded(!filtersExpanded)}
            color={hasActiveFilters ? 'primary' : 'inherit'}
          >
            {t('commands.filters')} {hasActiveFilters && `(${[
              searchTerm && t('commands.searchCommands'),
              statusFilter !== 'all' && t('commands.status'),
              priorityFilter !== 'all' && t('commands.priority'),
              deviceFilter !== 'all' && t('commands.device')
            ].filter(Boolean).length})`}
          </Button>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={clearFilters}
              size="small"
            >
              {t('commands.clear')}
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            {t('commands.refresh')}
          </Button>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={() => setCommandDialogOpen(true)}
            disabled={loading}
          >
            {t('commands.sendCommand')}
          </Button>
          <Button
            variant="outlined"
            startIcon={<BulkSendIcon />}
            onClick={() => setBulkCommandDialogOpen(true)}
            disabled={loading}
          >
            {t('commands.bulkSend')}
          </Button>
        </Box>
      </Box>

      {/* Filters Section */}
      <Collapse in={filtersExpanded}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            {t('commands.filterCommands')}
          </Typography>
          <Grid container spacing={2}>
            {/* Search */}
            <Grid item xs={12} md={4} component="div">
              <TextField
                fullWidth
                label={t('commands.searchCommands')}
                placeholder={t('commands.searchPlaceholder')}
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
            <Grid item xs={12} md={2} component="div">
              <FormControl fullWidth size="small">
                <InputLabel>{t('commands.status')}</InputLabel>
                <Select
                  value={statusFilter}
                  label={t('commands.status')}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">{t('commands.allStatus')}</MenuItem>
                  <MenuItem value="pending">{t('commands.pending')}</MenuItem>
                  <MenuItem value="sent">{t('commands.sent')}</MenuItem>
                  <MenuItem value="delivered">{t('commands.delivered')}</MenuItem>
                  <MenuItem value="failed">{t('commands.failed')}</MenuItem>
                  <MenuItem value="cancelled">{t('commands.cancelled')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Priority Filter */}
            <Grid item xs={12} md={2} component="div">
              <FormControl fullWidth size="small">
                <InputLabel>{t('commands.priority')}</InputLabel>
                <Select
                  value={priorityFilter}
                  label={t('commands.priority')}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                >
                  <MenuItem value="all">{t('commands.allPriorities')}</MenuItem>
                  <MenuItem value="urgent">{t('commands.urgent')}</MenuItem>
                  <MenuItem value="high">{t('commands.high')}</MenuItem>
                  <MenuItem value="normal">{t('commands.normal')}</MenuItem>
                  <MenuItem value="low">{t('commands.low')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Device Filter */}
            <Grid item xs={12} md={4} component="div">
              <FormControl fullWidth size="small">
                <InputLabel>{t('commands.device')}</InputLabel>
                <Select
                  value={deviceFilter}
                  label={t('commands.device')}
                  onChange={(e) => setDeviceFilter(e.target.value)}
                >
                  <MenuItem value="all">{t('commands.allDevices')}</MenuItem>
                  {uniqueDevices.map(device => (
                    <MenuItem key={device.id} value={device.id.toString()}>
                      {device.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
      </Collapse>

      {/* Quick Stats Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={3} component="div">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <SendIcon color="primary" />
                <Box>
                  <Typography variant="h6" color="primary">
                    {filteredCommands.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('commands.totalCommands')}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3} component="div">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <SuccessIcon color="success" />
                <Box>
                  <Typography variant="h6" color="success.main">
                    {filteredCommands.filter(c => c.status === 'delivered').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('commands.delivered')}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3} component="div">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <PendingIcon color="warning" />
                <Box>
                  <Typography variant="h6" color="warning.main">
                    {filteredCommands.filter(c => c.status === 'pending').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('commands.pending')}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3} component="div">
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <ErrorIcon color="error" />
                <Box>
                  <Typography variant="h6" color="error.main">
                    {filteredCommands.filter(c => c.status === 'failed').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('commands.failed')}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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
              <TableCell>{t('commands.commandType')}</TableCell>
              <TableCell>{t('commands.device')}</TableCell>
              <TableCell>{t('commands.status')}</TableCell>
              <TableCell>{t('commands.priority')}</TableCell>
              <TableCell>{t('commands.created')}</TableCell>
              <TableCell>{t('commands.sent')}</TableCell>
              <TableCell>{t('commands.result')}</TableCell>
              <TableCell align="right">{t('commands.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCommands.map((command) => (
              <TableRow key={command.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(command.status)}
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {command.command_type}
                      </Typography>
                      {command.parameters && Object.keys(command.parameters).length > 0 && (
                        <Typography variant="caption" color="text.secondary">
                          {Object.entries(command.parameters).map(([key, value]) => `${key}: ${value}`).join(', ')}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {command.device_name || `Device ${command.device_id}`}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={command.status}
                    color={getStatusColor(command.status) as any}
                    size="small"
                    icon={getStatusIcon(command.status)}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={command.priority}
                    color={getPriorityColor(command.priority) as any}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDateTime(command.created_at)}
                  </Typography>
                </TableCell>
                <TableCell>
                  {command.sent_at ? (
                    <Typography variant="body2">
                      {formatDateTime(command.sent_at)}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {command.result ? (
                    <Typography variant="body2" color={command.status === 'failed' ? 'error' : 'text.primary'}>
                      {command.result}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title={t('commands.resendCommand')}>
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => {
                        setSelectedCommand(command);
                        setCommandDialogOpen(true);
                      }}
                      disabled={loading || command.status === 'delivered'}
                    >
                      <SendIcon />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title={t('commands.viewDetails')}>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedCommand(command);
                        // Could open a details dialog here
                      }}
                      disabled={loading}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title={t('commands.cancelCommand')}>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => {
                        // Handle cancel command
                      }}
                      disabled={loading || command.status !== 'pending'}
                    >
                      <CancelIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredCommands.length === 0 && !loading && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 2 }}>
          <Typography variant="body1" color="text.secondary">
            {hasActiveFilters 
              ? t('commands.noCommandsMatchFilters')
              : t('commands.noCommandsFound')
            }
          </Typography>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              onClick={clearFilters}
              sx={{ mt: 2 }}
            >
              {t('commands.clearFilters')}
            </Button>
          )}
        </Paper>
      )}

      {/* Dialogs */}
      <CommandDialog
        open={commandDialogOpen}
        onClose={() => {
          setCommandDialogOpen(false);
          setSelectedCommand(null);
        }}
        deviceId={selectedCommand?.device_id}
        onCommandSent={handleCommandSent}
      />

      <BulkCommandDialog
        open={bulkCommandDialogOpen}
        onClose={() => setBulkCommandDialogOpen(false)}
        onCommandsSent={handleBulkCommandsSent}
      />

      {/* Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Commands;
