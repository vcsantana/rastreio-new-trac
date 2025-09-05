import { useState } from 'react';
import {
  Button, TextField, Typography, Snackbar, IconButton,
} from '@mui/material';
import { makeStyles } from 'tss-react/mui';
import { useNavigate } from 'react-router-dom';
import LoginLayout from './LoginLayout';
import { useTranslation } from '../common/components/LocalizationProvider';
import useQuery from '../common/util/useQuery';
import { snackBarDurationShortMs } from '../common/util/duration';
import { useCatch } from '../reactHelper';
import BackIcon from '../common/components/BackIcon';
import fetchOrThrow from '../common/util/fetchOrThrow';

const useStyles = makeStyles()((theme) => ({
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing(2),
  },
  header: {
    display: 'flex',
    alignItems: 'center',
  },
  title: {
    fontSize: theme.spacing(3),
    fontWeight: 500,
    marginLeft: theme.spacing(1),
    textTransform: 'uppercase',
  },
}));

const ResetPasswordPage = () => {
  const { classes } = useStyles();
  const navigate = useNavigate();
  const t = useTranslation();
  const query = useQuery();

  const token = query.get('passwordReset');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const handleSubmit = useCatch(async (event) => {
    event.preventDefault();
    if (!token) {
      await fetchOrThrow('/api/password/reset', {
        method: 'POST',
        body: new URLSearchParams(`email=${encodeURIComponent(email)}`),
      });
    } else {
      await fetchOrThrow('/api/password/update', {
        method: 'POST',
        body: new URLSearchParams(`token=${encodeURIComponent(token)}&password=${encodeURIComponent(password)}`),
      });
    }
    setSnackbarOpen(true);
  });

  return (
    <LoginLayout>
      <div className={classes.container}>
        <div className={classes.header}>
          <IconButton color="primary" onClick={() => navigate('/login')}>
            <BackIcon />
          </IconButton>
          <Typography className={classes.title} color="primary">
            {t('loginReset')}
          </Typography>
        </div>
        {!token ? (
          <TextField
            required
            type="email"
            label={t('userEmail')}
            name="email"
            value={email}
            autoComplete="email"
            onChange={(event) => setEmail(event.target.value)}
          />
        ) : (
          <TextField
            required
            label={t('userPassword')}
            name="password"
            value={password}
            type="password"
            autoComplete="current-password"
            onChange={(event) => setPassword(event.target.value)}
          />
        )}
        <Button
          variant="contained"
          color="secondary"
          type="submit"
          onClick={handleSubmit}
          disabled={!/(.+)@(.+)\.(.{2,})/.test(email) && !password}
          fullWidth
        >
          {t('loginReset')}
        </Button>
      </div>
      <Snackbar
        open={snackbarOpen}
        onClose={() => navigate('/login')}
        autoHideDuration={snackBarDurationShortMs}
        message={!token ? t('loginResetSuccess') : t('loginUpdateSuccess')}
      />
    </LoginLayout>
  );
};

export default ResetPasswordPage;
