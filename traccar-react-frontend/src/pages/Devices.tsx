import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Circle as StatusIcon,
} from '@mui/icons-material';

interface Device {
  id: number;
  name: string;
  uniqueId: string;
  status: 'online' | 'offline' | 'unknown';
  lastUpdate: string;
  protocol?: string;
}

const Devices: React.FC = () => {
  // Mock data - replace with real API calls
  const devices: Device[] = [
    {
      id: 1,
      name: 'Vehicle 001',
      uniqueId: 'ST001',
      status: 'online',
      lastUpdate: '2024-01-15 10:30:00',
      protocol: 'suntech',
    },
    {
      id: 2,
      name: 'Vehicle 002',
      uniqueId: 'ST002',
      status: 'offline',
      lastUpdate: '2024-01-15 09:15:00',
      protocol: 'suntech',
    },
    {
      id: 3,
      name: 'Vehicle 003',
      uniqueId: 'GT001',
      status: 'online',
      lastUpdate: '2024-01-15 10:25:00',
      protocol: 'gt06',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    const color = status === 'online' ? 'success' : status === 'offline' ? 'error' : 'disabled';
    return <StatusIcon color={color} sx={{ fontSize: 16 }} />;
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Devices
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            // TODO: Open add device dialog
            console.log('Add device clicked');
          }}
        >
          Add Device
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Unique ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Protocol</TableCell>
              <TableCell>Last Update</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {devices.map((device) => (
              <TableRow key={device.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getStatusIcon(device.status)}
                    {device.name}
                  </Box>
                </TableCell>
                <TableCell>{device.uniqueId}</TableCell>
                <TableCell>
                  <Chip
                    label={device.status}
                    color={getStatusColor(device.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {device.protocol && (
                    <Chip
                      label={device.protocol}
                      variant="outlined"
                      size="small"
                    />
                  )}
                </TableCell>
                <TableCell>{device.lastUpdate}</TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => {
                      // TODO: Open edit device dialog
                      console.log('Edit device', device.id);
                    }}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => {
                      // TODO: Confirm and delete device
                      console.log('Delete device', device.id);
                    }}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {devices.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 2 }}>
          <Typography variant="body1" color="text.secondary">
            No devices found. Click "Add Device" to get started.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default Devices;
