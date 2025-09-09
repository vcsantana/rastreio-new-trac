/**
 * Geofences Management Page
 * Main page for managing geofences with list, filters, and actions
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Tooltip,
  Fab
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Map as MapIcon,
  TestTube as TestIcon,
  Refresh as RefreshIcon,
  GetApp as ExportIcon
} from '@mui/icons-material';
import { useGeofences } from '../hooks/useGeofences';
import { Geofence, GeofenceFilters } from '../types/geofences';
import GeofenceList from '../components/geofences/GeofenceList';
import GeofenceDialog from '../components/geofences/GeofenceDialog';
import GeofenceTestDialog from '../components/geofences/GeofenceTestDialog';
import GeofenceStats from '../components/geofences/GeofenceStats';

const Geofences: React.FC = () => {
  const {
    geofences,
    stats,
    loading,
    loadingStats,
    error,
    fetchGeofences,
    fetchStats,
    deleteGeofence,
    clearError
  } = useGeofences();

  // State for filters and search
  const [filters, setFilters] = useState<GeofenceFilters>({
    page: 1,
    size: 50
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // State for dialogs
  const [geofenceDialog, setGeofenceDialog] = useState<{
    open: boolean;
    mode: 'create' | 'edit' | 'view';
    geofence?: Geofence;
  }>({
    open: false,
    mode: 'create'
  });
  const [testDialog, setTestDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    geofence?: Geofence;
  }>({
    open: false
  });

  // Load initial data
  useEffect(() => {
    fetchGeofences(filters);
    fetchStats();
  }, [fetchGeofences, fetchStats]);

  // Handle search
  const handleSearch = () => {
    const newFilters = {
      ...filters,
      search: searchTerm || undefined,
      page: 1 // Reset to first page when searching
    };
    setFilters(newFilters);
    fetchGeofences(newFilters);
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof GeofenceFilters, value: any) => {
    const newFilters = {
      ...filters,
      [key]: value,
      page: 1 // Reset to first page when filtering
    };
    setFilters(newFilters);
    fetchGeofences(newFilters);
  };

  // Clear all filters
  const clearFilters = () => {
    const clearedFilters = { page: 1, size: 50 };
    setFilters(clearedFilters);
    setSearchTerm('');
    fetchGeofences(clearedFilters);
  };

  // Handle geofence actions
  const handleCreateGeofence = () => {
    setGeofenceDialog({ open: true, mode: 'create' });
  };

  const handleEditGeofence = (geofence: Geofence) => {
    setGeofenceDialog({ open: true, mode: 'edit', geofence });
  };

  const handleViewGeofence = (geofence: Geofence) => {
    setGeofenceDialog({ open: true, mode: 'view', geofence });
  };

  const handleDeleteGeofence = (geofence: Geofence) => {
    setDeleteDialog({ open: true, geofence });
  };

  const confirmDelete = async () => {
    if (deleteDialog.geofence) {
      try {
        await deleteGeofence(deleteDialog.geofence.id);
        setDeleteDialog({ open: false });
        // Refresh the list
        fetchGeofences(filters);
        fetchStats();
      } catch (err) {
        // Error is handled by the hook
      }
    }
  };

  // Handle dialog close
  const handleDialogClose = () => {
    setGeofenceDialog({ open: false, mode: 'create' });
    // Refresh the list
    fetchGeofences(filters);
    fetchStats();
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchGeofences(filters);
    fetchStats();
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    const newFilters = { ...filters, page };
    setFilters(newFilters);
    fetchGeofences(newFilters);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Geofences
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateGeofence}
          >
            New Geofence
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={clearError}>
          {error}
        </Alert>
      )}

      {/* Statistics */}
      {stats && (
        <GeofenceStats stats={stats} loading={loadingStats} />
      )}

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search geofences..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Button
                  variant="outlined"
                  startIcon={<SearchIcon />}
                  onClick={handleSearch}
                  disabled={loading}
                >
                  Search
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<FilterIcon />}
                  onClick={() => setShowFilters(!showFilters)}
                >
                  Filters
                </Button>
                <Button
                  variant="outlined"
                  onClick={clearFilters}
                >
                  Clear
                </Button>
              </Box>
            </Grid>
          </Grid>

          {/* Advanced Filters */}
          {showFilters && (
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Type</InputLabel>
                    <Select
                      value={filters.type || ''}
                      onChange={(e) => handleFilterChange('type', e.target.value || undefined)}
                      label="Type"
                    >
                      <MenuItem value="">All Types</MenuItem>
                      <MenuItem value="polygon">Polygon</MenuItem>
                      <MenuItem value="circle">Circle</MenuItem>
                      <MenuItem value="polyline">Polyline</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Status</InputLabel>
                    <Select
                      value={filters.disabled === undefined ? '' : filters.disabled.toString()}
                      onChange={(e) => handleFilterChange('disabled', e.target.value === '' ? undefined : e.target.value === 'true')}
                      label="Status"
                    >
                      <MenuItem value="">All Status</MenuItem>
                      <MenuItem value="false">Active</MenuItem>
                      <MenuItem value="true">Disabled</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <TextField
                    fullWidth
                    label="Page Size"
                    type="number"
                    value={filters.size || 50}
                    onChange={(e) => handleFilterChange('size', parseInt(e.target.value) || 50)}
                    inputProps={{ min: 10, max: 1000 }}
                  />
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Geofences List */}
      <Card>
        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <GeofenceList
              geofences={geofences}
              onEdit={handleEditGeofence}
              onView={handleViewGeofence}
              onDelete={handleDeleteGeofence}
              onTest={() => setTestDialog(true)}
            />
          )}
        </CardContent>
      </Card>

      {/* Geofence Dialog */}
      <GeofenceDialog
        open={geofenceDialog.open}
        mode={geofenceDialog.mode}
        geofence={geofenceDialog.geofence}
        onClose={handleDialogClose}
      />

      {/* Test Dialog */}
      <GeofenceTestDialog
        open={testDialog}
        onClose={() => setTestDialog(false)}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false })}>
        <DialogTitle>Delete Geofence</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the geofence "{deleteDialog.geofence?.name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false })}>
            Cancel
          </Button>
          <Button onClick={confirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Geofences;
