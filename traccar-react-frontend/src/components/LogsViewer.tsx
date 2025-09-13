import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  ExpandMore as ExpandMoreIcon,
  LocationOn as LocationIcon,
  Event as EventIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { useAuth } from '../contexts/AuthContext';

interface LogEntry {
  id: string;
  timestamp: string;
  device_id: number;
  device_name: string;
  protocol: string;
  type: string;
  data: any;
}

interface LogsResponse {
  entries: LogEntry[];
  total: number;
  limit: number;
  filters: {
    device_id?: number;
    protocol?: string;
    hours: number;
  };
}

interface Device {
  id: number;
  name: string;
  unique_id: string;
  status: string;
}

const LogsViewer: React.FC = () => {
  const { isAuthenticated, token } = useAuth();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [protocols, setProtocols] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<number | ''>('');
  const [selectedProtocol, setSelectedProtocol] = useState<string>('');
  const [hours, setHours] = useState<number>(24);
  const [limit, setLimit] = useState<number>(100);
  const [logType, setLogType] = useState<'combined' | 'positions' | 'events'>('combined');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (!isAuthenticated || !token) {
        setError('Usuário não autenticado');
        setLoading(false);
        return;
      }

      const params = new URLSearchParams();
      if (selectedDevice) params.append('device_id', selectedDevice.toString());
      if (selectedProtocol) params.append('protocol', selectedProtocol);
      params.append('hours', hours.toString());
      params.append('limit', limit.toString());

      const response = await fetch(`http://localhost:8000/api/logs/${logType}?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch logs');
      }

      const data: LogsResponse = await response.json();
      setLogs(data.entries);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  };

  const fetchDevices = async () => {
    try {
      if (!isAuthenticated || !token) return;

      const response = await fetch('http://localhost:8000/api/logs/devices', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDevices(data);
      }
    } catch (err) {
      console.error('Failed to fetch devices:', err);
    }
  };

  const fetchProtocols = async () => {
    try {
      if (!isAuthenticated || !token) return;

      const response = await fetch('http://localhost:8000/api/logs/protocols', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProtocols(data);
      }
    } catch (err) {
      console.error('Failed to fetch protocols:', err);
    }
  };

  useEffect(() => {
    if (isAuthenticated && token) {
      fetchDevices();
      fetchProtocols();
      fetchLogs();
    } else {
      // Clear data when not authenticated
      setLogs([]);
      setDevices([]);
      setProtocols([]);
      setError('Usuário não autenticado');
    }
  }, [isAuthenticated, token, logType, selectedDevice, selectedProtocol, hours, limit]);

  const getLogIcon = (type: string) => {
    if (type === 'position') {
      return <LocationIcon color="primary" />;
    }
    return <EventIcon color="secondary" />;
  };

  const getLogColor = (type: string) => {
    if (type === 'position') {
      return 'primary';
    }
    if (type.includes('alarm') || type.includes('error')) {
      return 'error';
    }
    if (type.includes('moving') || type.includes('online')) {
      return 'success';
    }
    return 'default';
  };

  const formatTimestamp = (timestamp: string) => {
    return format(new Date(timestamp), 'dd/MM/yyyy HH:mm:ss', { locale: ptBR });
  };

  const renderLogData = (log: LogEntry) => {
    if (log.type === 'position') {
      return (
        <Box>
          <Typography variant="body2" color="text.secondary">
            <strong>Coordenadas:</strong> {log.data.latitude?.toFixed(6)}, {log.data.longitude?.toFixed(6)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Velocidade:</strong> {log.data.speed?.toFixed(2)} km/h
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Curso:</strong> {log.data.course?.toFixed(1)}°
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Altitude:</strong> {log.data.altitude?.toFixed(1)}m
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Válido:</strong> {log.data.valid ? 'Sim' : 'Não'}
          </Typography>
        </Box>
      );
    } else {
      return (
        <Box>
          <Typography variant="body2" color="text.secondary">
            <strong>Tipo:</strong> {log.type}
          </Typography>
          {log.data.attributes && (
            <Typography variant="body2" color="text.secondary">
              <strong>Atributos:</strong> {JSON.stringify(log.data.attributes)}
            </Typography>
          )}
        </Box>
      );
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Logs do Sistema
        </Typography>
        <Box>
          <Tooltip title="Configurações">
            <IconButton onClick={() => setSettingsOpen(true)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Atualizar">
            <IconButton onClick={fetchLogs} disabled={loading || !isAuthenticated}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Filtros */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Tipo de Log</InputLabel>
                <Select
                  value={logType}
                  onChange={(e) => setLogType(e.target.value as any)}
                  label="Tipo de Log"
                >
                  <MenuItem value="combined">Combinado</MenuItem>
                  <MenuItem value="positions">Posições</MenuItem>
                  <MenuItem value="events">Eventos</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Dispositivo</InputLabel>
                <Select
                  value={selectedDevice}
                  onChange={(e) => setSelectedDevice(e.target.value as number | '')}
                  label="Dispositivo"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {devices.map((device) => (
                    <MenuItem key={device.id} value={device.id}>
                      {device.name} ({device.unique_id})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Protocolo</InputLabel>
                <Select
                  value={selectedProtocol}
                  onChange={(e) => setSelectedProtocol(e.target.value)}
                  label="Protocolo"
                >
                  <MenuItem value="">Todos</MenuItem>
                  {protocols.map((protocol) => (
                    <MenuItem key={protocol} value={protocol}>
                      {protocol}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                size="small"
                label="Horas"
                type="number"
                value={hours}
                onChange={(e) => setHours(parseInt(e.target.value) || 24)}
                inputProps={{ min: 1, max: 168 }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                size="small"
                label="Limite"
                type="number"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
                inputProps={{ min: 1, max: 1000 }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Button
                variant="contained"
                startIcon={<FilterIcon />}
                onClick={fetchLogs}
                disabled={loading || !isAuthenticated}
                fullWidth
              >
                Filtrar
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {!isAuthenticated && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Você precisa fazer login para visualizar os logs.
            </Alert>
          )}

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Dispositivo</TableCell>
                    <TableCell>Protocolo</TableCell>
                    <TableCell>Tipo</TableCell>
                    <TableCell>Dados</TableCell>
                    <TableCell>Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id} hover>
                      <TableCell>
                        <Typography variant="body2">
                          {formatTimestamp(log.timestamp)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {log.device_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ID: {log.device_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={log.protocol} size="small" />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getLogIcon(log.type)}
                          <Chip
                            label={log.type}
                            size="small"
                            color={getLogColor(log.type) as any}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ maxWidth: 200 }}>
                          {log.type === 'position' ? (
                            <Typography variant="body2" noWrap>
                              {log.data.latitude?.toFixed(4)}, {log.data.longitude?.toFixed(4)}
                            </Typography>
                          ) : (
                            <Typography variant="body2" noWrap>
                              {log.type}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          onClick={() => setSelectedLog(log)}
                        >
                          Ver Detalhes
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {!loading && logs.length === 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Nenhum log encontrado com os filtros aplicados.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Log Details Dialog */}
      <Dialog
        open={!!selectedLog}
        onClose={() => setSelectedLog(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Detalhes do Log
          {selectedLog && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              {getLogIcon(selectedLog.type)}
              <Chip
                label={selectedLog.type}
                size="small"
                color={getLogColor(selectedLog.type) as any}
              />
            </Box>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedLog && (
            <Box>
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Informações Básicas</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>ID:</strong> {selectedLog.id}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Timestamp:</strong> {formatTimestamp(selectedLog.timestamp)}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Dispositivo:</strong> {selectedLog.device_name} (ID: {selectedLog.device_id})
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Protocolo:</strong> {selectedLog.protocol}
                      </Typography>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Dados</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {renderLogData(selectedLog)}
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">JSON Completo</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box
                    component="pre"
                    sx={{
                      backgroundColor: 'grey.100',
                      p: 2,
                      borderRadius: 1,
                      overflow: 'auto',
                      fontSize: '0.875rem'
                    }}
                  >
                    {JSON.stringify(selectedLog.data, null, 2)}
                  </Box>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedLog(null)}>Fechar</Button>
        </DialogActions>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Configurações de Logs</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Configurações Padrão
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Limite Padrão de Logs"
                  type="number"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
                  inputProps={{ min: 1, max: 1000 }}
                  helperText="Número máximo de logs a serem exibidos (1-1000)"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Período Padrão (horas)"
                  type="number"
                  value={hours}
                  onChange={(e) => setHours(parseInt(e.target.value) || 24)}
                  inputProps={{ min: 1, max: 168 }}
                  helperText="Período de tempo para buscar logs (1-168 horas)"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Fechar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LogsViewer;
