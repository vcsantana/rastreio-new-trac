import { useState } from 'react';
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
  disabled: boolean;
  group_id?: number;
  status?: string;
  protocol?: string;
  last_update?: string;
  created_at: string;
  group_name?: string;
}

export const useDevices = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchDevices = async () => {
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
  };

  return {
    devices,
    loading,
    error,
    fetchDevices,
  };
};