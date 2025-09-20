import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Tooltip,
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
  GpsFixed,
  BatteryAlert,
  Refresh,
  FilterList,
  NotificationsActive,
  Star,
  Power,
  SignalCellularOff,
  PriorityHigh,
  Edit,
  GroupWork,
  LocationOn
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
  return (
    <Card 
      sx={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s',
        '&:hover': onClick ? { transform: 'translateY(-2px)' } : {},
        mb: 2
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
          <Box
            sx={{
              width: 16,
              height: 16,
              borderRadius: '50%',
              backgroundColor: getStatusColor(device.communication_status.color),
              mb: 0.5
            }}
          />
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
            {device.client_code && (
              <Chip
                label={device.client_code}
                size="small"
                color={getClientCodeColor(device.client_code) as any}
                sx={{ fontSize: '0.75rem', height: 20 }}
              />
            )}
            
            <Typography variant="subtitle1" fontWeight="bold" sx={{ color: '#1a1a1a' }}>
              {device.name}
            </Typography>
            
            {device.has_sos_alert && <Error color="error" fontSize="small" />}
            {device.has_battery_alert && <BatteryAlert color="warning" fontSize="small" />}
            {device.has_communication_alert && <SignalCellularOff color="error" fontSize="small" />}
          </Box>
        }
        secondary={
          <Box>
            <Typography variant="body2" sx={{ color: '#424242' }}>
              {device.client_type_display} • {device.priority_display}
            </Typography>
            <Typography variant="body2" sx={{ color: '#424242' }}>
              {device.person_name || 'Sem responsável'} • {formatTimeAgo(device.minutes_since_update)}
            </Typography>
            {device.ignition !== undefined && (
              <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                <Power 
                  fontSize="small" 
                  color={device.ignition ? "success" : "disabled"} 
                />
                <Typography variant="caption" sx={{ color: '#424242' }}>
                  Ignição {device.ignition ? 'Ligada' : 'Desligada'}
                </Typography>
                {device.speed !== undefined && (
                  <>
                    <Typography variant="caption" sx={{ ml: 2, color: '#424242' }}>
                      {Math.round((device.speed || 0) * 1.852)} km/h
                    </Typography>
                  </>
                )}
              </Box>
            )}
          </Box>
        }
      />

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
        <Typography variant="caption" sx={{ color: '#424242' }}>
          Fidelidade
        </Typography>
      </Box>
    </ListItem>
  );
};

// Main Component
const ClientMonitoringDashboard: React.FC = () => {
  // const { devices, loading: devicesLoading, fetchDevices } = useDevices();
  
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
  const [pois, setPois] = useState<any[]>([]);

  // Fetch data
  const fetchMonitoringData = useCallback(async () => {
    try {
      setLoading(true);
      
      const token = localStorage.getItem('access_token');
      console.log('Token available:', !!token);
      
      if (!token) {
        console.error('No token found, user not authenticated');
        setLoading(false);
        return;
      }
      
      // Fetch summary
      console.log('Fetching summary...');
      const summaryResponse = await fetch('/api/client-monitoring/summary', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Summary response status:', summaryResponse.status);
      
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        console.log('Summary data:', summaryData);
        setSummary(summaryData);
      } else {
        console.error('Failed to fetch summary:', summaryResponse.statusText);
        setSummary({
          total_devices: 0,
          online_count: 0,
          offline_count: 0,
          unknown_count: 0,
          critical_count: 0,
          delinquent_count: 0,
          test_devices: 0,
          lost_devices: 0,
          active_alerts: 0,
          recent_sos: 0,
          battery_alerts: 0,
          communication_alerts: 0
        });
      }

      // Fetch POIs
      try {
        const poisResponse = await fetch('/api/pois/', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (poisResponse.ok) {
          const poisData = await poisResponse.json();
          setPois(Array.isArray(poisData) ? poisData : []);
          console.log('POIs loaded:', poisData.length);
        }
      } catch (error) {
        console.error('Error fetching POIs:', error);
      }
      
      // Fetch devices
      console.log('Fetching devices...');
      const params = new URLSearchParams();
      if (clientFilter !== 'all') params.append('client_filter', clientFilter);
      if (priorityOnly) params.append('priority_only', 'true');
      if (communicationFilter !== 'all') params.append('communication_status', communicationFilter);
      
      const devicesResponse = await fetch(`/api/client-monitoring/devices?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Devices response status:', devicesResponse.status);
      
      if (devicesResponse.ok) {
        const devicesData = await devicesResponse.json();
        console.log('Devices data:', devicesData);
        console.log('Is devices data an array?', Array.isArray(devicesData));
        // Ensure we have an array
        setMonitoringDevices(Array.isArray(devicesData) ? devicesData : []);
      } else {
        console.error('Failed to fetch devices:', devicesResponse.statusText);
        setMonitoringDevices([]);
      }
      
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      setMonitoringDevices([]);
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
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
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
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
        <Box sx={{ flex: '1 1 250px' }}>
          <StatsCard
            title="Dispositivos Totais"
            value={summary?.total_devices || 0}
            subtitle={`${summary?.online_count || 0} online`}
            icon={<GpsFixed />}
            color="primary"
          />
        </Box>
        
        <Box sx={{ flex: '1 1 250px' }}>
          <StatsCard
            title="Situações Críticas"
            value={summary?.critical_count || 0}
            subtitle="Requer atenção imediata"
            icon={<Warning />}
            color="error"
            onClick={() => handleFilterChange('priority', true)}
          />
        </Box>
        
        <Box sx={{ flex: '1 1 250px' }}>
          <StatsCard
            title="Inadimplentes"
            value={summary?.delinquent_count || 0}
            subtitle="Clientes em atraso"
            icon={<Error />}
            color="warning"
            onClick={() => handleFilterChange('client', 'delinquent')}
          />
        </Box>

        <Box sx={{ flex: '1 1 250px' }}>
          <StatsCard
            title="Alertas Ativos"
            value={summary?.active_alerts || 0}
            subtitle="Comunicação, SOS, Bateria"
            icon={<NotificationsActive />}
            color="info"
          />
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          <FilterList /> Filtros Inteligentes
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
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

          <FormControl size="small" sx={{ minWidth: 200 }}>
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

          <FormControlLabel
            control={
              <Switch
                checked={priorityOnly}
                onChange={(e) => handleFilterChange('priority', e.target.checked)}
              />
            }
            label="Apenas Prioritários"
          />

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
        </Box>
      </Paper>

      {/* Device List */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          📋 Lista Priorizada de Dispositivos ({Array.isArray(monitoringDevices) ? monitoringDevices.length : 0})
        </Typography>
        
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : (
          <List sx={{ maxHeight: '600px', overflow: 'auto' }}>
            {Array.isArray(monitoringDevices) && monitoringDevices.map((device) => (
              <DeviceListItem
                key={device.id}
                device={device}
                onDeviceClick={handleDeviceClick}
                selected={selectedDevices.includes(device.id)}
                onToggleSelection={toggleDeviceSelection}
              />
            ))}
            {(!Array.isArray(monitoringDevices) || monitoringDevices.length === 0) && (
              <Box textAlign="center" py={4}>
                <Typography sx={{ color: '#666666' }}>
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
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 300px' }}>
                <Typography variant="subtitle2" gutterBottom>Informações Básicas</Typography>
                <Typography>ID: {selectedDevice.unique_id}</Typography>
                <Typography>Status: {selectedDevice.status}</Typography>
                <Typography>Tipo: {selectedDevice.client_type_display}</Typography>
                <Typography>Prioridade: {selectedDevice.priority_display}</Typography>
                {selectedDevice.person_name && (
                  <Typography>Responsável: {selectedDevice.person_name}</Typography>
                )}
              </Box>
              
              <Box sx={{ flex: '1 1 300px' }}>
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
              </Box>
            </Box>
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
          <Box display="flex" alignItems="center" gap={1}>
            <GroupWork />
            Editar Dispositivos em Lote ({selectedDevices.length} selecionados)
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom sx={{ mt: 2 }}>
            Marcar como Inadimplentes:
          </Typography>
          <Button
            variant="contained"
            color="error"
            fullWidth
            sx={{ mb: 2 }}
            onClick={() => handleBulkUpdate({ 
              client_code: '#16', 
              client_status: 'delinquent',
              priority_level: 1,
              fidelity_score: 2
            })}
          >
            🔴 #16 - Cliente Inadimplente
          </Button>

          <Typography variant="body1" gutterBottom>
            Marcar como Equipamento de Teste:
          </Typography>
          <Button
            variant="contained"
            color="warning"
            fullWidth
            sx={{ mb: 2 }}
            onClick={() => handleBulkUpdate({ 
              client_code: '#13', 
              client_status: 'test',
              priority_level: 4
            })}
          >
            🟡 #13 - Equipamento de Teste
          </Button>

          <Typography variant="body1" gutterBottom>
            Marcar como Perdido:
          </Typography>
          <Button
            variant="contained"
            color="error"
            fullWidth
            sx={{ mb: 2 }}
            onClick={() => handleBulkUpdate({ 
              client_code: '#14', 
              client_status: 'lost',
              priority_level: 1,
              fidelity_score: 1
            })}
          >
            🔴 #14 - Equipamento Perdido
          </Button>

          <Typography variant="body1" gutterBottom>
            Marcar como Ativo:
          </Typography>
          <Button
            variant="contained"
            color="success"
            fullWidth
            onClick={() => handleBulkUpdate({ 
              client_code: '', 
              client_status: 'active',
              priority_level: 3,
              fidelity_score: 4
            })}
          >
            🟢 Cliente Ativo
          </Button>
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
