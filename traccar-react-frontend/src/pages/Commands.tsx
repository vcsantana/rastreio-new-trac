import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Send as SendIcon,
  SendAndArchive as BulkSendIcon,
  Assessment as StatsIcon,
  List as ListIcon,
} from '@mui/icons-material';
import { CommandDialog } from '../components/commands/CommandDialog';
import { BulkCommandDialog } from '../components/commands/BulkCommandDialog';
import { CommandList } from '../components/commands/CommandList';
import { CommandStats } from '../components/commands/CommandStats';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`commands-tabpanel-${index}`}
      aria-labelledby={`commands-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `commands-tab-${index}`,
    'aria-controls': `commands-tabpanel-${index}`,
  };
}

const Commands: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [commandDialogOpen, setCommandDialogOpen] = useState(false);
  const [bulkCommandDialogOpen, setBulkCommandDialogOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success');

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleCommandSent = (command: any) => {
    setSnackbarMessage(`Comando ${command.command_type} enviado com sucesso!`);
    setSnackbarSeverity('success');
    setSnackbarOpen(true);
  };

  const handleBulkCommandsSent = (result: { created: number; failed: number }) => {
    if (result.failed === 0) {
      setSnackbarMessage(`${result.created} comandos enviados com sucesso!`);
      setSnackbarSeverity('success');
    } else {
      setSnackbarMessage(`${result.created} comandos enviados, ${result.failed} falharam`);
      setSnackbarSeverity('warning');
    }
    setSnackbarOpen(true);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Sistema de Comandos
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={() => setCommandDialogOpen(true)}
          >
            Enviar Comando
          </Button>
          <Button
            variant="outlined"
            startIcon={<BulkSendIcon />}
            onClick={() => setBulkCommandDialogOpen(true)}
          >
            Envio em Lote
          </Button>
        </Box>
      </Box>

      {/* Quick Stats Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <SendIcon color="primary" />
                <Box>
                  <Typography variant="h6" color="primary">
                    28
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Tipos de Comandos
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <StatsIcon color="success" />
                <Box>
                  <Typography variant="h6" color="success.main">
                    4
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Níveis de Prioridade
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <ListIcon color="info" />
                <Box>
                  <Typography variant="h6" color="info.main">
                    8
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Status de Execução
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <BulkSendIcon color="warning" />
                <Box>
                  <Typography variant="h6" color="warning.main">
                    Ilimitado
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Dispositivos Simultâneos
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="commands tabs">
            <Tab 
              label="Lista de Comandos" 
              icon={<ListIcon />} 
              iconPosition="start"
              {...a11yProps(0)} 
            />
            <Tab 
              label="Estatísticas" 
              icon={<StatsIcon />} 
              iconPosition="start"
              {...a11yProps(1)} 
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <CommandList />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <CommandStats />
        </TabPanel>
      </Card>

      {/* Dialogs */}
      <CommandDialog
        open={commandDialogOpen}
        onClose={() => setCommandDialogOpen(false)}
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
