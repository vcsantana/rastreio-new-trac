import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Button, Box, Drawer, List, ListItem, ListItemText, ListItemButton, IconButton } from '@mui/material';
import { Menu as MenuIcon, Dashboard, Devices, Map, Event, Assessment, People, Settings, Fence, Replay, Terminal, Group } from '@mui/icons-material';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import DevicesPage from './pages/DevicesPage';
import MapPage from './pages/MapPage';
import EventsPage from './pages/EventsPage';
import ReportsPage from './pages/ReportsPage';
import UsersPage from './pages/UsersPage';
import SettingsPage from './pages/SettingsPage';
import GeofencesPage from './pages/GeofencesPage';
import ReplayPage from './pages/ReplayPage';
import CommandsPage from './pages/CommandsPage';
import GroupsPage from './pages/GroupsPage';
import { useSelector, useDispatch } from 'react-redux';
import { setUser, clearUser } from './store/authSlice';

function App() {
  const dispatch = useDispatch();
  const user = useSelector((state) => state.auth.user);
  const [loading, setLoading] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token with API
      fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => {
        if (response.ok) {
          return response.json();
        }
        throw new Error('Invalid token');
      })
      .then(userData => {
        dispatch(setUser(userData));
      })
      .catch(() => {
        localStorage.removeItem('token');
        dispatch(clearUser());
      })
      .finally(() => {
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [dispatch]);

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
          <Typography>Loading...</Typography>
        </Box>
      </Container>
    );
  }

  const menuItems = [
    { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
    { text: 'Map', icon: <Map />, path: '/map' },
    { text: 'Devices', icon: <Devices />, path: '/devices' },
    { text: 'Groups', icon: <Group />, path: '/groups' },
    { text: 'Geofences', icon: <Fence />, path: '/geofences' },
    { text: 'Events', icon: <Event />, path: '/events' },
    { text: 'Replay', icon: <Replay />, path: '/replay' },
    { text: 'Commands', icon: <Terminal />, path: '/commands' },
    { text: 'Reports', icon: <Assessment />, path: '/reports' },
    { text: 'Users', icon: <People />, path: '/users' },
    { text: 'Settings', icon: <Settings />, path: '/settings' },
  ];

  const drawer = (
    <Box sx={{ width: 250 }}>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Traccar
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton component="a" href={item.path}>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <div className="App">
      {user && (
        <>
          <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <Toolbar>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                onClick={() => setDrawerOpen(true)}
                edge="start"
                sx={{ mr: 2 }}
              >
                <MenuIcon />
              </IconButton>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Traccar Python API
              </Typography>
              <Button 
                color="inherit" 
                onClick={() => {
                  localStorage.removeItem('token');
                  dispatch(clearUser());
                }}
              >
                Logout
              </Button>
            </Toolbar>
          </AppBar>
          
          <Drawer
            variant="temporary"
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
            ModalProps={{
              keepMounted: true,
            }}
          >
            {drawer}
          </Drawer>
        </>
      )}
      
      <Box sx={{ mt: user ? 8 : 0 }}>
        <Routes>
          <Route 
            path="/login" 
            element={user ? <Navigate to="/dashboard" /> : <LoginPage />} 
          />
          <Route 
            path="/dashboard" 
            element={user ? <DashboardPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/map" 
            element={user ? <MapPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/devices" 
            element={user ? <DevicesPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/events" 
            element={user ? <EventsPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/reports" 
            element={user ? <ReportsPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/users" 
            element={user ? <UsersPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/geofences" 
            element={user ? <GeofencesPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/replay" 
            element={user ? <ReplayPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/commands" 
            element={user ? <CommandsPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/groups" 
            element={user ? <GroupsPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/settings" 
            element={user ? <SettingsPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/" 
            element={<Navigate to={user ? "/dashboard" : "/login"} />} 
          />
        </Routes>
      </Box>
    </div>
  );
}

export default App;
