import React, { useState, useMemo } from 'react';
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  InputAdornment,
  Collapse,
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
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
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

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [locationFilter, setLocationFilter] = useState<string>('all');
  const [filtersExpanded, setFiltersExpanded] = useState(false);

  // Get unique values for filter options
  const uniqueLocations = useMemo(() => {
    const locations = persons
      .map(p => p.city && p.state ? `${p.city}, ${p.state}` : null)
      .filter(Boolean);
    return Array.from(new Set(locations));
  }, [persons]);

  // Filter persons based on current filters
  const filteredPersons = useMemo(() => {
    return persons.filter(person => {
      // Search term filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = 
          person.name.toLowerCase().includes(searchLower) ||
          person.email.toLowerCase().includes(searchLower) ||
          (person.phone && person.phone.includes(searchTerm)) ||
          (person.cpf && person.cpf.includes(searchTerm)) ||
          (person.cnpj && person.cnpj.includes(searchTerm)) ||
          (person.trade_name && person.trade_name.toLowerCase().includes(searchLower));
        if (!matchesSearch) return false;
      }

      // Type filter
      if (typeFilter !== 'all' && person.person_type !== typeFilter) {
        return false;
      }

      // Status filter
      if (statusFilter !== 'all') {
        if (statusFilter === 'active' && !person.active) return false;
        if (statusFilter === 'inactive' && person.active) return false;
      }

      // Location filter
      if (locationFilter !== 'all') {
        const personLocation = person.city && person.state ? `${person.city}, ${person.state}` : null;
        if (personLocation !== locationFilter) return false;
      }

      return true;
    });
  }, [persons, searchTerm, typeFilter, statusFilter, locationFilter]);

  // Clear all filters
  const clearFilters = () => {
    setSearchTerm('');
    setTypeFilter('all');
    setStatusFilter('all');
    setLocationFilter('all');
  };

  // Check if any filters are active
  const hasActiveFilters = searchTerm || typeFilter !== 'all' || statusFilter !== 'all' || locationFilter !== 'all';

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
          Persons ({filteredPersons.length})
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
              typeFilter !== 'all' && 'Type',
              statusFilter !== 'all' && 'Status',
              locationFilter !== 'all' && 'Location'
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
            onClick={handleAddPerson}
            disabled={loading}
          >
            Add Person
          </Button>
        </Box>
      </Box>

      {/* Filters Section */}
      <Collapse in={filtersExpanded}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filter Persons
          </Typography>
          <Grid container spacing={2}>
            {/* Search */}
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search persons"
                placeholder="Search by name, email, phone, document..."
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

            {/* Type Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Type</InputLabel>
                <Select
                  value={typeFilter}
                  label="Type"
                  onChange={(e) => setTypeFilter(e.target.value)}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="physical">Physical</MenuItem>
                  <MenuItem value="legal">Legal</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Status Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Location Filter */}
            <Grid item xs={12} md={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Location</InputLabel>
                <Select
                  value={locationFilter}
                  label="Location"
                  onChange={(e) => setLocationFilter(e.target.value)}
                >
                  <MenuItem value="all">All Locations</MenuItem>
                  {uniqueLocations.map(location => (
                    <MenuItem key={location} value={location}>
                      {location}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
      </Collapse>

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
            {filteredPersons.map((person) => (
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

      {filteredPersons.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            {hasActiveFilters 
              ? 'No persons match the current filters'
              : 'No persons found'
            }
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {hasActiveFilters 
              ? 'Try adjusting your search criteria or clear the filters.'
              : 'Click "Add Person" to create your first person record.'
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
