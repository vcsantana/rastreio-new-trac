import React, { useState, useMemo, useEffect } from 'react';
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
  Alert,
  CircularProgress,
  Tooltip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  InputAdornment,
  Collapse,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Block as DisableIcon,
  CheckCircle as EnableIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useGroups, Group } from '../hooks/useGroups';
import GroupDialog from '../components/common/GroupDialog';
import ConfirmDialog from '../components/common/ConfirmDialog';

const Groups: React.FC = () => {
  const {
    groups,
    loading,
    error,
    fetchGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    toggleGroupStatus,
  } = useGroups();

  // Load groups on component mount
  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  // Dialog states
  const [groupDialogOpen, setGroupDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [confirmAction, setConfirmAction] = useState<'delete' | 'disable' | 'enable'>('delete');

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [personFilter, setPersonFilter] = useState<string>('all');
  const [filtersExpanded, setFiltersExpanded] = useState(false);

  // Get unique values for filter options
  const uniquePersons = useMemo(() => {
    const persons = groups.map(g => g.person_name).filter(Boolean);
    return Array.from(new Set(persons));
  }, [groups]);

  // Organize groups in hierarchical order
  const hierarchicalGroups = useMemo(() => {
    const groupMap = new Map(groups.map(group => [group.id, group]));
    const rootGroups: Group[] = [];
    const childGroups: Group[] = [];
    
    // Separate root groups (no parent) from child groups
    groups.forEach(group => {
      if (!group.parent_id) {
        rootGroups.push(group);
      } else {
        childGroups.push(group);
      }
    });
    
    // Sort groups by level and name
    const sortedGroups = [...rootGroups, ...childGroups].sort((a, b) => {
      // First sort by level
      const levelA = a.level || 0;
      const levelB = b.level || 0;
      if (levelA !== levelB) {
        return levelA - levelB;
      }
      // Then sort by name
      return a.name.localeCompare(b.name);
    });
    
    return sortedGroups;
  }, [groups]);

  // Filter groups based on current filters
  const filteredGroups = useMemo(() => {
    return hierarchicalGroups.filter(group => {
      // Search term filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = 
          group.name.toLowerCase().includes(searchLower) ||
          (group.description && group.description.toLowerCase().includes(searchLower)) ||
          (group.person_name && group.person_name.toLowerCase().includes(searchLower)) ||
          (group.parent_name && group.parent_name.toLowerCase().includes(searchLower));
        if (!matchesSearch) return false;
      }

      // Status filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'enabled' && group.disabled) return false;
        if (statusFilter === 'disabled' && !group.disabled) return false;
      }

      // Person filter
      if (personFilter !== 'all' && group.person_name !== personFilter) {
        return false;
      }

      return true;
    });
  }, [hierarchicalGroups, searchTerm, statusFilter, personFilter]);

  // Clear all filters
  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setPersonFilter('all');
  };

  // Check if any filters are active
  const hasActiveFilters = searchTerm || statusFilter !== 'all' || personFilter !== 'all';

  const getStatusColor = (disabled: boolean) => {
    return disabled ? 'default' : 'success';
  };

  const getStatusIcon = (disabled: boolean) => {
    return disabled ? (
      <DisableIcon color="disabled" sx={{ fontSize: 16 }} />
    ) : (
      <EnableIcon color="success" sx={{ fontSize: 16 }} />
    );
  };

  // Dialog handlers
  const handleAddGroup = () => {
    setDialogMode('create');
    setSelectedGroup(null);
    setGroupDialogOpen(true);
  };

  const handleEditGroup = (group: Group) => {
    setDialogMode('edit');
    setSelectedGroup(group);
    setGroupDialogOpen(true);
  };

  const handleSaveGroup = async (groupData: any) => {
    if (dialogMode === 'create') {
      await createGroup(groupData);
    } else if (selectedGroup) {
      await updateGroup(selectedGroup.id, groupData);
    }
    setGroupDialogOpen(false);
  };

  const handleDeleteGroup = (group: Group) => {
    setSelectedGroup(group);
    setConfirmAction('delete');
    setConfirmDialogOpen(true);
  };

  const handleToggleStatus = (group: Group) => {
    setSelectedGroup(group);
    setConfirmAction(group.disabled ? 'enable' : 'disable');
    setConfirmDialogOpen(true);
  };

  const handleConfirmAction = async () => {
    if (!selectedGroup) return;

    switch (confirmAction) {
      case 'delete':
        await deleteGroup(selectedGroup.id);
        break;
      case 'disable':
      case 'enable':
        await toggleGroupStatus(selectedGroup.id);
        break;
    }
    setConfirmDialogOpen(false);
  };

  const getConfirmMessage = () => {
    if (!selectedGroup) return '';
    
    switch (confirmAction) {
      case 'delete':
        return `Are you sure you want to delete the group "${selectedGroup.name}"? This action cannot be undone.`;
      case 'disable':
        return `Are you sure you want to disable the group "${selectedGroup.name}"?`;
      case 'enable':
        return `Are you sure you want to enable the group "${selectedGroup.name}"?`;
      default:
        return '';
    }
  };

  const getConfirmTitle = () => {
    switch (confirmAction) {
      case 'delete':
        return 'Delete Group';
      case 'disable':
        return 'Disable Group';
      case 'enable':
        return 'Enable Group';
      default:
        return 'Confirm Action';
    }
  };

  if (loading && groups.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Groups ({filteredGroups.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setFiltersExpanded(!filtersExpanded)}
            color={hasActiveFilters ? 'primary' : 'inherit'}
          >
            Filters {hasActiveFilters && `(${[
              searchTerm && 'Search',
              statusFilter !== 'all' && 'Status',
              personFilter !== 'all' && 'Person'
            ].filter(Boolean).length})`}
          </Button>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={clearFilters}
              size="small"
            >
              Clear
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddGroup}
          >
            Add Group
          </Button>
        </Box>
      </Box>

      {/* Filters Section */}
      <Collapse in={filtersExpanded}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filter Groups
          </Typography>
          <Grid container spacing={2}>
            {/* Search */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Search groups"
                placeholder="Search by name, description, or person..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                size="small"
              />
            </Grid>

            {/* Status Filter */}
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="enabled">Enabled</MenuItem>
                  <MenuItem value="disabled">Disabled</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Person Filter */}
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Person</InputLabel>
                <Select
                  value={personFilter}
                  label="Person"
                  onChange={(e) => setPersonFilter(e.target.value)}
                >
                  <MenuItem value="all">All Persons</MenuItem>
                  {uniquePersons.map(person => (
                    <MenuItem key={person} value={person}>
                      {person}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
      </Collapse>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Parent</TableCell>
                <TableCell>Person</TableCell>
                <TableCell>Devices</TableCell>
                <TableCell>Children</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredGroups.map((group) => (
                <TableRow key={group.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {/* Hierarchical indentation */}
                      {group.level && group.level > 0 && (
                        <Box sx={{ width: group.level * 20, display: 'flex', alignItems: 'center' }}>
                          {'└─'.repeat(group.level)}
                        </Box>
                      )}
                      <Typography variant="body2" fontWeight="medium">
                        {group.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {group.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {group.parent_name ? (
                      <Chip
                        label={group.parent_name}
                        size="small"
                        color="info"
                        variant="outlined"
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Root Group
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {group.person_name ? (
                      <Chip
                        label={group.person_name}
                        size="small"
                        color="secondary"
                        variant="outlined"
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No Person
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={group.device_count || 0}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={group.children_count || 0}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getStatusIcon(group.disabled)}
                      <Chip
                        label={group.disabled ? 'Disabled' : 'Enabled'}
                        size="small"
                        color={getStatusColor(group.disabled)}
                        variant="outlined"
                      />
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(group.created_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box display="flex" gap={1} justifyContent="center">
                      <Tooltip title="Edit Group">
                        <IconButton
                          size="small"
                          onClick={() => handleEditGroup(group)}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={group.disabled ? 'Enable Group' : 'Disable Group'}>
                        <IconButton
                          size="small"
                          onClick={() => handleToggleStatus(group)}
                        >
                          {group.disabled ? <EnableIcon /> : <DisableIcon />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete Group">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteGroup(group)}
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
        </TableContainer>
      </Paper>

      {filteredGroups.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            {hasActiveFilters 
              ? 'No groups match the current filters'
              : 'No groups found'
            }
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {hasActiveFilters 
              ? 'Try adjusting your search criteria or clear the filters.'
              : 'Click "Add Group" to create your first group.'
            }
          </Typography>
          {hasActiveFilters && (
            <Button
              variant="outlined"
              onClick={clearFilters}
              sx={{ mt: 2 }}
            >
              Clear Filters
            </Button>
          )}
        </Box>
      )}

      {/* Group Dialog */}
      <GroupDialog
        open={groupDialogOpen}
        onClose={() => setGroupDialogOpen(false)}
        onSave={handleSaveGroup}
        group={selectedGroup}
        mode={dialogMode}
      />

      {/* Confirm Dialog */}
      <ConfirmDialog
        open={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        onConfirm={handleConfirmAction}
        title={getConfirmTitle()}
        message={getConfirmMessage()}
        action={confirmAction}
      />
    </Box>
  );
};

export default Groups;
