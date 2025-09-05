import React, { useState } from 'react';
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
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Block as DisableIcon,
  CheckCircle as EnableIcon,
} from '@mui/icons-material';
import { useGroups, Group } from '../hooks/useGroups';
import GroupDialog from '../components/common/GroupDialog';
import ConfirmDialog from '../components/common/ConfirmDialog';

const Groups: React.FC = () => {
  const {
    groups,
    loading,
    error,
    createGroup,
    updateGroup,
    deleteGroup,
    toggleGroupStatus,
  } = useGroups();

  // Dialog states
  const [groupDialogOpen, setGroupDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [confirmAction, setConfirmAction] = useState<'delete' | 'disable' | 'enable'>('delete');

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
          Groups
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddGroup}
        >
          Add Group
        </Button>
      </Box>

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
                <TableCell>Devices</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {groups.map((group) => (
                <TableRow key={group.id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {group.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {group.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={group.device_count}
                      size="small"
                      color="primary"
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
