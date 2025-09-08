import { useState, useCallback, useEffect } from 'react';
import { API_ENDPOINTS } from '../api/apiConfig';
import { useAuth } from '../contexts/AuthContext';

export interface Device {
  id: number;
  name: string;
  unique_id: string;
  phone?: string;
  model?: string;
  contact?: string;
  category?: string;
  license_plate?: string;
  disabled: boolean;
  group_id?: number;
  person_id?: number;
  status?: string;
  protocol?: string;
  last_update?: string;
  created_at: string;
  group_name?: string;
  person_name?: string;
}

export interface CreateDeviceData {
  name: string;
  unique_id: string;
  phone?: string;
  model?: string;
  contact?: string;
  category?: string;
  license_plate?: string;
  group_id?: number;
  person_id?: number;
  protocol?: string;
}

export interface UpdateDeviceData extends Partial<CreateDeviceData> {
  id?: number;
}

export const useDevices = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.DEVICES, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [token]);

  const createDevice = useCallback(async (deviceData: CreateDeviceData): Promise<Device | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.DEVICES, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deviceData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const newDevice = await response.json();
      setDevices(prev => [...prev, newDevice]);
      return newDevice;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create device');
      return null;
    } finally {
      setLoading(false);
    }
  }, [token]);

  const updateDevice = useCallback(async (deviceId: number, deviceData: UpdateDeviceData): Promise<Device | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.DEVICES}/${deviceId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deviceData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const updatedDevice = await response.json();
      setDevices(prev => prev.map(device => 
        device.id === deviceId ? updatedDevice : device
      ));
      return updatedDevice;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update device');
      return null;
    } finally {
      setLoading(false);
    }
  }, [token]);

  const deleteDevice = useCallback(async (deviceId: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.DEVICES}/${deviceId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setDevices(prev => prev.filter(device => device.id !== deviceId));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete device');
      return false;
    } finally {
      setLoading(false);
    }
  }, [token]);

  const toggleDeviceStatus = useCallback(async (deviceId: number, disabled: boolean): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.DEVICES}/${deviceId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ disabled }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const updatedDevice = await response.json();
      setDevices(prev => prev.map(device => 
        device.id === deviceId ? updatedDevice : device
      ));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle device status');
      return false;
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Auto-fetch devices when component mounts
  useEffect(() => {
    if (token) {
      fetchDevices();
    }
  }, [fetchDevices, token]);

  return {
    devices,
    loading,
    error,
    fetchDevices,
    createDevice,
    updateDevice,
    deleteDevice,
    toggleDeviceStatus,
  };
};