import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
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
  Grid,
  Alert,
  CircularProgress,
  Tooltip,
  Menu,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
  Security as SecurityIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useUsers, User, UserStats, UserCreate, UserUpdate, UserPermission } from '../hooks/useUsers';
import { useDevices, Device } from '../hooks/useDevices';
import { useGroups, Group } from '../hooks/useGroups';
import { usePersons, Person } from '../hooks/usePersons';
import { useAuth } from '../contexts/AuthContext';

const Users: React.FC = () => {
  const { user: currentUser } = useAuth();
  const {
    users,
    loading,
    error,
    setError,
    fetchUsers,
    fetchUserStats,
    createUser,
    updateUser,
    deleteUser,
    fetchUserPermissions,
    updateUserPermissions,
  } = useUsers();
  
  const { devices, fetchDevices } = useDevices();
  const { groups, fetchGroups } = useGroups();
  const { persons, fetchPersons } = usePersons();

  const [stats, setStats] = useState<UserStats | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userPermissions, setUserPermissions] = useState<UserPermission | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [roleFilter, setRoleFilter] = useState<'all' | 'admin' | 'user'>('all');
  const [actionLoading, setActionLoading] = useState(false);
  
  // Permission states
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<number[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([]);
  const [selectedManagedUserIds, setSelectedManagedUserIds] = useState<number[]>([]);
  const [permissionsLoading, setPermissionsLoading] = useState(false);

  // Form states
  const [formData, setFormData] = useState<UserCreate>({
    email: '',
    name: '',
    password: '',
    is_active: true,
    is_admin: false,
    device_limit: -1,
    user_limit: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    await Promise.all([
      fetchUsers(),
      loadStats(),
      fetchDevices(),
      fetchGroups(),
      fetchPersons(),
    ]);
  };

  const loadStats = async () => {
    const statsData = await fetchUserStats();
    setStats(statsData);
  };

  const handleCreateUser = async () => {
    console.log('handleCreateUser called with formData:', formData);
    
    // Validate required fields
    if (!formData.email || !formData.name || !formData.password) {
      console.log('Validation failed - missing required fields');
      setError('Please fill in all required fields');
      return;
    }
    
    setActionLoading(true);
    setError(null);
    
    try {
      console.log('Calling createUser with:', formData);
      const newUser = await createUser(formData);
      console.log('createUser result:', newUser);
      
      if (newUser) {
        console.log('User created successfully, closing dialog');
        setCreateDialogOpen(false);
        setFormData({
          email: '',
          name: '',
          password: '',
          is_active: true,
          is_admin: false,
          device_limit: -1,
          user_limit: 0,
        });
        loadData();
      } else {
        console.log('User creation failed - newUser is null');
      }
    } catch (error) {
      console.error('Error in handleCreateUser:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    
    setActionLoading(true);
    setError(null);
    
    try {
      const updateData: UserUpdate = {
        ...formData,
        password: formData.password || undefined,
      };
      
      const updatedUser = await updateUser(selectedUser.id, updateData);
      
      if (updatedUser) {
        setEditDialogOpen(false);
        setSelectedUser(null);
        loadData();
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    
    const success = await deleteUser(selectedUser.id);
    if (success) {
      setDeleteDialogOpen(false);
      setSelectedUser(null);
      loadData();
    }
  };

  const handleViewPermissions = async (user: User) => {
    setSelectedUser(user);
    setPermissionsLoading(true);
    
    try {
      const permissions = await fetchUserPermissions(user.id);
      setUserPermissions(permissions);
      
      // Set current selections
      if (permissions) {
        setSelectedDeviceIds(permissions.device_permissions.map(d => d.id));
        setSelectedGroupIds(permissions.group_permissions.map(g => g.id));
        setSelectedManagedUserIds(permissions.managed_users.map(u => u.id));
      }
      
      setPermissionsDialogOpen(true);
    } catch (error) {
      console.error('Error fetching permissions:', error);
    } finally {
      setPermissionsLoading(false);
    }
  };

  const handleSavePermissions = async () => {
    if (!selectedUser) return;
    
    setPermissionsLoading(true);
    setError(null);
    
    try {
      const success = await updateUserPermissions(selectedUser.id, {
        device_ids: selectedDeviceIds,
        group_ids: selectedGroupIds,
        managed_user_ids: selectedManagedUserIds,
      });
      
      if (success) {
        setPermissionsDialogOpen(false);
        // Refresh permissions
        const updatedPermissions = await fetchUserPermissions(selectedUser.id);
        setUserPermissions(updatedPermissions);
      }
    } finally {
      setPermissionsLoading(false);
    }
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, user: User) => {
    setAnchorEl(event.currentTarget);
    setSelectedUser(user);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    // Don't clear selectedUser immediately - let the individual handlers do it
  };

  const handleEditClick = () => {
    if (selectedUser) {
      setFormData({
        email: selectedUser.email,
        name: selectedUser.name,
        password: '',
        is_active: selectedUser.is_active,
        is_admin: selectedUser.is_admin,
        phone: selectedUser.phone || '',
        map: selectedUser.map || '',
        latitude: selectedUser.latitude || '0',
        longitude: selectedUser.longitude || '0',
        zoom: selectedUser.zoom || 0,
        coordinate_format: selectedUser.coordinate_format || '',
        device_limit: selectedUser.device_limit || -1,
        user_limit: selectedUser.user_limit || 0,
        device_readonly: selectedUser.device_readonly || false,
        limit_commands: selectedUser.limit_commands || false,
        disable_reports: selectedUser.disable_reports || false,
        fixed_email: selectedUser.fixed_email || false,
        poi_layer: selectedUser.poi_layer || '',
      });
      setEditDialogOpen(true);
      handleMenuClose();
    }
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && user.is_active) ||
                         (statusFilter === 'inactive' && !user.is_active);
    const matchesRole = roleFilter === 'all' ||
                       (roleFilter === 'admin' && user.is_admin) ||
                       (roleFilter === 'user' && !user.is_admin);
    
    return matchesSearch && matchesStatus && matchesRole;
  });

  const StatCard: React.FC<{ title: string; value: number; color: string; icon: React.ReactNode }> = ({ title, value, color, icon }) => (
    <Card sx={{ minWidth: 200, background: `linear-gradient(135deg, ${color}20, ${color}10)` }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" component="div" color={color}>
              {value}
            </Typography>
          </Box>
          <Box color={color}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (!currentUser?.is_admin) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Access denied. Admin privileges required to manage users.
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          User Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            console.log('Add User button clicked');
            setCreateDialogOpen(true);
          }}
        >
          Add User
        </Button>
      </Box>

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Total Users"
              value={stats.total_users}
              color="#1976d2"
              icon={<PersonIcon sx={{ fontSize: 40 }} />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Active Users"
              value={stats.active_users}
              color="#2e7d32"
              icon={<PersonIcon sx={{ fontSize: 40 }} />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Administrators"
              value={stats.admin_users}
              color="#ed6c02"
              icon={<AdminIcon sx={{ fontSize: 40 }} />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Inactive Users"
              value={stats.inactive_users}
              color="#d32f2f"
              icon={<PersonIcon sx={{ fontSize: 40 }} />}
            />
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search users"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by name or email..."
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value as any)}
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="admin">Administrator</MenuItem>
                  <MenuItem value="user">User</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {loading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Device Limit</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          {user.is_admin ? (
                            <AdminIcon color="warning" sx={{ mr: 1 }} />
                          ) : (
                            <PersonIcon color="primary" sx={{ mr: 1 }} />
                          )}
                          {user.name}
                        </Box>
                      </TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Chip
                          label={user.is_active ? 'Active' : 'Inactive'}
                          color={user.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={user.is_admin ? 'Admin' : 'User'}
                          color={user.is_admin ? 'warning' : 'primary'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {user.device_limit === -1 ? 'Unlimited' : user.device_limit}
                      </TableCell>
                      <TableCell>
                        {new Date(user.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="More actions">
                          <IconButton
                            onClick={(e) => handleMenuClick(e, user)}
                            size="small"
                          >
                            <MoreVertIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEditClick}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit User</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => {
          handleViewPermissions(selectedUser!);
          handleMenuClose();
        }}>
          <ListItemIcon>
            <SecurityIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Permissions</ListItemText>
        </MenuItem>
        {selectedUser?.id !== currentUser?.id && (
          <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Delete User</ListItemText>
          </MenuItem>
        )}
      </Menu>

      {/* Create User Dialog */}
      <Dialog open={createDialogOpen} onClose={() => {
        console.log('Create dialog closed');
        setCreateDialogOpen(false);
      }} maxWidth="md" fullWidth>
        <DialogTitle>Create New User</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Device Limit"
                type="number"
                value={formData.device_limit}
                onChange={(e) => setFormData({ ...formData, device_limit: parseInt(e.target.value) || -1 })}
                helperText="-1 for unlimited"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="User Limit"
                type="number"
                value={formData.user_limit}
                onChange={(e) => setFormData({ ...formData, user_limit: parseInt(e.target.value) || 0 })}
                helperText="0 for no management rights"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                }
                label="Active"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_admin}
                    onChange={(e) => setFormData({ ...formData, is_admin: e.target.checked })}
                  />
                }
                label="Administrator"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)} disabled={actionLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleCreateUser} 
            variant="contained" 
            disabled={actionLoading}
            startIcon={actionLoading ? <CircularProgress size={20} /> : null}
          >
            {actionLoading ? 'Creating...' : 'Create User'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                helperText="Leave blank to keep current password"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Device Limit"
                type="number"
                value={formData.device_limit}
                onChange={(e) => setFormData({ ...formData, device_limit: parseInt(e.target.value) || -1 })}
                helperText="-1 for unlimited"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="User Limit"
                type="number"
                value={formData.user_limit}
                onChange={(e) => setFormData({ ...formData, user_limit: parseInt(e.target.value) || 0 })}
                helperText="0 for no management rights"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                }
                label="Active"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_admin}
                    onChange={(e) => setFormData({ ...formData, is_admin: e.target.checked })}
                  />
                }
                label="Administrator"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)} disabled={actionLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleUpdateUser} 
            variant="contained" 
            disabled={actionLoading}
            startIcon={actionLoading ? <CircularProgress size={20} /> : null}
          >
            {actionLoading ? 'Updating...' : 'Update User'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Permissions Dialog */}
      <Dialog open={permissionsDialogOpen} onClose={() => setPermissionsDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>User Permissions - {selectedUser?.name}</DialogTitle>
        <DialogContent>
          {permissionsLoading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3} sx={{ mt: 1 }}>
              {/* Device Permissions */}
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Device Permissions
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Select Devices</InputLabel>
                  <Select
                    multiple
                    value={selectedDeviceIds}
                    onChange={(e) => setSelectedDeviceIds(e.target.value as number[])}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => {
                          const device = devices.find(d => d.id === value);
                          return (
                            <Chip key={value} label={device?.name || `Device ${value}`} size="small" />
                          );
                        })}
                      </Box>
                    )}
                  >
                    {devices.map((device) => (
                      <MenuItem key={device.id} value={device.id}>
                        <Box>
                          <Typography variant="body2">{device.name}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {device.unique_id} - {device.model || 'No model'}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Group Permissions */}
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Group Permissions
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Select Groups</InputLabel>
                  <Select
                    multiple
                    value={selectedGroupIds}
                    onChange={(e) => setSelectedGroupIds(e.target.value as number[])}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => {
                          const group = groups.find(g => g.id === value);
                          return (
                            <Chip key={value} label={group?.name || `Group ${value}`} size="small" />
                          );
                        })}
                      </Box>
                    )}
                  >
                    {groups.map((group) => (
                      <MenuItem key={group.id} value={group.id}>
                        <Box>
                          <Typography variant="body2">{group.name}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {group.description || 'No description'} - {group.device_count || 0} devices
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Managed Users */}
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Managed Users
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Select Managed Users</InputLabel>
                  <Select
                    multiple
                    value={selectedManagedUserIds}
                    onChange={(e) => setSelectedManagedUserIds(e.target.value as number[])}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => {
                          const user = users.find(u => u.id === value);
                          return (
                            <Chip key={value} label={user?.name || `User ${value}`} size="small" />
                          );
                        })}
                      </Box>
                    )}
                  >
                    {users.filter(u => u.id !== selectedUser?.id).map((user) => (
                      <MenuItem key={user.id} value={user.id}>
                        <Box>
                          <Typography variant="body2">{user.name}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {user.email} - {user.is_admin ? 'Admin' : 'User'}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Current Permissions Summary */}
              {userPermissions && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Current Permissions Summary
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" color="primary">
                            Device Permissions
                          </Typography>
                          <Typography variant="h4">{selectedDeviceIds.length}</Typography>
                          <Typography variant="caption">
                            {selectedDeviceIds.length > 0 
                              ? `${selectedDeviceIds.length} device(s) selected`
                              : 'No devices selected'
                            }
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" color="primary">
                            Group Permissions
                          </Typography>
                          <Typography variant="h4">{selectedGroupIds.length}</Typography>
                          <Typography variant="caption">
                            {selectedGroupIds.length > 0 
                              ? `${selectedGroupIds.length} group(s) selected`
                              : 'No groups selected'
                            }
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" color="primary">
                            Managed Users
                          </Typography>
                          <Typography variant="h4">{selectedManagedUserIds.length}</Typography>
                          <Typography variant="caption">
                            {selectedManagedUserIds.length > 0 
                              ? `${selectedManagedUserIds.length} user(s) managed`
                              : 'No users managed'
                            }
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPermissionsDialogOpen(false)} disabled={permissionsLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleSavePermissions} 
            variant="contained" 
            disabled={permissionsLoading}
            startIcon={permissionsLoading ? <CircularProgress size={20} /> : null}
          >
            {permissionsLoading ? 'Saving...' : 'Save Permissions'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete User</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete user "{selectedUser?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteUser} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Users;
