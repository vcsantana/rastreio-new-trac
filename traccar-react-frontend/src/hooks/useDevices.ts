import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS, getAuthHeaders } from '../api/apiConfig';

export interface Device {
  id: number;
  name: string;
  unique_id: string;
  status: 'online' | 'offline' | 'unknown' | 'disabled';
  last_update?: string;
  protocol?: string;
  model?: string;
  contact?: string;
  category?: string;
  disabled?: boolean;
  phone?: string;
  group_id?: number;
  group_name?: string;
  created_at?: string;
}

export interface CreateDeviceData {
  name: string;
  unique_id: string;
  protocol?: string;
  model?: string;
  contact?: string;
  category?: string;
  phone?: string;
  group_id?: number;
}

export interface UpdateDeviceData {
  name?: string;
  unique_id?: string;
  protocol?: string;
  model?: string;
  contact?: string;
  category?: string;
  phone?: string;
  disabled?: boolean;
  group_id?: number;
}

export const useDevices = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all devices
  const fetchDevices = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.DEVICES, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch devices: ${response.statusText}`);
      }

      const data = await response.json();
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch devices');
      console.error('Error fetching devices:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create a new device
  const createDevice = useCallback(async (deviceData: CreateDeviceData): Promise<Device | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.DEVICES, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(deviceData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create device: ${response.statusText}`);
      }

      const newDevice = await response.json();
      setDevices(prev => [...prev, newDevice]);
      return newDevice;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create device');
      console.error('Error creating device:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update an existing device
  const updateDevice = useCallback(async (deviceId: number, deviceData: UpdateDeviceData): Promise<Device | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const url = `${API_ENDPOINTS.DEVICES}/${deviceId}`;
      const headers = {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      };
      
      console.log('Updating device:', { url, headers, deviceData });
      
      const response = await fetch(url, {
        method: 'PUT',
        headers,
        body: JSON.stringify(deviceData),
      });

      console.log('Update response:', { status: response.status, statusText: response.statusText });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Update error response:', errorText);
        throw new Error(`Failed to update device: ${response.statusText}`);
      }

      const updatedDevice = await response.json();
      console.log('Updated device:', updatedDevice);
      
      setDevices(prev => prev.map(device => 
        device.id === deviceId ? updatedDevice : device
      ));
      return updatedDevice;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update device');
      console.error('Error updating device:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete a device
  const deleteDevice = useCallback(async (deviceId: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.DEVICES}/${deviceId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete device: ${response.statusText}`);
      }

      setDevices(prev => prev.filter(device => device.id !== deviceId));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete device');
      console.error('Error deleting device:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // Toggle device status (enable/disable)
  const toggleDeviceStatus = useCallback(async (deviceId: number, disabled: boolean): Promise<boolean> => {
    return updateDevice(deviceId, { disabled }) !== null;
  }, [updateDevice]);

  // Get a single device by ID
  const getDevice = useCallback((deviceId: number): Device | undefined => {
    return devices.find(device => device.id === deviceId);
  }, [devices]);

  // Load devices on mount
  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  return {
    devices,
    loading,
    error,
    fetchDevices,
    createDevice,
    updateDevice,
    deleteDevice,
    toggleDeviceStatus,
    getDevice,
  };
};
