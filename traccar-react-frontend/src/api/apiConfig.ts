// API Configuration for Python FastAPI
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export const API_ENDPOINTS = {
  // Authentication
  LOGIN: `${API_BASE_URL}/api/auth/login`,
  REGISTER: `${API_BASE_URL}/api/auth/register`,
  LOGOUT: `${API_BASE_URL}/api/auth/logout`,
  ME: `${API_BASE_URL}/api/auth/me`,
  REFRESH: `${API_BASE_URL}/api/auth/refresh`,
  
  // Devices
  DEVICES: `${API_BASE_URL}/api/devices`,
  DEVICE_POSITIONS: (deviceId: number) => `${API_BASE_URL}/api/devices/${deviceId}/positions`,
  
  // Positions
  POSITIONS: `${API_BASE_URL}/api/positions`,
  
  // WebSocket
  WEBSOCKET: WS_URL,
  
  // Legacy endpoints for compatibility
  SESSION: `${API_BASE_URL}/api/session`,
};

export const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const getApiUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint}`;
};
