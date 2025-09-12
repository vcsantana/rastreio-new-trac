import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Paper,
  BottomNavigation,
  BottomNavigationAction,
  Menu,
  MenuItem,
  Typography,
  Badge,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Map as MapIcon,
  Description as ReportsIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';
import { useWebSocket } from '../../hooks/useWebSocket';

const BottomMenu: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user, logout } = useAuth();
  const { connected } = useWebSocket();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const currentSelection = () => {
    if (location.pathname === '/dashboard' || location.pathname === '/') {
      return 'map';
    }
    if (location.pathname.startsWith('/reports')) {
      return 'reports';
    }
    if (location.pathname.startsWith('/settings')) {
      return 'settings';
    }
    if (location.pathname === `/settings/user/${user?.id}`) {
      return 'account';
    }
    return null;
  };

  const handleAccount = () => {
    setAnchorEl(null);
    navigate(`/settings/user/${user?.id}`);
  };

  const handleLogout = async () => {
    setAnchorEl(null);
    await logout();
  };

  const handleSelection = (event: React.SyntheticEvent, value: string) => {
    switch (value) {
      case 'map':
        navigate('/dashboard');
        break;
      case 'reports':
        navigate('/reports');
        break;
      case 'settings':
        navigate('/settings');
        break;
      case 'account':
        setAnchorEl(event.currentTarget as HTMLElement);
        break;
      case 'logout':
        handleLogout();
        break;
      default:
        break;
    }
  };

  // Show different layout for desktop and mobile
  if (!isMobile) {
    // Desktop version - horizontal menu
    return (
      <Paper
        square
        elevation={3}
        sx={{
          position: 'fixed',
          bottom: 16,
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1000,
          borderRadius: 2,
          overflow: 'hidden'
        }}
      >
        <BottomNavigation
          value={currentSelection()}
          onChange={handleSelection}
          showLabels
          sx={{
            backgroundColor: theme.palette.background.paper,
            '& .MuiBottomNavigationAction-root': {
              minWidth: 80,
              padding: '6px 12px',
            }
          }}
        >
          <BottomNavigationAction
            label="Map"
            icon={
              <Badge color="error" variant="dot" overlap="circular" invisible={connected}>
                <MapIcon />
              </Badge>
            }
            value="map"
          />
          <BottomNavigationAction
            label="Reports"
            icon={<ReportsIcon />}
            value="reports"
          />
          <BottomNavigationAction
            label="Settings"
            icon={<SettingsIcon />}
            value="settings"
          />
          <BottomNavigationAction
            label="Account"
            icon={<PersonIcon />}
            value="account"
          />
        </BottomNavigation>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
        >
          <MenuItem onClick={handleAccount}>
            <Typography color="textPrimary">Account Settings</Typography>
          </MenuItem>
          <MenuItem onClick={handleLogout}>
            <Typography color="error">Logout</Typography>
          </MenuItem>
        </Menu>
      </Paper>
    );
  }

  return (
    <Paper square elevation={3} sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1000 }}>
      <BottomNavigation value={currentSelection()} onChange={handleSelection} showLabels>
        <BottomNavigationAction
          label="Map"
          icon={
            <Badge color="error" variant="dot" overlap="circular" invisible={connected}>
              <MapIcon />
            </Badge>
          }
          value="map"
        />
        <BottomNavigationAction
          label="Reports"
          icon={<ReportsIcon />}
          value="reports"
        />
        <BottomNavigationAction
          label="Settings"
          icon={<SettingsIcon />}
          value="settings"
        />
        <BottomNavigationAction
          label="Account"
          icon={<PersonIcon />}
          value="account"
        />
      </BottomNavigation>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={handleAccount}>
          <Typography color="textPrimary">Account Settings</Typography>
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <Typography color="error">Logout</Typography>
        </MenuItem>
      </Menu>
    </Paper>
  );
};

export default BottomMenu;
