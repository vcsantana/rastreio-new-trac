import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  FormControl,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Group } from '../../hooks/useGroups';

interface GroupDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (groupData: any) => void;
  group?: Group | null;
  mode: 'create' | 'edit';
}

const GroupDialog: React.FC<GroupDialogProps> = ({
  open,
  onClose,
  onSave,
  group,
  mode,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    disabled: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      if (mode === 'edit' && group) {
        setFormData({
          name: group.name,
          description: group.description || '',
          disabled: group.disabled,
        });
      } else {
        setFormData({
          name: '',
          description: '',
          disabled: false,
        });
      }
      setError(null);
    }
  }, [open, mode, group]);

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      setError('Group name is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onSave(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save group');
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
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {mode === 'create' ? 'Add New Group' : 'Edit Group'}
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              label="Group Name"
              value={formData.name}
              onChange={handleChange('name')}
              required
              disabled={loading}
              error={!formData.name.trim() && error !== null}
              helperText={!formData.name.trim() && error !== null ? 'Group name is required' : ''}
            />
          </Grid>
          
          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={handleChange('description')}
              multiline
              rows={3}
              disabled={loading}
              placeholder="Optional description for this group"
            />
          </Grid>
          
          <Grid size={{ xs: 12 }}>
            <FormControl>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.disabled}
                    onChange={handleChange('disabled')}
                    disabled={loading}
                  />
                }
                label="Disabled"
              />
            </FormControl>
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !formData.name.trim()}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Saving...' : mode === 'create' ? 'Create Group' : 'Update Group'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default GroupDialog;
