import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, useMediaQuery } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';

import { store } from './store';
import { theme } from './styles/theme';
import { AuthProvider } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { Layout } from './components/common/Layout';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { ErrorBoundary } from './components/common/ErrorBoundary';

// Lazy load pages for better performance
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Devices = React.lazy(() => import('./pages/Devices'));
const Groups = React.lazy(() => import('./pages/Groups'));
const Reports = React.lazy(() => import('./pages/Reports'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Login = React.lazy(() => import('./pages/Login'));

function App() {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <ThemeProvider theme={theme(prefersDarkMode)}>
          <CssBaseline />
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <AuthProvider>
              <WebSocketProvider>
                <Router>
                  <React.Suspense fallback={<LoadingSpinner />}>
                    <Routes>
                      {/* Public routes */}
                      <Route path="/login" element={<Login />} />
                      
                      {/* Protected routes */}
                      <Route
                        path="/"
                        element={
                          <ProtectedRoute>
                            <Layout />
                          </ProtectedRoute>
                        }
                      >
                        <Route index element={<Navigate to="/dashboard" replace />} />
                        <Route path="dashboard" element={<Dashboard />} />
                        <Route path="devices" element={<Devices />} />
                        <Route path="groups" element={<Groups />} />
                        <Route path="reports" element={<Reports />} />
                        <Route path="settings" element={<Settings />} />
                      </Route>
                      
                      {/* Catch all route */}
                      <Route path="*" element={<Navigate to="/dashboard" replace />} />
                    </Routes>
                  </React.Suspense>
                </Router>
              </WebSocketProvider>
            </AuthProvider>
          </LocalizationProvider>
        </ThemeProvider>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;
