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
  Assessment as AssessmentIcon,
  BugReport as LogsIcon,
  Devices as DevicesIcon,
  LocationOn as GeofencesIcon,
  Group as GroupsIcon,
  People as PeopleIcon,
  Security as SecurityIcon,
  DifferenceOutlined,
  Rotate90DegreesCcwOutlined,
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
  const [reportsAnchorEl, setReportsAnchorEl] = useState<null | HTMLElement>(null);
  const [settingsAnchorEl, setSettingsAnchorEl] = useState<null | HTMLElement>(null);

  const currentSelection = () => {
    if (location.pathname === '/dashboard' || location.pathname === '/') {
      return 'map';
    }
    if (location.pathname.startsWith('/reports') || location.pathname.startsWith('/logs')) {
      return 'reports';
    }
    if (location.pathname.startsWith('/settings') || 
        location.pathname.startsWith('/devices') ||
        location.pathname.startsWith('/geofences') ||
        location.pathname.startsWith('/groups') ||
        location.pathname.startsWith('/persons') ||
        location.pathname.startsWith('/users') ||
        location.pathname.startsWith('/commands') ||
        location.pathname.startsWith('/events') ||
        location.pathname.startsWith('/unknown-devices')) {
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

  const handleReportsMenu = (event: React.MouseEvent<HTMLElement>) => {
    setReportsAnchorEl(event.currentTarget);
  };

  const handleSettingsMenu = (event: React.MouseEvent<HTMLElement>) => {
    setSettingsAnchorEl(event.currentTarget);
  };

  const handleReportsClose = () => {
    setReportsAnchorEl(null);
  };

  const handleSettingsClose = () => {
    setSettingsAnchorEl(null);
  };

  const handleSelection = (event: React.SyntheticEvent, value: string) => {
    switch (value) {
      case 'map':
        navigate('/dashboard');
        break;
      case 'reports':
        handleReportsMenu(event as any);
        break;
      case 'settings':
        handleSettingsMenu(event as any);
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

        {/* Reports Menu */}
        <Menu
          anchorEl={reportsAnchorEl}
          open={Boolean(reportsAnchorEl)}
          onClose={handleReportsClose}
        >
          <MenuItem onClick={() => { handleReportsClose(); navigate('/replay'); }}>
          <Rotate90DegreesCcwOutlined sx={{ mr: 1 }} />
            <Typography>Replay</Typography>
          </MenuItem>
         
          <MenuItem onClick={() => { handleReportsClose(); navigate('/logs'); }}>
            <LogsIcon sx={{ mr: 1 }} />
            <Typography>Logs</Typography>
          </MenuItem>
        </Menu>

        {/* Settings Menu */}
        <Menu
          anchorEl={settingsAnchorEl}
          open={Boolean(settingsAnchorEl)}
          onClose={handleSettingsClose}
        >
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/devices'); }}>
            <DevicesIcon sx={{ mr: 1 }} />
            <Typography>Devices</Typography>
          </MenuItem>
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/groups'); }}>
            <GroupsIcon sx={{ mr: 1 }} />
            <Typography>Groups</Typography>
          </MenuItem>
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/persons'); }}>
            <PeopleIcon sx={{ mr: 1 }} />
            <Typography>Persons</Typography>
          </MenuItem>
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/commands'); }}>
            <SettingsIcon sx={{ mr: 1 }} />
            <Typography>Commands</Typography>
          </MenuItem>
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/geofences'); }}>
            <GeofencesIcon sx={{ mr: 1 }} />
            <Typography>Geofences</Typography>
          </MenuItem>
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/events'); }}>
            <SettingsIcon sx={{ mr: 1 }} />
            <Typography>Events</Typography>
          </MenuItem>
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/unknown-devices'); }}>
            <DevicesIcon sx={{ mr: 1 }} />
            <Typography>Unknown Devices</Typography>
          </MenuItem>
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/users'); }}>
            <SecurityIcon sx={{ mr: 1 }} />
            <Typography>Users</Typography>
          </MenuItem>
          <MenuItem onClick={() => { handleSettingsClose(); navigate('/settings'); }}>
            <SettingsIcon sx={{ mr: 1 }} />
            <Typography>Settings</Typography>
          </MenuItem>
        </Menu>

        {/* Account Menu */}
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
      
      {/* Reports Menu */}
      <Menu
        anchorEl={reportsAnchorEl}
        open={Boolean(reportsAnchorEl)}
        onClose={handleReportsClose}
      >
        <MenuItem onClick={() => { handleReportsClose(); navigate('/replay'); }}>
          <Rotate90DegreesCcwOutlined sx={{ mr: 1 }} />
            <Typography>Replay</Typography>
          </MenuItem>
       
        <MenuItem onClick={() => { handleReportsClose(); navigate('/logs'); }}>
          <LogsIcon sx={{ mr: 1 }} />
          <Typography>Logs</Typography>
        </MenuItem>
      </Menu>

      {/* Settings Menu */}
      <Menu
        anchorEl={settingsAnchorEl}
        open={Boolean(settingsAnchorEl)}
        onClose={handleSettingsClose}
      >
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/devices'); }}>
          <DevicesIcon sx={{ mr: 1 }} />
          <Typography>Devices</Typography>
        </MenuItem>
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/groups'); }}>
          <GroupsIcon sx={{ mr: 1 }} />
          <Typography>Groups</Typography>
        </MenuItem>
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/persons'); }}>
          <PeopleIcon sx={{ mr: 1 }} />
          <Typography>Persons</Typography>
        </MenuItem>
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/commands'); }}>
          <SettingsIcon sx={{ mr: 1 }} />
          <Typography>Commands</Typography>
        </MenuItem>
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/geofences'); }}>
          <GeofencesIcon sx={{ mr: 1 }} />
          <Typography>Geofences</Typography>
        </MenuItem>
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/events'); }}>
          <SettingsIcon sx={{ mr: 1 }} />
          <Typography>Events</Typography>
        </MenuItem>
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/unknown-devices'); }}>
          <DevicesIcon sx={{ mr: 1 }} />
          <Typography>Unknown Devices</Typography>
        </MenuItem>
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/users'); }}>
          <SecurityIcon sx={{ mr: 1 }} />
          <Typography>Users</Typography>
        </MenuItem>
        <MenuItem onClick={() => { handleSettingsClose(); navigate('/settings'); }}>
          <SettingsIcon sx={{ mr: 1 }} />
          <Typography>Settings</Typography>
        </MenuItem>
      </Menu>

      {/* Account Menu */}
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
