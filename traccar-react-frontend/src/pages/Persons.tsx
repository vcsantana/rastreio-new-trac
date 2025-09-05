import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import { usePersons, Person } from '../hooks/usePersons';
import PersonDialog from '../components/common/PersonDialog';
import ConfirmDialog from '../components/common/ConfirmDialog';

const Persons: React.FC = () => {
  const {
    persons,
    loading,
    error,
    createPerson,
    updatePerson,
    deletePerson,
    togglePersonStatus,
  } = usePersons();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [actionType, setActionType] = useState<'edit' | 'delete' | 'toggle'>('edit');

  const handleAddPerson = () => {
    setSelectedPerson(null);
    setDialogOpen(true);
  };

  const handleEditPerson = (person: Person) => {
    setSelectedPerson(person);
    setDialogOpen(true);
  };

  const handleDeletePerson = (person: Person) => {
    setSelectedPerson(person);
    setActionType('delete');
    setConfirmDialogOpen(true);
  };

  const handleToggleStatus = (person: Person) => {
    setSelectedPerson(person);
    setActionType('toggle');
    setConfirmDialogOpen(true);
  };

  const handleSavePerson = async (personData: any): Promise<boolean> => {
    if (selectedPerson) {
      const result = await updatePerson(selectedPerson.id, personData);
      return result !== null;
    } else {
      const result = await createPerson(personData);
      return result !== null;
    }
  };

  const handleConfirmAction = async () => {
    if (!selectedPerson) return;

    let success = false;
    switch (actionType) {
      case 'delete':
        success = await deletePerson(selectedPerson.id);
        break;
      case 'toggle':
        success = await togglePersonStatus(selectedPerson.id);
        break;
    }

    if (success) {
      setConfirmDialogOpen(false);
      setSelectedPerson(null);
    }
  };

  const getPersonTypeIcon = (personType: string) => {
    return personType === 'legal' ? <BusinessIcon /> : <PersonIcon />;
  };

  const getPersonTypeColor = (personType: string) => {
    return personType === 'legal' ? 'primary' : 'secondary';
  };

  const getStatusColor = (active: boolean) => {
    return active ? 'success' : 'error';
  };

  const formatDocument = (person: Person) => {
    if (person.person_type === 'physical' && person.cpf) {
      return person.cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    if (person.person_type === 'legal' && person.cnpj) {
      return person.cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
    return '-';
  };

  const getConfirmDialogTitle = () => {
    if (!selectedPerson) return '';
    switch (actionType) {
      case 'delete':
        return 'Delete Person';
      case 'toggle':
        return selectedPerson.active ? 'Deactivate Person' : 'Activate Person';
      default:
        return '';
    }
  };

  const getConfirmDialogMessage = () => {
    if (!selectedPerson) return '';
    switch (actionType) {
      case 'delete':
        return `Are you sure you want to delete "${selectedPerson.name}"? This action cannot be undone.`;
      case 'toggle':
        return `Are you sure you want to ${selectedPerson.active ? 'deactivate' : 'activate'} "${selectedPerson.name}"?`;
      default:
        return '';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Persons
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddPerson}
          disabled={loading}
        >
          Add Person
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Document</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Groups</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {persons.map((person) => (
              <TableRow key={person.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getPersonTypeIcon(person.person_type)}
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {person.name}
                      </Typography>
                      {person.person_type === 'legal' && person.trade_name && (
                        <Typography variant="caption" color="text.secondary">
                          ({person.trade_name})
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={person.person_type === 'legal' ? 'Legal' : 'Physical'}
                    color={getPersonTypeColor(person.person_type) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDocument(person)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <EmailIcon fontSize="small" color="action" />
                    <Typography variant="body2">
                      {person.email}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  {person.phone ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <PhoneIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {person.phone}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  {person.city && person.state ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <LocationIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {person.city}, {person.state}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Chip
                    label={person.active ? 'Active' : 'Inactive'}
                    color={getStatusColor(person.active) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={person.group_count || 0}
                    variant="outlined"
                    size="small"
                    color="info"
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Edit Person">
                    <IconButton
                      size="small"
                      onClick={() => handleEditPerson(person)}
                      disabled={loading}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title={person.active ? 'Deactivate' : 'Activate'}>
                    <IconButton
                      size="small"
                      onClick={() => handleToggleStatus(person)}
                      disabled={loading}
                    >
                      {person.active ? '⏸️' : '▶️'}
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Delete Person">
                    <IconButton
                      size="small"
                      onClick={() => handleDeletePerson(person)}
                      disabled={loading}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {persons.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            No persons found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Click "Add Person" to create your first person record.
          </Typography>
        </Box>
      )}

      <PersonDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSavePerson}
        person={selectedPerson}
        title={selectedPerson ? 'Edit Person' : 'Add Person'}
      />

      <ConfirmDialog
        open={confirmDialogOpen}
        onClose={() => setConfirmDialogOpen(false)}
        onConfirm={handleConfirmAction}
        title={getConfirmDialogTitle()}
        message={getConfirmDialogMessage()}
        confirmText={actionType === 'delete' ? 'Delete' : actionType === 'toggle' ? 'Confirm' : 'OK'}
        severity={actionType === 'delete' ? 'error' : 'warning'}
      />
    </Box>
  );
};

export default Persons;
