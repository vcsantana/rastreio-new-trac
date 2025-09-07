import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import {
  CommandStats as CommandStatsType,
  CommandStatus,
  CommandPriority,
  CommandType,
} from '../../types';
import { useCommands } from '../../hooks/useCommands';

interface CommandStatsProps {
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

const getStatusIcon = (status: CommandStatus) => {
  switch (status) {
    case 'EXECUTED': return <SuccessIcon color="success" />;
    case 'FAILED': return <ErrorIcon color="error" />;
    case 'PENDING': return <PendingIcon color="info" />;
    case 'CANCELLED': return <CancelIcon color="default" />;
    default: return null;
  }
};

export const CommandStats: React.FC<CommandStatsProps> = ({
  refreshInterval = 30000, // 30 seconds
}) => {
  const { commandStats, loading, error, refreshStats } = useCommands();
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Auto-refresh
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(() => {
        refreshStats();
        setLastUpdated(new Date());
      }, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshStats, refreshInterval]);

  const handleRefresh = () => {
    refreshStats();
    setLastUpdated(new Date());
  };

  if (loading && !commandStats) {
    return (
      <Card>
        <CardContent>
          <LinearProgress />
          <Typography variant="body2" sx={{ mt: 1 }}>
            Carregando estatísticas...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">
            Erro ao carregar estatísticas: {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!commandStats) {
    return (
      <Card>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Nenhuma estatística disponível
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const totalCommands = commandStats.total_commands;
  const successRate = commandStats.success_rate;
  const avgExecutionTime = commandStats.average_execution_time;

  // Calculate status percentages
  const statusPercentages = Object.entries(commandStats.commands_by_status).map(([status, count]) => ({
    status: status as CommandStatus,
    count,
    percentage: totalCommands > 0 ? (count / totalCommands) * 100 : 0,
  }));

  // Calculate priority percentages
  const priorityPercentages = Object.entries(commandStats.commands_by_priority).map(([priority, count]) => ({
    priority: priority as CommandPriority,
    count,
    percentage: totalCommands > 0 ? (count / totalCommands) * 100 : 0,
  }));

  // Get top command types
  const topCommandTypes = Object.entries(commandStats.commands_by_type)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([type, count]) => ({
      type: type as CommandType,
      count,
      percentage: totalCommands > 0 ? (count / totalCommands) * 100 : 0,
    }));

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Estatísticas de Comandos</Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="caption" color="text.secondary">
            Atualizado: {lastUpdated.toLocaleTimeString()}
          </Typography>
          <Tooltip title="Atualizar">
            <IconButton onClick={handleRefresh} disabled={loading} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={2}>
        {/* Summary Cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="primary">
                {totalCommands.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total de Comandos
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="success.main">
                {successRate.toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Taxa de Sucesso
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="info.main">
                {avgExecutionTime.toFixed(1)}s
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tempo Médio
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="warning.main">
                {commandStats.commands_by_status.FAILED || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Comandos Falhados
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Status Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Distribuição por Status
              </Typography>
              <Box>
                {statusPercentages.map(({ status, count, percentage }) => (
                  <Box key={status} mb={1}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getStatusIcon(status)}
                        <Typography variant="body2">
                          {getStatusLabel(status)}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body2" fontWeight="bold">
                          {count}
                        </Typography>
                        <Chip
                          label={`${percentage.toFixed(1)}%`}
                          color={getStatusColor(status)}
                          size="small"
                        />
                      </Box>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={percentage}
                      color={getStatusColor(status)}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Priority Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Distribuição por Prioridade
              </Typography>
              <Box>
                {priorityPercentages.map(({ priority, count, percentage }) => (
                  <Box key={priority} mb={1}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Typography variant="body2">
                        {getPriorityLabel(priority)}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body2" fontWeight="bold">
                          {count}
                        </Typography>
                        <Chip
                          label={`${percentage.toFixed(1)}%`}
                          color={getPriorityColor(priority)}
                          size="small"
                        />
                      </Box>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={percentage}
                      color={getPriorityColor(priority)}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Command Types */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tipos de Comando Mais Usados
              </Typography>
              <Grid container spacing={2}>
                {topCommandTypes.map(({ type, count, percentage }) => (
                  <Grid item xs={12} sm={6} md={4} lg={2.4} key={type}>
                    <Box textAlign="center">
                      <Typography variant="h6" color="primary">
                        {count}
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace">
                        {type}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {percentage.toFixed(1)}%
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
