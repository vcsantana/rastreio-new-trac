import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { useMediaQuery, useTheme } from '@mui/material';
import { makeStyles } from 'tss-react/mui';
import BottomMenu from './common/components/BottomMenu';
import SocketController from './SocketController';
import CachingController from './CachingController';
import { useCatch, useEffectAsync } from './reactHelper';
import { sessionActions } from './store';
import UpdateController from './UpdateController';
import TermsDialog from './common/components/TermsDialog';
import Loader from './common/components/Loader';
import fetchOrThrow from './common/util/fetchOrThrow';
import { authService } from './api/auth.js';

const useStyles = makeStyles()(() => ({
  page: {
    flexGrow: 1,
    overflow: 'auto',
  },
  menu: {
    zIndex: 4,
    '@media print': {
      display: 'none',
    },
  },
}));

const App = () => {
  const { classes } = useStyles();
  const theme = useTheme();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { pathname, search } = useLocation();

  const desktop = useMediaQuery(theme.breakpoints.up('md'));

  const newServer = useSelector((state) => state.session.server.newServer);
  const termsUrl = useSelector((state) => state.session.server.attributes.termsUrl);
  const user = useSelector((state) => state.session.user);

  const acceptTerms = useCatch(async () => {
    const response = await fetchOrThrow(`/api/users/${user.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...user, attributes: { ...user.attributes, termsAccepted: true } }),
    });
    dispatch(sessionActions.updateUser(await response.json()));
  });

  useEffectAsync(async () => {
    if (!user) {
      try {
        // Check if user is authenticated with our Python API
        if (authService.isAuthenticated()) {
          const userData = await authService.getCurrentUser();
          dispatch(sessionActions.updateUser(userData));
        } else {
          window.sessionStorage.setItem('postLogin', pathname + search);
          navigate(newServer ? '/register' : '/login', { replace: true });
        }
      } catch (error) {
        console.error('Session check failed:', error);
        // Clear invalid tokens
        authService.logout();
        window.sessionStorage.setItem('postLogin', pathname + search);
        navigate(newServer ? '/register' : '/login', { replace: true });
      }
    }
    return null;
  }, []);

  if (user == null) {
    return (<Loader />);
  }
  if (termsUrl && !user.attributes.termsAccepted) {
    return (
      <TermsDialog
        open
        onCancel={() => navigate('/login')}
        onAccept={() => acceptTerms()}
      />
    );
  }
  return (
    <>
      <SocketController />
      <CachingController />
      <UpdateController />
      <div className={classes.page}>
        <Outlet />
      </div>
      {!desktop && (
        <div className={classes.menu}>
          <BottomMenu />
        </div>
      )}
    </>
  );
};

export default App;
