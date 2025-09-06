import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Typography,
  Alert,
  FormControlLabel,
  Switch,
  RadioGroup,
  Radio,
  FormLabel,
} from '@mui/material';
import { Person, CreatePersonData, UpdatePersonData } from '../../hooks/usePersons';

interface PersonDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: CreatePersonData | UpdatePersonData) => Promise<boolean>;
  person?: Person | null;
  title: string;
}

const PersonDialog: React.FC<PersonDialogProps> = ({
  open,
  onClose,
  onSave,
  person,
  title,
}) => {
  const [formData, setFormData] = useState<CreatePersonData>({
    name: '',
    person_type: 'physical',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'Brazil',
    active: true,
    cpf: '',
    birth_date: '',
    cnpj: '',
    company_name: '',
    trade_name: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when dialog opens/closes or person changes
  useEffect(() => {
    if (open) {
      if (person) {
        setFormData({
          name: person.name || '',
          person_type: person.person_type || 'physical',
          email: person.email || '',
          phone: person.phone || '',
          address: person.address || '',
          city: person.city || '',
          state: person.state || '',
          zip_code: person.zip_code || '',
          country: person.country || 'Brazil',
          active: person.active !== undefined ? person.active : true,
          cpf: person.cpf || '',
          birth_date: person.birth_date ? person.birth_date.split('T')[0] : '',
          cnpj: person.cnpj || '',
          company_name: person.company_name || '',
          trade_name: person.trade_name || '',
        });
      } else {
        setFormData({
          name: '',
          person_type: 'physical',
          email: '',
          phone: '',
          address: '',
          city: '',
          state: '',
          zip_code: '',
          country: 'Brazil',
          active: true,
          cpf: '',
          birth_date: '',
          cnpj: '',
          company_name: '',
          trade_name: '',
        });
      }
      setError(null);
    }
  }, [open, person]);

  const handleInputChange = (field: keyof CreatePersonData) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | any
  ) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePersonTypeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const personType = event.target.value as 'physical' | 'legal';
    setFormData(prev => ({
      ...prev,
      person_type: personType,
      // Clear fields when switching type
      cpf: personType === 'physical' ? prev.cpf : '',
      birth_date: personType === 'physical' ? prev.birth_date : '',
      cnpj: personType === 'legal' ? prev.cnpj : '',
      company_name: personType === 'legal' ? prev.company_name : '',
      trade_name: personType === 'legal' ? prev.trade_name : '',
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);

    try {
      // Validate required fields
      if (!formData.name.trim()) {
        setError('Name is required');
        return;
      }
      
      if (!formData.email.trim()) {
        setError('Email is required');
        return;
      }
      
      // Validate email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        setError('Please enter a valid email address');
        return;
      }

      // Prepare data for submission
      const submitData: any = {
        name: formData.name.trim(),
        person_type: formData.person_type,
        email: formData.email.trim(),
        active: formData.active,
        country: formData.country || 'Brazil'
      };
      
      // Add optional fields only if they have values
      if (formData.phone?.trim()) submitData.phone = formData.phone.trim();
      if (formData.address?.trim()) submitData.address = formData.address.trim();
      if (formData.city?.trim()) submitData.city = formData.city.trim();
      if (formData.state?.trim()) submitData.state = formData.state.trim();
      if (formData.zip_code?.trim()) submitData.zip_code = formData.zip_code.trim();
      
      // Add person type specific fields
      if (formData.person_type === 'physical') {
        if (formData.cpf?.trim()) submitData.cpf = formData.cpf.trim();
        if (formData.birth_date?.trim()) submitData.birth_date = formData.birth_date;
      } else if (formData.person_type === 'legal') {
        if (formData.cnpj?.trim()) submitData.cnpj = formData.cnpj.trim();
        if (formData.company_name?.trim()) submitData.company_name = formData.company_name.trim();
        if (formData.trade_name?.trim()) submitData.trade_name = formData.trade_name.trim();
      }

      const success = await onSave(submitData);
      
      if (success) {
        handleClose();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save person');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ pt: 1 }}>
          <Grid container spacing={2}>
            {/* Person Type */}
            <Grid item xs={12}>
              <FormControl component="fieldset">
                <FormLabel component="legend">Person Type</FormLabel>
                <RadioGroup
                  row
                  value={formData.person_type}
                  onChange={handlePersonTypeChange}
                  disabled={loading}
                >
                  <FormControlLabel
                    value="physical"
                    control={<Radio />}
                    label="Physical Person (Pessoa Física)"
                  />
                  <FormControlLabel
                    value="legal"
                    control={<Radio />}
                    label="Legal Person (Pessoa Jurídica)"
                  />
                </RadioGroup>
              </FormControl>
            </Grid>

            {/* Basic Information */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={handleInputChange('name')}
                required
                disabled={loading}
                helperText="Full name or company name"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={handleInputChange('email')}
                required
                disabled={loading}
              />
            </Grid>

            {/* Physical Person Fields */}
            {formData.person_type === 'physical' && (
              <>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="CPF"
                    value={formData.cpf}
                    onChange={handleInputChange('cpf')}
                    disabled={loading}
                    helperText="Format: 000.000.000-00"
                    placeholder="000.000.000-00"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Birth Date"
                    type="date"
                    value={formData.birth_date}
                    onChange={handleInputChange('birth_date')}
                    disabled={loading}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </>
            )}

            {/* Legal Person Fields */}
            {formData.person_type === 'legal' && (
              <>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="CNPJ"
                    value={formData.cnpj}
                    onChange={handleInputChange('cnpj')}
                    disabled={loading}
                    helperText="Format: 00.000.000/0000-00"
                    placeholder="00.000.000/0000-00"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Company Name"
                    value={formData.company_name}
                    onChange={handleInputChange('company_name')}
                    disabled={loading}
                    helperText="Official company name"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Trade Name"
                    value={formData.trade_name}
                    onChange={handleInputChange('trade_name')}
                    disabled={loading}
                    helperText="Commercial name (optional)"
                  />
                </Grid>
              </>
            )}

            {/* Contact Information */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={handleInputChange('phone')}
                disabled={loading}
                helperText="Phone number"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Country"
                value={formData.country}
                onChange={handleInputChange('country')}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                value={formData.address}
                onChange={handleInputChange('address')}
                disabled={loading}
                multiline
                rows={2}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="City"
                value={formData.city}
                onChange={handleInputChange('city')}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="State"
                value={formData.state}
                onChange={handleInputChange('state')}
                disabled={loading}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="ZIP Code"
                value={formData.zip_code}
                onChange={handleInputChange('zip_code')}
                disabled={loading}
                helperText="Postal code"
              />
            </Grid>

            {/* Status */}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.active}
                    onChange={(e) => setFormData(prev => ({ ...prev, active: e.target.checked }))}
                    disabled={loading}
                  />
                }
                label="Active"
              />
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading || !formData.name || !formData.email}
        >
          {loading ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PersonDialog;

