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
  IconButton,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Pagination,
  Stack,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as RetryIcon,
  Cancel as CancelIcon,
  Visibility as ViewIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  Command,
  CommandStatus,
  CommandPriority,
  CommandType,
} from '../../types';
import { useCommands } from '../../hooks/useCommands';

interface CommandListProps {
  deviceId?: number;
  refreshInterval?: number;
}

const getStatusColor = (status: CommandStatus): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  switch (status) {
    case 'PENDING': return 'info';
    case 'SENT': return 'primary';
    case 'DELIVERED': return 'secondary';
    case 'EXECUTED': return 'success';
    case 'FAILED': return 'error';
    case 'TIMEOUT': return 'warning';
    case 'CANCELLED': return 'default';
    case 'EXPIRED': return 'default';
    default: return 'default';
  }
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

const getStatusLabel = (status: CommandStatus): string => {
  const labels: Record<CommandStatus, string> = {
    PENDING: 'Pendente',
    SENT: 'Enviado',
    DELIVERED: 'Entregue',
    EXECUTED: 'Executado',
    FAILED: 'Falhou',
    TIMEOUT: 'Timeout',
    CANCELLED: 'Cancelado',
    EXPIRED: 'Expirado',
  };
  return labels[status] || status;
};

const getPriorityLabel = (priority: CommandPriority): string => {
  const labels: Record<CommandPriority, string> = {
    LOW: 'Baixa',
    NORMAL: 'Normal',
    HIGH: 'Alta',
    CRITICAL: 'Crítica',
  };
  return labels[priority] || priority;
};

export const CommandList: React.FC<CommandListProps> = ({
  deviceId,
  refreshInterval = 30000, // 30 seconds
}) => {
  const {
    commands,
    loading,
    error,
    refreshCommands,
    retryCommand,
    cancelCommand,
  } = useCommands();

  const [filteredCommands, setFilteredCommands] = useState<Command[]>([]);
  const [statusFilter, setStatusFilter] = useState<CommandStatus | 'ALL'>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<CommandPriority | 'ALL'>('ALL');
  const [typeFilter, setTypeFilter] = useState<CommandType | 'ALL'>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [selectedCommand, setSelectedCommand] = useState<Command | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const itemsPerPage = 10;

  // Filter commands
  useEffect(() => {
    let filtered = commands;

    // Filter by device if specified
    if (deviceId) {
      filtered = filtered.filter(cmd => cmd.device_id === deviceId);
    }

    // Filter by status
    if (statusFilter !== 'ALL') {
      filtered = filtered.filter(cmd => cmd.status === statusFilter);
    }

    // Filter by priority
    if (priorityFilter !== 'ALL') {
      filtered = filtered.filter(cmd => cmd.priority === priorityFilter);
    }

    // Filter by type
    if (typeFilter !== 'ALL') {
      filtered = filtered.filter(cmd => cmd.command_type === typeFilter);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(cmd =>
        cmd.command_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        cmd.device?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        cmd.response?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredCommands(filtered);
    setPage(1); // Reset to first page when filters change
  }, [commands, deviceId, statusFilter, priorityFilter, typeFilter, searchTerm]);

  // Auto-refresh
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(refreshCommands, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshCommands, refreshInterval]);

  const handleRetry = async (commandId: number) => {
    try {
      await retryCommand(commandId);
    } catch (err) {
      console.error('Error retrying command:', err);
    }
  };

  const handleCancel = async (commandId: number) => {
    try {
      await cancelCommand(commandId);
    } catch (err) {
      console.error('Error cancelling command:', err);
    }
  };

  const handleViewDetails = (command: Command) => {
    setSelectedCommand(command);
    setDetailsOpen(true);
  };

  const canRetry = (command: Command): boolean => {
    return command.status === 'FAILED' && command.retry_count < command.max_retries;
  };

  const canCancel = (command: Command): boolean => {
    return command.status === 'PENDING' || command.status === 'SENT';
  };

  const paginatedCommands = filteredCommands.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  );

  const totalPages = Math.ceil(filteredCommands.length / itemsPerPage);

  return (
    <Box>
      {/* Filters */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Buscar"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as CommandStatus | 'ALL')}
                >
                  <MenuItem value="ALL">Todos</MenuItem>
                  <MenuItem value="PENDING">Pendente</MenuItem>
                  <MenuItem value="SENT">Enviado</MenuItem>
                  <MenuItem value="DELIVERED">Entregue</MenuItem>
                  <MenuItem value="EXECUTED">Executado</MenuItem>
                  <MenuItem value="FAILED">Falhou</MenuItem>
                  <MenuItem value="TIMEOUT">Timeout</MenuItem>
                  <MenuItem value="CANCELLED">Cancelado</MenuItem>
                  <MenuItem value="EXPIRED">Expirado</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Prioridade</InputLabel>
                <Select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value as CommandPriority | 'ALL')}
                >
                  <MenuItem value="ALL">Todas</MenuItem>
                  <MenuItem value="LOW">Baixa</MenuItem>
                  <MenuItem value="NORMAL">Normal</MenuItem>
                  <MenuItem value="HIGH">Alta</MenuItem>
                  <MenuItem value="CRITICAL">Crítica</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Tipo</InputLabel>
                <Select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as CommandType | 'ALL')}
                >
                  <MenuItem value="ALL">Todos</MenuItem>
                  <MenuItem value="REBOOT">REBOOT</MenuItem>
                  <MenuItem value="PING">PING</MenuItem>
                  <MenuItem value="STATUS">STATUS</MenuItem>
                  <MenuItem value="SETINTERVAL">SETINTERVAL</MenuItem>
                  <MenuItem value="SETOVERSPEED">SETOVERSPEED</MenuItem>
                  <MenuItem value="CUSTOM">CUSTOM</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <Stack direction="row" spacing={1}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={refreshCommands}
                  disabled={loading}
                  size="small"
                >
                  Atualizar
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Commands Table */}
      <Card>
        <CardContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Dispositivo</TableCell>
                  <TableCell>Comando</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Prioridade</TableCell>
                  <TableCell>Enviado</TableCell>
                  <TableCell>Tentativas</TableCell>
                  <TableCell>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedCommands.map((command) => (
                  <TableRow key={command.id}>
                    <TableCell>{command.id}</TableCell>
                    <TableCell>
                      {command.device?.name || `Device ${command.device_id}`}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {command.command_type}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusLabel(command.status)}
                        color={getStatusColor(command.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getPriorityLabel(command.priority)}
                        color={getPriorityColor(command.priority)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {command.sent_at
                        ? format(new Date(command.sent_at), 'dd/MM/yyyy HH:mm', { locale: ptBR })
                        : '-'
                      }
                    </TableCell>
                    <TableCell>
                      {command.retry_count}/{command.max_retries}
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        <Tooltip title="Ver Detalhes">
                          <IconButton
                            size="small"
                            onClick={() => handleViewDetails(command)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        {canRetry(command) && (
                          <Tooltip title="Tentar Novamente">
                            <IconButton
                              size="small"
                              onClick={() => handleRetry(command.id)}
                              color="primary"
                            >
                              <RetryIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        {canCancel(command) && (
                          <Tooltip title="Cancelar">
                            <IconButton
                              size="small"
                              onClick={() => handleCancel(command.id)}
                              color="error"
                            >
                              <CancelIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box display="flex" justifyContent="center" mt={2}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          )}

          {filteredCommands.length === 0 && !loading && (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="text.secondary">
                Nenhum comando encontrado
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Command Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Detalhes do Comando</DialogTitle>
        <DialogContent>
          {selectedCommand && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">ID:</Typography>
                <Typography variant="body2">{selectedCommand.id}</Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Dispositivo:</Typography>
                <Typography variant="body2">
                  {selectedCommand.device?.name || `Device ${selectedCommand.device_id}`}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Tipo:</Typography>
                <Typography variant="body2" fontFamily="monospace">
                  {selectedCommand.command_type}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Status:</Typography>
                <Chip
                  label={getStatusLabel(selectedCommand.status)}
                  color={getStatusColor(selectedCommand.status)}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Prioridade:</Typography>
                <Chip
                  label={getPriorityLabel(selectedCommand.priority)}
                  color={getPriorityColor(selectedCommand.priority)}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Tentativas:</Typography>
                <Typography variant="body2">
                  {selectedCommand.retry_count}/{selectedCommand.max_retries}
                </Typography>
              </Grid>
              {selectedCommand.parameters && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Parâmetros:</Typography>
                  <Typography variant="body2" component="pre" sx={{ bgcolor: 'grey.100', p: 1, borderRadius: 1 }}>
                    {JSON.stringify(selectedCommand.parameters, null, 2)}
                  </Typography>
                </Grid>
              )}
              {selectedCommand.response && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Resposta:</Typography>
                  <Typography variant="body2" component="pre" sx={{ bgcolor: 'grey.100', p: 1, borderRadius: 1 }}>
                    {selectedCommand.response}
                  </Typography>
                </Grid>
              )}
              {selectedCommand.error_message && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Erro:</Typography>
                  <Alert severity="error">
                    {selectedCommand.error_message}
                  </Alert>
                </Grid>
              )}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Criado em:</Typography>
                <Typography variant="body2">
                  {format(new Date(selectedCommand.created_at), 'dd/MM/yyyy HH:mm:ss', { locale: ptBR })}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2">Atualizado em:</Typography>
                <Typography variant="body2">
                  {format(new Date(selectedCommand.updated_at), 'dd/MM/yyyy HH:mm:ss', { locale: ptBR })}
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Fechar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

