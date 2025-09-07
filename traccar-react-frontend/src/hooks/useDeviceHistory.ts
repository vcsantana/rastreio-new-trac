import { useState, useEffect, useCallback } from 'react';

interface Position {
  id: number;
  deviceId: number;
  latitude: number;
  longitude: number;
  course?: number;
  speed?: number;
  fixTime?: string;
  serverTime?: string;
  deviceTime?: string;
  altitude?: number;
  valid?: boolean;
  address?: string;
  accuracy?: number;
  attributes?: Record<string, any>;
}

interface UseDeviceHistoryOptions {
  deviceId?: number;
  fromTime?: Date;
  toTime?: Date;
  limit?: number;
  enabled?: boolean;
}

interface UseDeviceHistoryReturn {
  positions: Position[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export const useDeviceHistory = ({
  deviceId,
  fromTime,
  toTime,
  limit = 1000,
  enabled = true
}: UseDeviceHistoryOptions): UseDeviceHistoryReturn => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    if (!deviceId || !enabled) {
      setPositions([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (fromTime) {
        params.append('from_time', fromTime.toISOString());
      }
      if (toTime) {
        params.append('to_time', toTime.toISOString());
      }
      params.append('limit', limit.toString());

      const response = await fetch(
        `/api/positions/device/${deviceId}/history?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch device history: ${response.statusText}`);
      }

      const data = await response.json();
      setPositions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch device history');
      setPositions([]);
    } finally {
      setLoading(false);
    }
  }, [deviceId, fromTime, toTime, limit, enabled]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return {
    positions,
    loading,
    error,
    refetch: fetchHistory,
  };
};
