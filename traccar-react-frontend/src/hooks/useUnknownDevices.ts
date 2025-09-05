import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS, getAuthHeaders } from '../api/apiConfig';
import { useAuth } from '../contexts/AuthContext';

export interface UnknownDevice {
  id: number;
  unique_id: string;
  protocol: string;
  port: number;
  protocol_type: string;
  client_address?: string;
  first_seen: string;
  last_seen: string;
  connection_count: number;
  raw_data?: string;
  parsed_data?: Record<string, any>;
  is_registered: boolean;
  registered_device_id?: number;
  notes?: string;
}

export interface UnknownDeviceStats {
  total_count: number;
  protocol_stats: Record<string, number>;
  port_stats: Record<string, number>;
  registration_stats: Record<string, number>;
  time_period_hours: number;
}

export interface UnknownDeviceFilters {
  protocol?: string;
  port?: number;
  protocol_type?: string;
  is_registered?: boolean;
  hours?: number;
  limit?: number;
}

export const useUnknownDevices = () => {
  const [unknownDevices, setUnknownDevices] = useState<UnknownDevice[]>([]);
  const [stats, setStats] = useState<UnknownDeviceStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, token } = useAuth();

  const fetchUnknownDevices = useCallback(async (filters: UnknownDeviceFilters = {}) => {
    console.log('fetchUnknownDevices called with filters:', filters);
    console.log('isAuthenticated:', isAuthenticated, 'token:', token ? 'present' : 'missing');
    
    if (!isAuthenticated || !token) {
      setUnknownDevices([]);
      setError('Authentication required to fetch unknown devices.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.protocol) params.append('protocol', filters.protocol);
      if (filters.port) params.append('port', filters.port.toString());
      if (filters.protocol_type) params.append('protocol_type', filters.protocol_type);
      if (filters.is_registered !== undefined) params.append('is_registered', filters.is_registered.toString());
      if (filters.hours) params.append('hours', filters.hours.toString());
      if (filters.limit) params.append('limit', filters.limit.toString());

      const url = `${API_ENDPOINTS.UNKNOWN_DEVICES}${params.toString() ? `?${params.toString()}` : ''}`;
      console.log('Fetching URL:', url);
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Failed to fetch unknown devices: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Received unknown devices data:', data);
      setUnknownDevices(data);
    } catch (err) {
      console.error('Error fetching unknown devices:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch unknown devices');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, token]);

  const fetchStats = useCallback(async (hours: number = 24) => {
    if (!isAuthenticated || !token) {
      setStats(null);
      return;
    }

    try {
      const response = await fetch(`${API_ENDPOINTS.UNKNOWN_DEVICES}/stats?hours=${hours}`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch unknown devices stats: ${response.statusText}`);
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching unknown devices stats:', err);
    }
  }, [isAuthenticated, token]);

  const updateUnknownDevice = useCallback(async (id: number, updateData: Partial<UnknownDevice>) => {
    if (!isAuthenticated || !token) {
      throw new Error('Authentication required to update unknown device.');
    }

    try {
      const response = await fetch(`${API_ENDPOINTS.UNKNOWN_DEVICES}/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        throw new Error(`Failed to update unknown device: ${response.statusText}`);
      }

      const updatedDevice = await response.json();
      
      // Update the device in the local state
      setUnknownDevices(prev => 
        prev.map(device => device.id === id ? updatedDevice : device)
      );

      return updatedDevice;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update unknown device');
      throw err;
    }
  }, [isAuthenticated, token]);

  const deleteUnknownDevice = useCallback(async (id: number) => {
    if (!isAuthenticated || !token) {
      throw new Error('Authentication required to delete unknown device.');
    }

    try {
      const response = await fetch(`${API_ENDPOINTS.UNKNOWN_DEVICES}/${id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete unknown device: ${response.statusText}`);
      }

      // Remove the device from local state
      setUnknownDevices(prev => prev.filter(device => device.id !== id));

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete unknown device');
      throw err;
    }
  }, [isAuthenticated, token]);

  const registerUnknownDevice = useCallback(async (unknownDeviceId: number, deviceId: number) => {
    if (!isAuthenticated || !token) {
      throw new Error('Authentication required to register unknown device.');
    }

    try {
      const response = await fetch(`${API_ENDPOINTS.UNKNOWN_DEVICES}/${unknownDeviceId}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ device_id: deviceId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to register unknown device: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Update the device in the local state
      setUnknownDevices(prev => 
        prev.map(device => 
          device.id === unknownDeviceId 
            ? { ...device, is_registered: true, registered_device_id: deviceId }
            : device
        )
      );

      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to register unknown device');
      throw err;
    }
  }, [isAuthenticated, token]);

  useEffect(() => {
    fetchUnknownDevices();
    fetchStats();
  }, [fetchUnknownDevices, fetchStats]);

  return {
    unknownDevices,
    stats,
    loading,
    error,
    fetchUnknownDevices,
    fetchStats,
    updateUnknownDevice,
    deleteUnknownDevice,
    registerUnknownDevice,
  };
};
