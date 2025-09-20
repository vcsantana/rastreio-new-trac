import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Grid,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Fab,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  LocationOn as LocationIcon,
  Home as HomeIcon,
  Work as WorkIcon,
  School as SchoolIcon,
  ShoppingCart as ShoppingIcon,
  Place as PlaceIcon,
} from '@mui/icons-material';

interface Device {
  id: number;
  name: string;
  unique_id: string;
}

interface POI {
  id: number;
  name: string;
  description: string;
  latitude: number;
  longitude: number;
  radius: number;
  device_id: number;
  is_active: boolean;
  color: string;
  icon: string;
  created_at: string;
  visit_count?: number;
}

interface POIFormData {
  name: string;
  description: string;
  latitude: number | string;
  longitude: number | string;
  radius: number | string;
  device_id: number | string;
  color: string;
  icon: string;
}

const POI_ICONS = [
  { value: 'home', label: 'Casa', icon: <HomeIcon /> },
  { value: 'work', label: 'Trabalho', icon: <WorkIcon /> },
  { value: 'school', label: 'Escola', icon: <SchoolIcon /> },
  { value: 'shopping_cart', label: 'Shopping', icon: <ShoppingIcon /> },
  { value: 'location_on', label: 'Local', icon: <LocationIcon /> },
  { value: 'place', label: 'Lugar', icon: <PlaceIcon /> },
];

const POI_COLORS = [
  { value: '#4CAF50', label: 'Verde' },
  { value: '#2196F3', label: 'Azul' },
  { value: '#FF9800', label: 'Laranja' },
  { value: '#9C27B0', label: 'Roxo' },
  { value: '#F44336', label: 'Vermelho' },
  { value: '#607D8B', label: 'Cinza' },
];

const POIManagement: React.FC = () => {
  const [pois, setPois] = useState<POI[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPoi, setEditingPoi] = useState<POI | null>(null);
  const [formData, setFormData] = useState<POIFormData>({
    name: '',
    description: '',
    latitude: '',
    longitude: '',
    radius: 100,
    device_id: '',
    color: '#2196F3',
    icon: 'location_on',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      // Fetch POIs and devices in parallel
      const [poisResponse, devicesResponse] = await Promise.all([
        fetch('/api/pois/', {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch('/api/devices/', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (poisResponse.ok) {
        const poisData = await poisResponse.json();
        setPois(Array.isArray(poisData) ? poisData : []);
      }

      if (devicesResponse.ok) {
        const devicesData = await devicesResponse.json();
        setDevices(Array.isArray(devicesData) ? devicesData : []);
      }

    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (poi?: POI) => {
    if (poi) {
      setEditingPoi(poi);
      setFormData({
        name: poi.name,
        description: poi.description || '',
        latitude: poi.latitude,
        longitude: poi.longitude,
        radius: poi.radius,
        device_id: poi.device_id,
        color: poi.color,
        icon: poi.icon,
      });
    } else {
      setEditingPoi(null);
      setFormData({
        name: '',
        description: '',
        latitude: '',
        longitude: '',
        radius: 100,
        device_id: '',
        color: '#2196F3',
        icon: 'location_on',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingPoi(null);
  };

  const handleSubmit = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const url = editingPoi ? `/api/pois/${editingPoi.id}` : '/api/pois/';
      const method = editingPoi ? 'PUT' : 'POST';

      const submitData = {
        name: formData.name,
        description: formData.description,
        latitude: parseFloat(formData.latitude.toString()),
        longitude: parseFloat(formData.longitude.toString()),
        radius: parseFloat(formData.radius.toString()),
        device_id: parseInt(formData.device_id.toString()),
        color: formData.color,
        icon: formData.icon,
        is_active: true,
      };

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(submitData)
      });

      if (response.ok) {
        await fetchData();
        handleCloseDialog();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Erro ao salvar POI');
      }
    } catch (error) {
      console.error('Error saving POI:', error);
      setError('Erro ao salvar POI');
    }
  };

  const handleDelete = async (poiId: number) => {
    if (!window.confirm('Tem certeza que deseja excluir este POI?')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/pois/${poiId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchData();
      } else {
        setError('Erro ao excluir POI');
      }
    } catch (error) {
      console.error('Error deleting POI:', error);
      setError('Erro ao excluir POI');
    }
  };

  const getDeviceName = (deviceId: number) => {
    const device = devices.find(d => d.id === deviceId);
    return device ? device.name : `Device ${deviceId}`;
  };

  const getIconComponent = (iconName: string) => {
    const iconConfig = POI_ICONS.find(i => i.value === iconName);
    return iconConfig ? iconConfig.icon : <LocationIcon />;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          📍 Gerenciamento de POIs
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Novo POI
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total de POIs
              </Typography>
              <Typography variant="h5" component="div">
                {pois.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                POIs Ativos
              </Typography>
              <Typography variant="h5" component="div">
                {pois.filter(p => p.is_active).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Dispositivos com POIs
              </Typography>
              <Typography variant="h5" component="div">
                {new Set(pois.map(p => p.device_id)).size}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Tipos de POIs
              </Typography>
              <Typography variant="h5" component="div">
                {new Set(pois.map(p => p.icon)).size}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* POIs Table */}
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Nome</TableCell>
                <TableCell>Dispositivo</TableCell>
                <TableCell>Coordenadas</TableCell>
                <TableCell>Raio (m)</TableCell>
                <TableCell>Tipo</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {pois.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="textSecondary">
                      Nenhum POI cadastrado
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                pois.map((poi) => (
                  <TableRow key={poi.id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ color: poi.color }}>
                          {getIconComponent(poi.icon)}
                        </Box>
                        <Box>
                          <Typography variant="body2" fontWeight="bold">
                            {poi.name}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {poi.description}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>{getDeviceName(poi.device_id)}</TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {poi.latitude.toFixed(6)}, {poi.longitude.toFixed(6)}
                      </Typography>
                    </TableCell>
                    <TableCell>{poi.radius}m</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={POI_ICONS.find(i => i.value === poi.icon)?.label || poi.icon}
                        style={{ backgroundColor: poi.color, color: 'white' }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={poi.is_active ? 'Ativo' : 'Inativo'}
                        color={poi.is_active ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(poi)}
                        color="primary"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(poi.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingPoi ? 'Editar POI' : 'Novo POI'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Nome"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Dispositivo</InputLabel>
                <Select
                  value={formData.device_id}
                  onChange={(e) => setFormData({ ...formData, device_id: e.target.value })}
                  label="Dispositivo"
                >
                  {devices.map((device) => (
                    <MenuItem key={device.id} value={device.id}>
                      {device.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Descrição"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Latitude"
                type="number"
                value={formData.latitude}
                onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                required
                inputProps={{ step: 'any' }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Longitude"
                type="number"
                value={formData.longitude}
                onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                required
                inputProps={{ step: 'any' }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Raio (metros)"
                type="number"
                value={formData.radius}
                onChange={(e) => setFormData({ ...formData, radius: e.target.value })}
                required
                inputProps={{ min: 10, max: 1000 }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo/Ícone</InputLabel>
                <Select
                  value={formData.icon}
                  onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                  label="Tipo/Ícone"
                >
                  {POI_ICONS.map((iconConfig) => (
                    <MenuItem key={iconConfig.value} value={iconConfig.value}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {iconConfig.icon}
                        {iconConfig.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Cor</InputLabel>
                <Select
                  value={formData.color}
                  onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                  label="Cor"
                >
                  {POI_COLORS.map((colorConfig) => (
                    <MenuItem key={colorConfig.value} value={colorConfig.value}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                          sx={{
                            width: 20,
                            height: 20,
                            backgroundColor: colorConfig.value,
                            borderRadius: '50%',
                          }}
                        />
                        {colorConfig.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancelar</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingPoi ? 'Atualizar' : 'Criar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button for mobile */}
      <Fab
        color="primary"
        aria-label="add"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          display: { xs: 'flex', sm: 'none' }
        }}
        onClick={() => handleOpenDialog()}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};

export default POIManagement;
