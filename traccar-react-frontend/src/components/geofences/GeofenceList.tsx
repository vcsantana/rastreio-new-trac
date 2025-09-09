/**
 * Geofence List Component
 * Displays a list of geofences with actions
 */

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Box,
  Typography,
  TablePagination,
  Avatar
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Map as MapIcon,
  TestTube as TestIcon,
  Circle as CircleIcon,
  Square as SquareIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { Geofence } from '../../types/geofences';

interface GeofenceListProps {
  geofences: Geofence[];
  onEdit: (geofence: Geofence) => void;
  onView: (geofence: Geofence) => void;
  onDelete: (geofence: Geofence) => void;
  onTest: () => void;
}

const GeofenceList: React.FC<GeofenceListProps> = ({
  geofences,
  onEdit,
  onView,
  onDelete,
  onTest
}) => {
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(10);

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'circle':
        return <CircleIcon />;
      case 'polygon':
        return <SquareIcon />;
      case 'polyline':
        return <TimelineIcon />;
      default:
        return <MapIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'circle':
        return 'primary';
      case 'polygon':
        return 'secondary';
      case 'polyline':
        return 'success';
      default:
        return 'default';
    }
  };

  const formatArea = (area?: number) => {
    if (!area) return 'N/A';
    
    if (area < 1000) {
      return `${area.toFixed(0)} m²`;
    } else if (area < 1000000) {
      return `${(area / 1000).toFixed(1)} km²`;
    } else {
      return `${(area / 1000000).toFixed(2)} km²`;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const paginatedGeofences = geofences.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  if (geofences.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <MapIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          No geofences found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Create your first geofence to get started
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Area</TableCell>
            <TableCell>Created</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {paginatedGeofences.map((geofence) => (
            <TableRow key={geofence.id} hover>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                    {getTypeIcon(geofence.type)}
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle2" fontWeight="medium">
                      {geofence.name}
                    </Typography>
                    {geofence.description && (
                      <Typography variant="caption" color="text.secondary">
                        {geofence.description}
                      </Typography>
                    )}
                  </Box>
                </Box>
              </TableCell>
              <TableCell>
                <Chip
                  icon={getTypeIcon(geofence.type)}
                  label={geofence.type}
                  color={getTypeColor(geofence.type) as any}
                  size="small"
                  variant="outlined"
                />
              </TableCell>
              <TableCell>
                <Chip
                  label={geofence.disabled ? 'Disabled' : 'Active'}
                  color={geofence.disabled ? 'error' : 'success'}
                  size="small"
                  variant={geofence.disabled ? 'outlined' : 'filled'}
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2">
                  {formatArea(geofence.area)}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {formatDate(geofence.created_at)}
                </Typography>
              </TableCell>
              <TableCell align="center">
                <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => onView(geofence)}
                      color="primary"
                    >
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Edit">
                    <IconButton
                      size="small"
                      onClick={() => onEdit(geofence)}
                      color="primary"
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Test">
                    <IconButton
                      size="small"
                      onClick={onTest}
                      color="secondary"
                    >
                      <TestIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      onClick={() => onDelete(geofence)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <TablePagination
        rowsPerPageOptions={[5, 10, 25, 50]}
        component="div"
        count={geofences.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        labelRowsPerPage="Rows per page:"
        labelDisplayedRows={({ from, to, count }) =>
          `${from}-${to} of ${count !== -1 ? count : `more than ${to}`}`
        }
      />
    </TableContainer>
  );
};

export default GeofenceList;
