import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS, getAuthHeaders } from '../api/apiConfig';

export interface Position {
  id: number;
  device_id: number;
  protocol: string;
  device_time?: string;
  server_time: string;
  valid: boolean;
  latitude: number;
  longitude: number;
  altitude?: number;
  speed?: number;
  course?: number;
  address?: string;
  accuracy?: number;
  attributes?: Record<string, any>;
}

export interface PositionFilters {
  device_id?: number;
  from_time?: string;
  to_time?: string;
  limit?: number;
}

export const usePositions = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [latestPositions, setLatestPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch positions with filters
  const fetchPositions = useCallback(async (filters: PositionFilters = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (filters.device_id) params.append('device_id', filters.device_id.toString());
      if (filters.from_time) params.append('from_time', filters.from_time);
      if (filters.to_time) params.append('to_time', filters.to_time);
      if (filters.limit) params.append('limit', filters.limit.toString());

      const response = await fetch(`${API_ENDPOINTS.POSITIONS}?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch positions: ${response.statusText}`);
      }

      const data = await response.json();
      setPositions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch positions');
      console.error('Error fetching positions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch latest positions for all devices
  const fetchLatestPositions = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.POSITIONS}/latest`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch latest positions: ${response.statusText}`);
      }

      const data = await response.json();
      setLatestPositions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch latest positions');
      console.error('Error fetching latest positions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Get positions for a specific device
  const getDevicePositions = useCallback(async (deviceId: number, limit: number = 100) => {
    return fetchPositions({ device_id: deviceId, limit });
  }, [fetchPositions]);

  // Get recent positions (last 24 hours)
  const getRecentPositions = useCallback(async (limit: number = 100) => {
    const fromTime = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    return fetchPositions({ from_time: fromTime, limit });
  }, [fetchPositions]);

  // Load latest positions on mount
  useEffect(() => {
    fetchLatestPositions();
  }, [fetchLatestPositions]);

  return {
    positions,
    latestPositions,
    loading,
    error,
    fetchPositions,
    fetchLatestPositions,
    getDevicePositions,
    getRecentPositions,
  };
};
