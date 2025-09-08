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
import { Add, Edit, Delete, People } from '@mui/icons-material';
import { useSelector } from 'react-redux';

const GroupsPage = () => {
  const user = useSelector((state) => state.auth.user);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/groups', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setGroups(data);
        } else {
          setError('Failed to fetch groups');
        }
      } catch (err) {
        setError('Network error. Please check if the API is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchGroups();
  }, []);

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
          Groups
        </Typography>
        <Button variant="contained" color="primary" startIcon={<Add />}>
          Add Group
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
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Devices</TableCell>
              <TableCell>Users</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.length > 0 ? (
              groups.map((group) => (
                <TableRow key={group.id}>
                  <TableCell>{group.id}</TableCell>
                  <TableCell>{group.name}</TableCell>
                  <TableCell>{group.description || 'No description'}</TableCell>
                  <TableCell>
                    <Chip 
                      label={group.device_count || 0} 
                      color="primary"
                      size="small"
                      icon={<People />}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={group.user_count || 0} 
                      color="secondary"
                      size="small"
                      icon={<People />}
                    />
                  </TableCell>
                  <TableCell>
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
                    No groups found
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

export default GroupsPage;

