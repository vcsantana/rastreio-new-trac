/**
 * Geofence List Component
 * Displays a list of geofences with actions (based on traccar-web)
 */

import React from 'react';
import {
  List,
  ListItemButton,
  ListItemText,
  Divider,
  Box,
  IconButton,
  Tooltip,
  Typography
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { Geofence } from '../../types/geofences';

interface GeofenceListProps {
  geofences: Geofence[];
  onGeofenceSelected: (geofenceId: number) => void;
  onEdit: (geofence: Geofence) => void;
  onDelete: (geofence: Geofence) => void;
}

const GeofenceList: React.FC<GeofenceListProps> = ({
  geofences,
  onGeofenceSelected,
  onEdit,
  onDelete
}) => {
  if (geofences.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          No geofences found
        </Typography>
      </Box>
    );
  }

  return (
    <List sx={{ flexGrow: 1, overflow: 'auto' }}>
      {Object.values(geofences).map((geofence: Geofence, index: number, list: Geofence[]) => (
        <React.Fragment key={geofence.id}>
          <ListItemButton onClick={() => onGeofenceSelected(geofence.id)}>
            <ListItemText primary={geofence.name} />
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <Tooltip title="Edit">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(geofence);
                  }}
                  color="primary"
                >
                  <EditIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(geofence);
                  }}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </ListItemButton>
          {index < list.length - 1 ? <Divider /> : null}
        </React.Fragment>
      ))}
    </List>
  );
};

export default GeofenceList;
