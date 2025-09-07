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
  Grid,
  Typography,
  Box,
  Alert,
  Chip,
  Divider,
  Autocomplete,
  Checkbox,
  FormControlLabel,
  FormGroup,
} from '@mui/material';
// import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
// import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
// import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
// import { ptBR } from 'date-fns/locale';
import {
  CommandBulkCreate,
  CommandType,
  CommandPriority,
  Device,
} from '../../types';
import { useCommands } from '../../hooks/useCommands';
import { useDevices } from '../../hooks/useDevices';

interface BulkCommandDialogProps {
  open: boolean;
  onClose: () => void;
  onCommandsSent?: (result: { created: number; failed: number }) => void;
}

interface CommandParameter {
  key: string;
  label: string;
  type: 'number' | 'string' | 'boolean';
  required: boolean;
  description?: string;
}

const COMMAND_PARAMETERS: Record<CommandType, CommandParameter[]> = {
  // Suntech Commands
  REBOOT: [],
  SETTIME: [],
  SETINTERVAL: [
    { key: 'interval', label: 'Intervalo (segundos)', type: 'number', required: true, description: 'Intervalo entre envios de posição' }
  ],
  SETOVERSPEED: [
    { key: 'speed_limit', label: 'Limite de Velocidade (km/h)', type: 'number', required: true, description: 'Velocidade máxima permitida' }
  ],
  SETGEOFENCE: [
    { key: 'latitude', label: 'Latitude', type: 'number', required: true, description: 'Latitude do centro da geofence' },
    { key: 'longitude', label: 'Longitude', type: 'number', required: true, description: 'Longitude do centro da geofence' },
    { key: 'radius', label: 'Raio (metros)', type: 'number', required: true, description: 'Raio da geofence em metros' }
  ],
  SETOUTPUT: [
    { key: 'output_id', label: 'ID da Saída', type: 'number', required: true, description: 'Identificador da saída digital' },
    { key: 'output_state', label: 'Estado', type: 'boolean', required: true, description: 'Estado da saída (ligado/desligado)' }
  ],
  SETINPUT: [
    { key: 'input_id', label: 'ID da Entrada', type: 'number', required: true, description: 'Identificador da entrada digital' },
    { key: 'input_type', label: 'Tipo', type: 'string', required: true, description: 'Tipo da entrada' }
  ],
  SETACCELERATION: [
    { key: 'threshold', label: 'Limite de Aceleração', type: 'number', required: true, description: 'Limite de aceleração em m/s²' }
  ],
  SETDECELERATION: [
    { key: 'threshold', label: 'Limite de Desaceleração', type: 'number', required: true, description: 'Limite de desaceleração em m/s²' }
  ],
  SETTURN: [
    { key: 'angle_threshold', label: 'Limite de Curva (graus)', type: 'number', required: true, description: 'Ângulo mínimo para detectar curva' }
  ],
  SETIDLE: [
    { key: 'idle_time', label: 'Tempo de Inatividade (minutos)', type: 'number', required: true, description: 'Tempo para considerar inativo' }
  ],
  SETPARKING: [],
  SETMOVEMENT: [],
  SETVIBRATION: [],
  SETDOOR: [],
  SETPOWER: [],

  // OsmAnd Commands
  SET_INTERVAL: [
    { key: 'interval', label: 'Intervalo (segundos)', type: 'number', required: true, description: 'Intervalo entre envios de posição' }
  ],
  SET_ACCURACY: [
    { key: 'accuracy', label: 'Precisão (metros)', type: 'number', required: true, description: 'Precisão GPS desejada' }
  ],
  SET_BATTERY_SAVER: [
    { key: 'battery_saver', label: 'Modo Economia', type: 'boolean', required: true, description: 'Ativar modo economia de bateria' }
  ],
  SET_ALARM: [
    { key: 'alarm_type', label: 'Tipo de Alarme', type: 'string', required: true, description: 'Tipo do alarme' },
    { key: 'alarm_enabled', label: 'Alarme Ativo', type: 'boolean', required: true, description: 'Ativar/desativar alarme' }
  ],
  SET_GEOFENCE: [
    { key: 'latitude', label: 'Latitude', type: 'number', required: true, description: 'Latitude do centro da geofence' },
    { key: 'longitude', label: 'Longitude', type: 'number', required: true, description: 'Longitude do centro da geofence' },
    { key: 'radius', label: 'Raio (metros)', type: 'number', required: true, description: 'Raio da geofence em metros' }
  ],
  SET_SPEED_LIMIT: [
    { key: 'speed_limit', label: 'Limite de Velocidade (km/h)', type: 'number', required: true, description: 'Velocidade máxima permitida' }
  ],
  SET_ENGINE_STOP: [],
  SET_ENGINE_START: [],

  // Generic Commands
  CUSTOM: [
    { key: 'raw_command', label: 'Comando Raw', type: 'string', required: true, description: 'Comando personalizado para o dispositivo' }
  ],
  PING: [],
  STATUS: [],
  CONFIG: [
    { key: 'parameters', label: 'Parâmetros', type: 'string', required: false, description: 'Parâmetros de configuração (JSON)' }
  ],
};

export const BulkCommandDialog: React.FC<BulkCommandDialogProps> = ({
  open,
  onClose,
  onCommandsSent,
}) => {
  const { devices, loading: devicesLoading } = useDevices();
  const { 
    commandTypes, 
    commandPriorities, 
    createBulkCommands, 
    loading, 
    error 
  } = useCommands();

  const [formData, setFormData] = useState<CommandBulkCreate>({
    device_ids: [],
    command_type: 'PING',
    priority: 'NORMAL',
    parameters: {},
    max_retries: 3,
  });
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({});
  const [selectedDevices, setSelectedDevices] = useState<Device[]>([]);
  const [selectAll, setSelectAll] = useState(false);

  useEffect(() => {
    // Reset parameters when command type changes
    setParameterValues({});
    setFormData(prev => ({ ...prev, parameters: {} }));
  }, [formData.command_type]);

  useEffect(() => {
    // Update device_ids when selectedDevices changes
    setFormData(prev => ({ 
      ...prev, 
      device_ids: selectedDevices.map(device => device.id) 
    }));
  }, [selectedDevices]);

  const handleSubmit = async () => {
    try {
      const commandData: CommandBulkCreate = {
        ...formData,
        parameters: Object.keys(parameterValues).length > 0 ? parameterValues : undefined,
        expires_at: expiresAt ? expiresAt.toISOString() : undefined,
      };

      const result = await createBulkCommands(commandData);
      onCommandsSent?.(result);
      onClose();
      
      // Reset form
      setFormData({
        device_ids: [],
        command_type: 'PING',
        priority: 'NORMAL',
        parameters: {},
        max_retries: 3,
      });
      setParameterValues({});
      setExpiresAt(null);
      setSelectedDevices([]);
      setSelectAll(false);
    } catch (err) {
      console.error('Error creating bulk commands:', err);
    }
  };

  const handleParameterChange = (key: string, value: any) => {
    setParameterValues(prev => ({ ...prev, [key]: value }));
  };

  const handleSelectAll = (checked: boolean) => {
    setSelectAll(checked);
    if (checked) {
      setSelectedDevices(devices);
    } else {
      setSelectedDevices([]);
    }
  };

  const handleDeviceToggle = (device: Device, checked: boolean) => {
    if (checked) {
      setSelectedDevices(prev => [...prev, device]);
    } else {
      setSelectedDevices(prev => prev.filter(d => d.id !== device.id));
    }
  };

  const getCommandDescription = (commandType: CommandType): string => {
    const descriptions: Record<CommandType, string> = {
      REBOOT: 'Reinicia o dispositivo',
      SETTIME: 'Configura o horário do dispositivo',
      SETINTERVAL: 'Define o intervalo de envio de posições',
      SETOVERSPEED: 'Configura limite de velocidade',
      SETGEOFENCE: 'Configura geofence circular',
      SETOUTPUT: 'Controla saída digital',
      SETINPUT: 'Configura entrada digital',
      SETACCELERATION: 'Define limite de aceleração',
      SETDECELERATION: 'Define limite de desaceleração',
      SETTURN: 'Configura detecção de curvas',
      SETIDLE: 'Define tempo de inatividade',
      SETPARKING: 'Ativa detecção de estacionamento',
      SETMOVEMENT: 'Ativa detecção de movimento',
      SETVIBRATION: 'Ativa detecção de vibração',
      SETDOOR: 'Controla porta do veículo',
      SETPOWER: 'Controla energia do dispositivo',
      SET_INTERVAL: 'Define intervalo de tracking (OsmAnd)',
      SET_ACCURACY: 'Configura precisão GPS (OsmAnd)',
      SET_BATTERY_SAVER: 'Ativa modo economia (OsmAnd)',
      SET_ALARM: 'Configura alarmes (OsmAnd)',
      SET_GEOFENCE: 'Configura geofence (OsmAnd)',
      SET_SPEED_LIMIT: 'Define limite de velocidade (OsmAnd)',
      SET_ENGINE_STOP: 'Para o motor (OsmAnd)',
      SET_ENGINE_START: 'Liga o motor (OsmAnd)',
      CUSTOM: 'Comando personalizado',
      PING: 'Testa conectividade',
      STATUS: 'Solicita status do dispositivo',
      CONFIG: 'Configuração geral',
    };
    return descriptions[commandType] || 'Comando não documentado';
  };

  const getPriorityColor = (priority: CommandPriority): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (priority) {
      case 'LOW': return 'default';
      case 'NORMAL': return 'primary';
      case 'HIGH': return 'warning';
      case 'CRITICAL': return 'error';
      default: return 'default';
    }
  };

  const currentParameters = COMMAND_PARAMETERS[formData.command_type] || [];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="h6">Envio em Lote</Typography>
            <Chip 
              label={formData.priority} 
              color={getPriorityColor(formData.priority)}
              size="small"
            />
            <Chip 
              label={`${selectedDevices.length} dispositivos`} 
              color="primary"
              size="small"
            />
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Grid container spacing={2}>
            {/* Command Type */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Comando</InputLabel>
                <Select
                  value={formData.command_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, command_type: e.target.value as CommandType }))}
                >
                  {commandTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Priority */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Prioridade</InputLabel>
                <Select
                  value={formData.priority}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value as CommandPriority }))}
                >
                  {commandPriorities.map((priority) => (
                    <MenuItem key={priority} value={priority}>
                      {priority}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Command Description */}
            <Grid item xs={12}>
              <Alert severity="info">
                <Typography variant="body2">
                  {getCommandDescription(formData.command_type)}
                </Typography>
              </Alert>
            </Grid>

            {/* Device Selection */}
            <Grid item xs={12}>
              <Divider>
                <Typography variant="subtitle2">Seleção de Dispositivos</Typography>
              </Divider>
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={selectAll}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                  />
                }
                label="Selecionar Todos"
              />
            </Grid>

            <Grid item xs={12}>
              <Box 
                sx={{ 
                  maxHeight: 200, 
                  overflow: 'auto', 
                  border: 1, 
                  borderColor: 'divider', 
                  borderRadius: 1,
                  p: 1 
                }}
              >
                <FormGroup>
                  {devices.map((device) => (
                    <FormControlLabel
                      key={device.id}
                      control={
                        <Checkbox
                          checked={selectedDevices.some(d => d.id === device.id)}
                          onChange={(e) => handleDeviceToggle(device, e.target.checked)}
                        />
                      }
                      label={`${device.name} (${device.status})`}
                    />
                  ))}
                </FormGroup>
              </Box>
            </Grid>

            {/* Parameters */}
            {currentParameters.length > 0 && (
              <>
                <Grid item xs={12}>
                  <Divider>
                    <Typography variant="subtitle2">Parâmetros</Typography>
                  </Divider>
                </Grid>
                {currentParameters.map((param) => (
                  <Grid item xs={12} md={6} key={param.key}>
                    {param.type === 'boolean' ? (
                      <FormControl fullWidth>
                        <InputLabel>{param.label}</InputLabel>
                        <Select
                          value={parameterValues[param.key] || ''}
                          onChange={(e) => handleParameterChange(param.key, e.target.value === 'true')}
                        >
                          <MenuItem value="true">Sim</MenuItem>
                          <MenuItem value="false">Não</MenuItem>
                        </Select>
                      </FormControl>
                    ) : (
                      <TextField
                        fullWidth
                        label={param.label}
                        type={param.type === 'number' ? 'number' : 'text'}
                        value={parameterValues[param.key] || ''}
                        onChange={(e) => {
                          const value = param.type === 'number' ? Number(e.target.value) : e.target.value;
                          handleParameterChange(param.key, value);
                        }}
                        required={param.required}
                        helperText={param.description}
                      />
                    )}
                  </Grid>
                ))}
              </>
            )}

            {/* Max Retries */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Máximo de Tentativas"
                type="number"
                value={formData.max_retries}
                onChange={(e) => setFormData(prev => ({ ...prev, max_retries: Number(e.target.value) }))}
                inputProps={{ min: 1, max: 10 }}
              />
            </Grid>

            {/* Expires At */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Expira em"
                type="datetime-local"
                value={expiresAt ? expiresAt.toISOString().slice(0, 16) : ''}
                onChange={(e) => setExpiresAt(e.target.value ? new Date(e.target.value) : null)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={loading || selectedDevices.length === 0}
          >
            {loading ? 'Enviando...' : `Enviar para ${selectedDevices.length} Dispositivos`}
          </Button>
        </DialogActions>
      </Dialog>
  );
};
