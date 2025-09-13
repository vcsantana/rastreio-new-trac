import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, useMediaQuery } from '@mui/material';
// import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
// import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';

import { store } from './store';
import { theme } from './styles/theme';
import { AuthProvider } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { AdminRoute } from './components/common/AdminRoute';
import { Layout } from './components/common/Layout';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { ErrorBoundary } from './components/common/ErrorBoundary';

// Import Dashboard directly to avoid lazy loading issues
import Dashboard from './pages/Dashboard';
const Devices = React.lazy(() => import('./pages/Devices'));
const Groups = React.lazy(() => import('./pages/Groups'));
const Persons = React.lazy(() => import('./pages/Persons'));
const Commands = React.lazy(() => import('./pages/Commands'));
const Geofences = React.lazy(() => import('./pages/Geofences'));
const Events = React.lazy(() => import('./pages/Events'));
const Reports = React.lazy(() => import('./pages/ReportsPage'));
const Replay = React.lazy(() => import('./pages/Replay'));
const Settings = React.lazy(() => import('./pages/Settings'));
const ServerSettings = React.lazy(() => import('./pages/ServerSettings'));
const LogsViewer = React.lazy(() => import('./components/LogsViewer'));
const UnknownDevices = React.lazy(() => import('./pages/UnknownDevices'));
const Users = React.lazy(() => import('./pages/Users'));
const Login = React.lazy(() => import('./pages/Login'));

function App() {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemeProvider theme={theme(prefersDarkMode)}>
          <CssBaseline />
          <AuthProvider>
            <WebSocketProvider>
              <Router>
                <React.Suspense fallback={<LoadingSpinner />}>
                  <Routes>
                      {/* Public routes */}
                      <Route path="/login" element={<Login />} />
                      
                      {/* Dashboard route - standalone without Layout */}
                      <Route 
                        path="/dashboard" 
                        element={
                          <ProtectedRoute>
                            <Dashboard />
                          </ProtectedRoute>
                        } 
                      />
                      <Route index element={<Navigate to="/dashboard" replace />} />
                      
                      {/* Protected routes with Layout */}
                      <Route
                        path="/"
                        element={
                          <ProtectedRoute>
                            <Layout />
                          </ProtectedRoute>
                        }
                      >
                        <Route path="devices" element={<Devices />} />
                        <Route path="groups" element={<Groups />} />
                        <Route path="persons" element={<Persons />} />
                        <Route path="commands" element={<Commands />} />
                        <Route path="geofences" element={<Geofences />} />
                        <Route path="events" element={<Events />} />
                        <Route path="replay" element={<Replay />} />
                        
                        {/* Admin-only routes */}
                        <Route path="reports" element={
                          <AdminRoute>
                            <Reports />
                          </AdminRoute>
                        } />
                        <Route path="logs" element={
                          <AdminRoute>
                            <LogsViewer />
                          </AdminRoute>
                        } />
                        <Route path="unknown-devices" element={
                          <AdminRoute>
                            <UnknownDevices />
                          </AdminRoute>
                        } />
                        <Route path="users" element={
                          <AdminRoute>
                            <Users />
                          </AdminRoute>
                        } />
                        <Route path="settings" element={
                          <AdminRoute>
                            <Settings />
                          </AdminRoute>
                        } />
                        <Route path="settings/server" element={
                          <AdminRoute>
                            <ServerSettings />
                          </AdminRoute>
                        } />
                      </Route>
                      
                      {/* Catch all route */}
                      <Route path="*" element={<Navigate to="/dashboard" replace />} />
                    </Routes>
                  </React.Suspense>
                </Router>
              </WebSocketProvider>
            </AuthProvider>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
