import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Badge,
  Alert,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Switch,
  FormControlLabel,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Tooltip,
  Divider,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Checkbox
} from '@mui/material';
import {
  Warning,
  Error,
  CheckCircle,
  Phone,
  GpsFixed,
  BatteryAlert,
  DirectionsCar,
  Refresh,
  FilterList,
  NotificationsActive,
  Schedule,
  Star,
  Settings,
  LocationOn,
  Speed,
  Navigation,
  Power,
  SignalCellular4Bar,
  SignalCellularOff,
  PriorityHigh,
  Person,
  Edit,
  GroupWork
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useDevices } from '../hooks/useDevices';

// Types
interface ClientMonitoringSummary {
  total_devices: number;
  online_count: number;
  offline_count: number;
  unknown_count: number;
  critical_count: number;
  delinquent_count: number;
  test_devices: number;
  lost_devices: number;
  active_alerts: number;
  recent_sos: number;
  battery_alerts: number;
  communication_alerts: number;
}

interface MonitoringDevice {
  id: number;
  name: string;
  unique_id: string;
  status: 'online' | 'offline' | 'unknown';
  client_code?: string;
  client_status: 'active' | 'delinquent' | 'test' | 'lost' | 'removal';
  priority_level: number;
  fidelity_score: number;
  communication_status: {
    status: string;
    color: string;
    minutes_ago: number;
  };
  is_critical: boolean;
  client_type_display: string;
  priority_display: string;
  person_name?: string;
  group_name?: string;
  latitude?: number;
  longitude?: number;
  speed?: number;
  course?: number;
  ignition?: boolean;
  minutes_since_update?: number;
  has_sos_alert: boolean;
  has_battery_alert: boolean;
  has_communication_alert: boolean;
}

// Stats Card Component
const StatsCard: React.FC<{
  title: string;
  value: number;
  subtitle?: string;
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  onClick?: () => void;
}> = ({ title, value, subtitle, icon, color, onClick }) => {
  const theme = useTheme();
  
  return (
    <Card 
      sx={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s',
        '&:hover': onClick ? { transform: 'translateY(-2px)' } : {}
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h4" color={`${color}.main`} fontWeight="bold">
              {value}
            </Typography>
            <Typography variant="h6" color="textPrimary">
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Avatar sx={{ bgcolor: `${color}.main`, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );
};

// Device List Item Component
const DeviceListItem: React.FC<{
  device: MonitoringDevice;
  onDeviceClick: (device: MonitoringDevice) => void;
  selected: boolean;
  onToggleSelection: (deviceId: number) => void;
}> = ({ device, onDeviceClick, selected, onToggleSelection }) => {
  const theme = useTheme();
  
  const getStatusColor = (commStatus: string) => {
    switch (commStatus) {
      case 'green': return '#4caf50';
      case 'yellow': return '#ff9800';
      case 'orange': return '#ff5722';
      case 'red': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getClientCodeColor = (code?: string) => {
    if (!code) return 'default';
    if (code === '#16') return 'error';
    if (code === '#13') return 'warning';
    if (code === '#14') return 'error';
    return 'default';
  };

  const formatTimeAgo = (minutes?: number) => {
    if (!minutes) return 'Agora';
    if (minutes < 60) return `${minutes}min`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h`;
    return `${Math.floor(minutes / 1440)}d`;
  };

  return (
    <ListItem
      sx={{
        mb: 1,
        border: device.is_critical ? `2px solid ${theme.palette.error.main}` : '1px solid #e0e0e0',
        borderRadius: 1,
        backgroundColor: device.is_critical ? '#ffebee' : 'white',
        '&:hover': {
          backgroundColor: device.is_critical ? '#ffcdd2' : '#f5f5f5',
        }
      }}
    >
      <ListItemIcon>
        <Checkbox
          checked={selected}
          onChange={(e) => {
            e.stopPropagation();
            onToggleSelection(device.id);
          }}
        />
      </ListItemIcon>

      <ListItemIcon>
        <Box display="flex" flexDirection="column" alignItems="center">
          {/* Status Indicator */}
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: '50%',
              backgroundColor: getStatusColor(device.communication_status.color),
              mb: 0.5
            }}
          />
          {/* Priority Level */}
          {device.priority_level <= 2 && (
            <PriorityHigh color="error" fontSize="small" />
          )}
        </Box>
      </ListItemIcon>

      <ListItemText
        onClick={() => onDeviceClick(device)}
        sx={{ cursor: 'pointer' }}
        primary={
          <Box display="flex" alignItems="center" gap={1}>
            {/* Client Code */}
            {device.client_code && (
              <Chip
                label={device.client_code}
                size="small"
                color={getClientCodeColor(device.client_code) as any}
                sx={{ fontSize: '0.75rem', height: 20 }}
              />
            )}
            
            {/* Device Name */}
            <Typography variant="subtitle1" fontWeight="bold">
              {device.name}
            </Typography>
            
            {/* Alerts */}
            {device.has_sos_alert && <Error color="error" fontSize="small" />}
            {device.has_battery_alert && <BatteryAlert color="warning" fontSize="small" />}
            {device.has_communication_alert && <SignalCellularOff color="error" fontSize="small" />}
          </Box>
        }
        secondary={
          <Box>
            <Typography variant="body2" color="textSecondary">
              {device.client_type_display} • {device.priority_display}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {device.person_name || 'Sem responsável'} • {formatTimeAgo(device.minutes_since_update)}
            </Typography>
            {device.ignition !== undefined && (
              <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                <Power 
                  fontSize="small" 
                  color={device.ignition ? "success" : "disabled"} 
                />
                <Typography variant="caption">
                  Ignição {device.ignition ? 'Ligada' : 'Desligada'}
                </Typography>
                {device.speed !== undefined && (
                  <>
                    <Speed fontSize="small" color="action" />
                    <Typography variant="caption">
                      {Math.round((device.speed || 0) * 1.852)} km/h
                    </Typography>
                  </>
                )}
              </Box>
            )}
          </Box>
        }
      />

      {/* Fidelity Score */}
      <Box display="flex" flexDirection="column" alignItems="center">
        <Box display="flex" alignItems="center">
          {[...Array(5)].map((_, i) => (
            <Star
              key={i}
              fontSize="small"
              color={i < (device.fidelity_score || 0) ? "warning" : "disabled"}
            />
          ))}
        </Box>
        <Typography variant="caption" color="textSecondary">
          Fidelidade
        </Typography>
      </Box>
    </ListItem>
  );
};

// Main Component
const ClientMonitoringDashboard: React.FC = () => {
  const theme = useTheme();
  const { devices, loading: devicesLoading, fetchDevices } = useDevices();
  
  // State
  const [summary, setSummary] = useState<ClientMonitoringSummary | null>(null);
  const [monitoringDevices, setMonitoringDevices] = useState<MonitoringDevice[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [clientFilter, setClientFilter] = useState('all');
  const [priorityOnly, setPriorityOnly] = useState(false);
  const [communicationFilter, setCommunicationFilter] = useState('all');
  
  // Dialog states
  const [selectedDevice, setSelectedDevice] = useState<MonitoringDevice | null>(null);
  const [deviceDialogOpen, setDeviceDialogOpen] = useState(false);
  const [bulkEditDialogOpen, setBulkEditDialogOpen] = useState(false);
  const [selectedDevices, setSelectedDevices] = useState<number[]>([]);

  // Fetch data
  const fetchMonitoringData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch summary
      const summaryResponse = await fetch('/api/client-monitoring/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const summaryData = await summaryResponse.json();
      setSummary(summaryData);

      // Fetch devices
      const params = new URLSearchParams();
      if (clientFilter !== 'all') params.append('client_filter', clientFilter);
      if (priorityOnly) params.append('priority_only', 'true');
      if (communicationFilter !== 'all') params.append('communication_status', communicationFilter);
      
      const devicesResponse = await fetch(`/api/client-monitoring/devices?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const devicesData = await devicesResponse.json();
      setMonitoringDevices(devicesData);
      
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
    } finally {
      setLoading(false);
    }
  }, [clientFilter, priorityOnly, communicationFilter]);

  useEffect(() => {
    fetchMonitoringData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchMonitoringData, 30000);
    return () => clearInterval(interval);
  }, [fetchMonitoringData]);

  const handleDeviceClick = (device: MonitoringDevice) => {
    setSelectedDevice(device);
    setDeviceDialogOpen(true);
  };

  const handleFilterChange = (filterType: string, value: any) => {
    switch (filterType) {
      case 'client':
        setClientFilter(value);
        break;
      case 'priority':
        setPriorityOnly(value);
        break;
      case 'communication':
        setCommunicationFilter(value);
        break;
    }
  };

  const handleBulkUpdate = async (updates: {
    client_code?: string;
    client_status?: string;
    priority_level?: number;
    fidelity_score?: number;
    notes?: string;
  }) => {
    try {
      const promises = selectedDevices.map(deviceId =>
        fetch(`/api/client-monitoring/devices/${deviceId}/client-info`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(updates)
        })
      );

      await Promise.all(promises);
      
      // Refresh data
      await fetchMonitoringData();
      
      // Clear selection
      setSelectedDevices([]);
      setBulkEditDialogOpen(false);
      
      console.log('Bulk update completed successfully');
    } catch (error) {
      console.error('Error in bulk update:', error);
    }
  };

  const toggleDeviceSelection = (deviceId: number) => {
    setSelectedDevices(prev => 
      prev.includes(deviceId) 
        ? prev.filter(id => id !== deviceId)
        : [...prev, deviceId]
    );
  };

  if (loading && !summary) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          🏢 Central de Monitoramento - Protege Express
        </Typography>
        <Box>
          <Tooltip title="Atualizar dados">
            <IconButton onClick={fetchMonitoringData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <StatsCard
            title="Dispositivos Totais"
            value={summary?.total_devices || 0}
            subtitle={`${summary?.online_count || 0} online`}
            icon={<GpsFixed />}
            color="primary"
          />
        </Grid>
        
        <Grid item xs={12} md={3}>
          <StatsCard
            title="Situações Críticas"
            value={summary?.critical_count || 0}
            subtitle="Requer atenção imediata"
            icon={<Warning />}
            color="error"
            onClick={() => handleFilterChange('priority', true)}
          />
        </Grid>
        
        <Grid item xs={12} md={3}>
          <StatsCard
            title="Inadimplentes"
            value={summary?.delinquent_count || 0}
            subtitle="Clientes em atraso"
            icon={<Error />}
            color="warning"
            onClick={() => handleFilterChange('client', 'delinquent')}
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <StatsCard
            title="Alertas Ativos"
            value={summary?.active_alerts || 0}
            subtitle="Comunicação, SOS, Bateria"
            icon={<NotificationsActive />}
            color="info"
          />
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          <FilterList /> Filtros Inteligentes
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Tipo de Cliente</InputLabel>
              <Select
                value={clientFilter}
                label="Tipo de Cliente"
                onChange={(e) => handleFilterChange('client', e.target.value)}
              >
                <MenuItem value="all">Todos os clientes</MenuItem>
                <MenuItem value="active">Somente ativos</MenuItem>
                <MenuItem value="delinquent">Somente inadimplentes</MenuItem>
                <MenuItem value="test">Equipamentos de teste</MenuItem>
                <MenuItem value="lost">Equipamentos perdidos</MenuItem>
                <MenuItem value="removal">Somente remoção</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Comunicação</InputLabel>
              <Select
                value={communicationFilter}
                label="Comunicação"
                onChange={(e) => handleFilterChange('communication', e.target.value)}
              >
                <MenuItem value="all">Todos</MenuItem>
                <MenuItem value="excellent">Excelente (0-10min)</MenuItem>
                <MenuItem value="normal">Normal (11-45min)</MenuItem>
                <MenuItem value="attention">Atenção (46min-2h)</MenuItem>
                <MenuItem value="critical">Crítico (+2h)</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={3}>
            <FormControlLabel
              control={
                <Switch
                  checked={priorityOnly}
                  onChange={(e) => handleFilterChange('priority', e.target.checked)}
                />
              }
              label="Apenas Prioritários"
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <Box display="flex" gap={1}>
              <Button
                variant="outlined"
                onClick={() => {
                  setClientFilter('all');
                  setPriorityOnly(false);
                  setCommunicationFilter('all');
                }}
              >
                Limpar Filtros
              </Button>
              
              {selectedDevices.length > 0 && (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<Edit />}
                  onClick={() => setBulkEditDialogOpen(true)}
                >
                  Editar ({selectedDevices.length})
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Device List */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          📋 Lista Priorizada de Dispositivos ({monitoringDevices.length})
        </Typography>
        
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : (
          <List sx={{ maxHeight: '600px', overflow: 'auto' }}>
            {monitoringDevices.map((device) => (
              <DeviceListItem
                key={device.id}
                device={device}
                onDeviceClick={handleDeviceClick}
                selected={selectedDevices.includes(device.id)}
                onToggleSelection={toggleDeviceSelection}
              />
            ))}
            {monitoringDevices.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography color="textSecondary">
                  Nenhum dispositivo encontrado com os filtros selecionados
                </Typography>
              </Box>
            )}
          </List>
        )}
      </Paper>

      {/* Device Details Dialog */}
      <Dialog
        open={deviceDialogOpen}
        onClose={() => setDeviceDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Detalhes do Dispositivo - {selectedDevice?.name}
        </DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Informações Básicas</Typography>
                <Typography>ID: {selectedDevice.unique_id}</Typography>
                <Typography>Status: {selectedDevice.status}</Typography>
                <Typography>Tipo: {selectedDevice.client_type_display}</Typography>
                <Typography>Prioridade: {selectedDevice.priority_display}</Typography>
                {selectedDevice.person_name && (
                  <Typography>Responsável: {selectedDevice.person_name}</Typography>
                )}
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Localização e Status</Typography>
                {selectedDevice.latitude && selectedDevice.longitude && (
                  <Typography>
                    Coordenadas: {selectedDevice.latitude.toFixed(6)}, {selectedDevice.longitude.toFixed(6)}
                  </Typography>
                )}
                {selectedDevice.speed !== undefined && (
                  <Typography>
                    Velocidade: {Math.round((selectedDevice.speed || 0) * 1.852)} km/h
                  </Typography>
                )}
                {selectedDevice.ignition !== undefined && (
                  <Typography>
                    Ignição: {selectedDevice.ignition ? 'Ligada' : 'Desligada'}
                  </Typography>
                )}
                <Typography>
                  Última comunicação: {selectedDevice.minutes_since_update ? 
                    `${selectedDevice.minutes_since_update} min atrás` : 'Agora'}
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeviceDialogOpen(false)}>Fechar</Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Edit Dialog */}
      <Dialog
        open={bulkEditDialogOpen}
        onClose={() => setBulkEditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <GroupWork /> Editar Dispositivos em Lote ({selectedDevices.length} selecionados)
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Código do Cliente</InputLabel>
                <Select
                  defaultValue=""
                  label="Código do Cliente"
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value) {
                      handleBulkUpdate({ client_code: value });
                    }
                  }}
                >
                  <MenuItem value="">Sem código</MenuItem>
                  <MenuItem value="#16">
                    <Chip label="#16" color="error" size="small" sx={{ mr: 1 }} />
                    Cliente Inadimplente
                  </MenuItem>
                  <MenuItem value="#13">
                    <Chip label="#13" color="warning" size="small" sx={{ mr: 1 }} />
                    Equipamento de Teste
                  </MenuItem>
                  <MenuItem value="#14">
                    <Chip label="#14" color="error" size="small" sx={{ mr: 1 }} />
                    Equipamento Perdido
                  </MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Status do Cliente</InputLabel>
                <Select
                  defaultValue=""
                  label="Status do Cliente"
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value) {
                      handleBulkUpdate({ client_status: value });
                    }
                  }}
                >
                  <MenuItem value="active">Ativo</MenuItem>
                  <MenuItem value="delinquent">Inadimplente</MenuItem>
                  <MenuItem value="test">Teste</MenuItem>
                  <MenuItem value="lost">Perdido</MenuItem>
                  <MenuItem value="removal">Remoção</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Nível de Prioridade</InputLabel>
                <Select
                  defaultValue=""
                  label="Nível de Prioridade"
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value) {
                      handleBulkUpdate({ priority_level: parseInt(value) });
                    }
                  }}
                >
                  <MenuItem value={1}>1 - Crítico</MenuItem>
                  <MenuItem value={2}>2 - Alto</MenuItem>
                  <MenuItem value={3}>3 - Normal</MenuItem>
                  <MenuItem value={4}>4 - Baixo</MenuItem>
                  <MenuItem value={5}>5 - Mínimo</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Fidelidade</InputLabel>
                <Select
                  defaultValue=""
                  label="Fidelidade"
                  onChange={(e) => {
                    const value = e.target.value;
                    if (value) {
                      handleBulkUpdate({ fidelity_score: parseInt(value) });
                    }
                  }}
                >
                  <MenuItem value={1}>⭐ (1 estrela)</MenuItem>
                  <MenuItem value={2}>⭐⭐ (2 estrelas)</MenuItem>
                  <MenuItem value={3}>⭐⭐⭐ (3 estrelas)</MenuItem>
                  <MenuItem value={4}>⭐⭐⭐⭐ (4 estrelas)</MenuItem>
                  <MenuItem value={5}>⭐⭐⭐⭐⭐ (5 estrelas)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
          
          <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
            Selecione uma opção acima para aplicar a todos os dispositivos selecionados.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkEditDialogOpen(false)}>Cancelar</Button>
        </DialogActions>
      </Dialog>

      {/* Floating Refresh Button */}
      <Fab
        color="primary"
        aria-label="refresh"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={fetchMonitoringData}
        disabled={loading}
      >
        <Refresh />
      </Fab>
    </Box>
  );
};

export default ClientMonitoringDashboard;
