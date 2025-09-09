import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Badge,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Group as GroupsIcon,
  Person as PersonsIcon,
  Send as CommandsIcon,
  Map as GeofencesIcon,
  Assessment as ReportsIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
  Logout as LogoutIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  ListAlt as LogsIcon,
  NetworkCheck as UnknownDevicesIcon,
  People as UsersIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';

import { useAuth } from '../../hooks/useAuth';
import { RootState } from '../../store';
import { toggleTheme } from '../../store/slices/uiSlice';
import { WebSocketStatus } from './WebSocketStatus';
import BottomMenu from './BottomMenu';

const DRAWER_WIDTH = 240;

interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon: React.ReactElement;
}

// Main navigation items (like original Traccar)
const mainNavigationItems: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Map',
    path: '/dashboard',
    icon: <DashboardIcon />,
  },
  {
    id: 'reports',
    label: 'Reports',
    path: '/reports',
    icon: <ReportsIcon />,
  },
];

// Settings navigation items (admin only)
const settingsNavigationItems: NavigationItem[] = [
  {
    id: 'groups',
    label: 'Groups',
    path: '/groups',
    icon: <GroupsIcon />,
  },
  {
    id: 'persons',
    label: 'Persons',
    path: '/persons',
    icon: <PersonsIcon />,
  },
  {
    id: 'commands',
    label: 'Commands',
    path: '/commands',
    icon: <CommandsIcon />,
  },
  {
    id: 'geofences',
    label: 'Geofences',
    path: '/geofences',
    icon: <GeofencesIcon />,
  },
  {
    id: 'logs',
    label: 'Logs',
    path: '/logs',
    icon: <LogsIcon />,
  },
  {
    id: 'unknown-devices',
    label: 'Unknown Devices',
    path: '/unknown-devices',
    icon: <UnknownDevicesIcon />,
  },
  {
    id: 'users',
    label: 'Users',
    path: '/users',
    icon: <UsersIcon />,
  },
  {
    id: 'settings',
    label: 'Settings',
    path: '/settings',
    icon: <SettingsIcon />,
  },
];

// Combine all navigation items
const allNavigationItems: NavigationItem[] = [
  ...mainNavigationItems,
  ...settingsNavigationItems,
];

// Admin-only navigation items
const adminOnlyItems = ['logs', 'unknown-devices', 'users', 'settings'];

export const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const { user, logout } = useAuth();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const darkMode = useSelector((state: RootState) => state.ui.darkMode);
  const notifications = useSelector((state: RootState) => state.ui.notifications);
  const unreadCount = notifications.filter(n => !n.read).length;

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleProfileMenuClose();
    await logout();
  };

  const handleThemeToggle = () => {
    dispatch(toggleTheme());
  };

  // Check if we're on a settings page (should show sidebar)
  const isSettingsPage = location.pathname.startsWith('/settings') || 
                        location.pathname.startsWith('/reports') ||
                        location.pathname.startsWith('/groups') ||
                        location.pathname.startsWith('/persons') ||
                        location.pathname.startsWith('/commands') ||
                        location.pathname.startsWith('/geofences') ||
                        location.pathname.startsWith('/logs') ||
                        location.pathname.startsWith('/unknown-devices') ||
                        location.pathname.startsWith('/users');

  // Filter navigation items based on user permissions
  const navigationItems = allNavigationItems.filter(item => {
    if (adminOnlyItems.includes(item.id)) {
      return user?.is_admin;
    }
    return true;
  });

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* AppBar - Only show on settings pages */}
      {isSettingsPage && (
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
              {location.pathname.split('/')[1]?.charAt(0).toUpperCase() + location.pathname.split('/')[1]?.slice(1) || 'Settings'}
            </Typography>
            
            {/* WebSocket Status */}
            <WebSocketStatus />
            
            {/* Notifications */}
            <IconButton color="inherit">
              <Badge badgeContent={unreadCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            
            {/* Theme Toggle */}
            <IconButton color="inherit" onClick={handleThemeToggle}>
              {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
            
            {/* Profile Menu */}
            <IconButton
              size="large"
              edge="end"
              aria-label="account of current user"
              aria-controls="primary-search-account-menu"
              aria-haspopup="true"
              onClick={handleProfileMenuOpen}
              color="inherit"
            >
              <AccountIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
      )}

      {/* Sidebar - Only show on settings pages */}
      {isSettingsPage && (
        <Drawer
          variant="permanent"
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              top: isSettingsPage ? 64 : 0, // Account for AppBar height
            },
          }}
        >
          <Box sx={{ overflow: 'auto', pt: isSettingsPage ? 1 : 0 }}>
            <List>
              {navigationItems.map((item) => (
                <ListItem key={item.id} disablePadding>
                  <ListItemButton
                    selected={location.pathname === item.path}
                    onClick={() => navigate(item.path)}
                  >
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.label} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: isSettingsPage ? `calc(100% - ${DRAWER_WIDTH}px)` : '100%',
          height: '100vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {isSettingsPage && <Toolbar />} {/* Spacer for fixed AppBar on settings pages */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: { xs: 1, sm: 2, md: 3 },
            pb: { xs: 8, md: 3 }, // Add bottom padding for mobile bottom menu
          }}
        >
          <Outlet />
        </Box>
      </Box>

      {/* Bottom Menu for Mobile */}
      <BottomMenu />

      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleProfileMenuClose}
        onClick={handleProfileMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
            '&:before': {
              content: '""',
              display: 'block',
              position: 'absolute',
              top: 0,
              right: 14,
              width: 10,
              height: 10,
              bgcolor: 'background.paper',
              transform: 'translateY(-50%) rotate(45deg)',
              zIndex: 0,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={() => navigate('/settings/user')}>
          <Avatar /> Profile
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>
    </Box>
  );
};