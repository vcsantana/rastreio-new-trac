import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Alert,
  CircularProgress,
  Button,
  IconButton,
  Chip
} from '@mui/material';
import { Add, Edit, Delete, Send } from '@mui/icons-material';
import { useSelector } from 'react-redux';

const CommandsPage = () => {
  const user = useSelector((state) => state.auth.user);
  const [commands, setCommands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCommands = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/commands', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setCommands(data);
        } else {
          setError('Failed to fetch commands');
        }
      } catch (err) {
        setError('Network error. Please check if the API is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchCommands();
  }, []);

  const getCommandTypeColor = (type) => {
    const colors = {
      'engineStop': 'error',
      'engineResume': 'success',
      'alarmArm': 'warning',
      'alarmDisarm': 'info',
      'default': 'default'
    };
    return colors[type] || 'default';
  };

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Commands
        </Typography>
        <Button variant="contained" color="primary" startIcon={<Add />}>
          Add Command
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Parameters</TableCell>
              <TableCell>Send SMS</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {commands.length > 0 ? (
              commands.map((command) => (
                <TableRow key={command.id}>
                  <TableCell>{command.id}</TableCell>
                  <TableCell>{command.description}</TableCell>
                  <TableCell>
                    <Chip 
                      label={command.type || 'Unknown'} 
                      color={getCommandTypeColor(command.type)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {command.parameters ? JSON.stringify(command.parameters) : 'None'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={command.text_channel ? 'Yes' : 'No'} 
                      color={command.text_channel ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton size="small" color="primary">
                      <Send />
                    </IconButton>
                    <IconButton size="small" color="primary">
                      <Edit />
                    </IconButton>
                    <IconButton size="small" color="error">
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No commands found
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default CommandsPage;
