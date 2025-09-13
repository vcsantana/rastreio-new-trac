/**
 * Geofences Management Page
 * Based on traccar-web GeofencesPage - sidebar with list + map for editing
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Toolbar,
  Typography,
  IconButton,
  Tooltip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert
} from '@mui/material';
import {
  UploadFile as UploadFileIcon,
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useGeofences } from '../hooks/useGeofences';
import { Geofence } from '../types/geofences';
import GeofenceList from '../components/geofences/GeofenceList';
import MapView from '../components/map/MapView';
import MapGeofenceEdit from '../components/map/MapGeofenceEdit';
import MapCurrentLocation from '../components/map/MapCurrentLocation';
import MapGeocoder from '../components/map/MapGeocoder';
import MapScale from '../components/map/MapScale';

const Geofences: React.FC = () => {
  const navigate = useNavigate();
  const { geofences, loading, error, fetchGeofences, deleteGeofence, clearError } = useGeofences();

  const [selectedGeofenceId, setSelectedGeofenceId] = useState<number | undefined>();

  // State for dialogs
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    geofence?: Geofence;
  }>({
    open: false
  });

  // Load geofences on mount
  React.useEffect(() => {
    fetchGeofences();
  }, [fetchGeofences]);

  // Handle GPX file upload
  const handleFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const [file] = files;
    const reader = new FileReader();

    reader.onload = async () => {
      const xml = new DOMParser().parseFromString(reader.result as string, 'text/xml');
      const segment = xml.getElementsByTagName('trkseg')[0];
      const coordinates = Array.from(segment.getElementsByTagName('trkpt'))
        .map((point) => `${point.getAttribute('lat')} ${point.getAttribute('lon')}`)
        .join(', ');

      const area = `LINESTRING (${coordinates})`;
      const newItem = { name: 'GPX Route', area, type: 'polyline' };

      try {
        const response = await fetch('http://localhost:8000/api/geofences', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify(newItem),
        });

        if (!response.ok) {
          throw new Error(`Failed to upload GPX: ${response.statusText}`);
        }

        const item = await response.json();
        fetchGeofences();
        navigate(`/geofences/${item.id}`);
      } catch (error) {
        console.error('Failed to upload GPX:', error);
      }
    };

    reader.onerror = (event) => {
      console.error('File read error:', event);
    };

    if (file) {
      reader.readAsText(file);
    }
  };

  // Handle geofence selection
  const handleGeofenceSelected = (geofenceId: number) => {
    setSelectedGeofenceId(geofenceId);
  };

  // Handle edit geofence
  const handleEditGeofence = (geofence: Geofence) => {
    navigate(`/geofences/${geofence.id}`);
  };

  // Handle delete geofence
  const handleDeleteGeofence = (geofence: Geofence) => {
    setDeleteDialog({ open: true, geofence });
  };

  // Confirm delete
  const confirmDelete = async () => {
    if (deleteDialog.geofence) {
      try {
        await deleteGeofence(deleteDialog.geofence.id);
        setDeleteDialog({ open: false });
        fetchGeofences();
      } catch (err) {
        // Error is handled by the hook
      }
    }
  };

  return (
    <Box sx={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Box sx={{
        display: 'flex',
        flex: 1,
        overflow: 'hidden'
      }}>
        {/* Sidebar */}
        <Paper
          square
          elevation={3}
          sx={{
            display: 'flex',
            flexDirection: 'column',
            width: 350,
            zIndex: 1
          }}
        >
          <Toolbar>
            <IconButton
              edge="start"
              sx={{ mr: 2 }}
              onClick={() => navigate(-1)}
            >
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Geofences
            </Typography>
            <label htmlFor="upload-gpx">
              <input
                accept=".gpx"
                id="upload-gpx"
                type="file"
                style={{ display: 'none' }}
                onChange={handleFile}
              />
              <IconButton edge="end" component="span">
                <Tooltip title="Upload GPX">
                  <UploadFileIcon />
                </Tooltip>
              </IconButton>
            </label>
          </Toolbar>
          <Divider />

          {error && (
            <Alert severity="error" sx={{ m: 1 }} onClose={clearError}>
              {error}
            </Alert>
          )}

          <GeofenceList
            geofences={geofences}
            onGeofenceSelected={handleGeofenceSelected}
            onEdit={handleEditGeofence}
            onDelete={handleDeleteGeofence}
          />
        </Paper>

        {/* Map */}
        <Box sx={{ flex: 1, position: 'relative' }}>
          <MapView>
            <MapGeofenceEdit selectedGeofenceId={selectedGeofenceId} />
          </MapView>
          <MapScale />
          <MapCurrentLocation />
          <MapGeocoder />
        </Box>
      </Box>

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
