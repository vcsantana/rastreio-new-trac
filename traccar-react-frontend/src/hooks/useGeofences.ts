/**
 * Custom hook for geofence management
 * Provides CRUD operations and state management for geofences
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  Geofence, 
  GeofenceCreate, 
  GeofenceUpdate, 
  GeofenceListResponse, 
  GeofenceStats,
  GeofenceFilters,
  GeofenceTestRequest,
  GeofenceTestResponse,
  GeofenceEvent,
  GeofenceEventStats,
  GeofenceEventFilters
} from '../types/geofences';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface UseGeofencesReturn {
  // Data
  geofences: Geofence[];
  geofence: Geofence | null;
  stats: GeofenceStats | null;
  events: GeofenceEvent[];
  eventStats: GeofenceEventStats | null;
  
  // Loading states
  loading: boolean;
  loadingGeofence: boolean;
  loadingStats: boolean;
  loadingEvents: boolean;
  
  // Error states
  error: string | null;
  
  // Actions
  fetchGeofences: (filters?: GeofenceFilters) => Promise<void>;
  fetchGeofence: (id: number) => Promise<void>;
  createGeofence: (data: GeofenceCreate) => Promise<Geofence>;
  updateGeofence: (id: number, data: GeofenceUpdate) => Promise<Geofence>;
  deleteGeofence: (id: number) => Promise<void>;
  fetchStats: () => Promise<void>;
  testGeofences: (request: GeofenceTestRequest) => Promise<GeofenceTestResponse[]>;
  fetchEvents: (filters?: GeofenceEventFilters) => Promise<void>;
  fetchEventStats: (deviceId?: number, geofenceId?: number, days?: number) => Promise<void>;
  
  // Utility functions
  clearError: () => void;
  clearGeofence: () => void;
}

export const useGeofences = (): UseGeofencesReturn => {
  const [geofences, setGeofences] = useState<Geofence[]>([]);
  const [geofence, setGeofence] = useState<Geofence | null>(null);
  const [stats, setStats] = useState<GeofenceStats | null>(null);
  const [events, setEvents] = useState<GeofenceEvent[]>([]);
  const [eventStats, setEventStats] = useState<GeofenceEventStats | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [loadingGeofence, setLoadingGeofence] = useState(false);
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper function to get auth headers
  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }, []);

  // Helper function to handle API errors
  const handleError = useCallback((err: any, context: string) => {
    console.error(`Error in ${context}:`, err);
    const errorMessage = err.response?.data?.detail || err.message || `Error in ${context}`;
    setError(errorMessage);
    throw new Error(errorMessage);
  }, []);

  // Fetch geofences with optional filters
  const fetchGeofences = useCallback(async (filters: GeofenceFilters = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      
      if (filters.disabled !== undefined) {
        params.append('disabled', filters.disabled.toString());
      }
      if (filters.type) {
        params.append('type', filters.type);
      }
      if (filters.search) {
        params.append('search', filters.search);
      }
      if (filters.page) {
        params.append('page', filters.page.toString());
      }
      if (filters.size) {
        params.append('size', filters.size.toString());
      }
      
      const response = await fetch(`${API_BASE_URL}/geofences/?${params}`, {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: GeofenceListResponse = await response.json();
      setGeofences(data.geofences);
    } catch (err) {
      handleError(err, 'fetchGeofences');
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, handleError]);

  // Fetch a specific geofence
  const fetchGeofence = useCallback(async (id: number) => {
    setLoadingGeofence(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/geofences/${id}`, {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: Geofence = await response.json();
      setGeofence(data);
    } catch (err) {
      handleError(err, 'fetchGeofence');
    } finally {
      setLoadingGeofence(false);
    }
  }, [getAuthHeaders, handleError]);

  // Create a new geofence
  const createGeofence = useCallback(async (data: GeofenceCreate): Promise<Geofence> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/geofences/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const newGeofence: Geofence = await response.json();
      
      // Update the geofences list
      setGeofences(prev => [newGeofence, ...prev]);
      
      return newGeofence;
    } catch (err) {
      handleError(err, 'createGeofence');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, handleError]);

  // Update an existing geofence
  const updateGeofence = useCallback(async (id: number, data: GeofenceUpdate): Promise<Geofence> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/geofences/${id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const updatedGeofence: Geofence = await response.json();
      
      // Update the geofences list
      setGeofences(prev => 
        prev.map(g => g.id === id ? updatedGeofence : g)
      );
      
      // Update the current geofence if it's the one being updated
      if (geofence?.id === id) {
        setGeofence(updatedGeofence);
      }
      
      return updatedGeofence;
    } catch (err) {
      handleError(err, 'updateGeofence');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, handleError, geofence]);

  // Delete a geofence
  const deleteGeofence = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/geofences/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Remove from the geofences list
      setGeofences(prev => prev.filter(g => g.id !== id));
      
      // Clear current geofence if it's the one being deleted
      if (geofence?.id === id) {
        setGeofence(null);
      }
    } catch (err) {
      handleError(err, 'deleteGeofence');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, handleError, geofence]);

  // Fetch geofence statistics
  const fetchStats = useCallback(async () => {
    setLoadingStats(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/geofences/stats/summary`, {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: GeofenceStats = await response.json();
      setStats(data);
    } catch (err) {
      handleError(err, 'fetchStats');
    } finally {
      setLoadingStats(false);
    }
  }, [getAuthHeaders, handleError]);

  // Test geofences for a point
  const testGeofences = useCallback(async (request: GeofenceTestRequest): Promise<GeofenceTestResponse[]> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/geofences/test`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: GeofenceTestResponse[] = await response.json();
      return data;
    } catch (err) {
      handleError(err, 'testGeofences');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, handleError]);

  // Fetch geofence events
  const fetchEvents = useCallback(async (filters: GeofenceEventFilters = {}) => {
    setLoadingEvents(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      
      if (filters.device_id) {
        params.append('device_id', filters.device_id.toString());
      }
      if (filters.geofence_id) {
        params.append('geofence_id', filters.geofence_id.toString());
      }
      if (filters.event_type) {
        params.append('event_type', filters.event_type);
      }
      if (filters.limit) {
        params.append('limit', filters.limit.toString());
      }
      
      const response = await fetch(`${API_BASE_URL}/geofences/events/?${params}`, {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setEvents(data.events || []);
    } catch (err) {
      handleError(err, 'fetchEvents');
    } finally {
      setLoadingEvents(false);
    }
  }, [getAuthHeaders, handleError]);

  // Fetch geofence event statistics
  const fetchEventStats = useCallback(async (deviceId?: number, geofenceId?: number, days: number = 30) => {
    setLoadingStats(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      
      if (deviceId) {
        params.append('device_id', deviceId.toString());
      }
      if (geofenceId) {
        params.append('geofence_id', geofenceId.toString());
      }
      params.append('days', days.toString());
      
      const response = await fetch(`${API_BASE_URL}/geofences/events/stats?${params}`, {
        headers: getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: GeofenceEventStats = await response.json();
      setEventStats(data);
    } catch (err) {
      handleError(err, 'fetchEventStats');
    } finally {
      setLoadingStats(false);
    }
  }, [getAuthHeaders, handleError]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Clear current geofence
  const clearGeofence = useCallback(() => {
    setGeofence(null);
  }, []);

  return {
    // Data
    geofences,
    geofence,
    stats,
    events,
    eventStats,
    
    // Loading states
    loading,
    loadingGeofence,
    loadingStats,
    loadingEvents,
    
    // Error states
    error,
    
    // Actions
    fetchGeofences,
    fetchGeofence,
    createGeofence,
    updateGeofence,
    deleteGeofence,
    fetchStats,
    testGeofences,
    fetchEvents,
    fetchEventStats,
    
    // Utility functions
    clearError,
    clearGeofence
  };
};
