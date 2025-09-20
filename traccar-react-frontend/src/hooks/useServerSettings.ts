import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Types for server configuration
export interface ServerConfig {
  id: number;
  name: string;
  registration_enabled: boolean;
  limit_commands: boolean;
  map_provider: 'bing' | 'mapbox' | 'openstreetmap' | 'google';
  map_url?: string;
  bing_key?: string;
  mapbox_key?: string;
  google_key?: string;
  coordinate_format: string;
  timezone: string;
  language: string;
  distance_unit: string;
  speed_unit: string;
  volume_unit: string;
  latitude?: number;
  longitude?: number;
  zoom: number;
  poi_layer: boolean;
  traffic_layer: boolean;
  attributes?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ServerConfigUpdate {
  name?: string;
  registration_enabled?: boolean;
  limit_commands?: boolean;
  map_provider?: 'bing' | 'mapbox' | 'openstreetmap' | 'google';
  map_url?: string;
  bing_key?: string;
  mapbox_key?: string;
  google_key?: string;
  coordinate_format?: string;
  timezone?: string;
  language?: string;
  distance_unit?: string;
  speed_unit?: string;
  volume_unit?: string;
  latitude?: number;
  longitude?: number;
  zoom?: number;
  poi_layer?: boolean;
  traffic_layer?: boolean;
  attributes?: Record<string, any>;
}

export interface ServerStats {
  total_users: number;
  total_devices: number;
  total_positions: number;
  total_events: number;
  total_geofences: number;
  online_devices: number;
  offline_devices: number;
  server_uptime: number;
  memory_usage: number;
  cpu_usage: number;
  disk_usage: number;
}

export interface ServerHealth {
  status: string;
  timestamp: string;
  version: string;
  database_status: string;
  redis_status?: string;
  uptime: number;
  memory_usage: number;
  cpu_usage: number;
}

export interface ServerInfo {
  name: string;
  version: string;
  build_time?: string;
  java_version?: string;
  os_name?: string;
  os_version?: string;
  os_arch?: string;
  memory_total?: number;
  memory_used?: number;
  cpu_count?: number;
  timezone: string;
  language: string;
  distance_unit: string;
  speed_unit: string;
  volume_unit: string;
}

export const useServerSettings = () => {
  const { token } = useAuth();
  const [config, setConfig] = useState<ServerConfig | null>(null);
  const [stats, setStats] = useState<ServerStats | null>(null);
  const [health, setHealth] = useState<ServerHealth | null>(null);
  const [info, setInfo] = useState<ServerInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = 'http://localhost:8000/api';

  // Fetch server configuration
  const fetchServerConfig = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/server/config`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch server config: ${response.statusText}`);
      }

      const data = await response.json();
      setConfig(data);
    } catch (err) {
      console.error('Error fetching server config:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch server config');
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Update server configuration
  const updateServerConfig = useCallback(async (updateData: ServerConfigUpdate): Promise<boolean> => {
    if (!token || !config) return false;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/server/config`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        throw new Error(`Failed to update server config: ${response.statusText}`);
      }

      const updatedConfig = await response.json();
      setConfig(updatedConfig);
      return true;
    } catch (err) {
      console.error('Error updating server config:', err);
      setError(err instanceof Error ? err.message : 'Failed to update server config');
      return false;
    } finally {
      setLoading(false);
    }
  }, [token, config]);

  // Fetch server statistics
  const fetchServerStats = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/server/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch server stats: ${response.statusText}`);
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching server stats:', err);
    }
  }, [token]);

  // Fetch server health
  const fetchServerHealth = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/server/health`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch server health: ${response.statusText}`);
      }

      const data = await response.json();
      setHealth(data);
    } catch (err) {
      console.error('Error fetching server health:', err);
    }
  }, [token]);

  // Fetch server info
  const fetchServerInfo = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/server/info`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch server info: ${response.statusText}`);
      }

      const data = await response.json();
      setInfo(data);
    } catch (err) {
      console.error('Error fetching server info:', err);
    }
  }, [token]);

  // Restart server
  const restartServer = useCallback(async (): Promise<boolean> => {
    if (!token) return false;

    try {
      const response = await fetch(`${API_BASE_URL}/server/restart`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to restart server: ${response.statusText}`);
      }

      return true;
    } catch (err) {
      console.error('Error restarting server:', err);
      setError(err instanceof Error ? err.message : 'Failed to restart server');
      return false;
    }
  }, [token]);

  // Create backup
  const createBackup = useCallback(async (): Promise<{ success: boolean; filename?: string }> => {
    if (!token) return { success: false };

    try {
      const response = await fetch(`${API_BASE_URL}/server/backup`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to create backup: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, filename: data.filename };
    } catch (err) {
      console.error('Error creating backup:', err);
      setError(err instanceof Error ? err.message : 'Failed to create backup');
      return { success: false };
    }
  }, [token]);

  // Get server logs
  const getServerLogs = useCallback(async (lines: number = 100, level?: string): Promise<string[]> => {
    if (!token) return [];

    try {
      const params = new URLSearchParams({ lines: lines.toString() });
      if (level) params.append('level', level);

      const response = await fetch(`${API_BASE_URL}/server/logs?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch server logs: ${response.statusText}`);
      }

      const data = await response.json();
      return data.logs || [];
    } catch (err) {
      console.error('Error fetching server logs:', err);
      return [];
    }
  }, [token]);

  // Load all server data
  const loadServerData = useCallback(async () => {
    await Promise.all([
      fetchServerConfig(),
      fetchServerStats(),
      fetchServerHealth(),
      fetchServerInfo(),
    ]);
  }, [fetchServerConfig, fetchServerStats, fetchServerHealth, fetchServerInfo]);

  // Load data on mount
  useEffect(() => {
    if (token) {
      loadServerData();
    }
  }, [token, loadServerData]);

  return {
    config,
    stats,
    health,
    info,
    loading,
    error,
    setError,
    fetchServerConfig,
    updateServerConfig,
    fetchServerStats,
    fetchServerHealth,
    fetchServerInfo,
    restartServer,
    createBackup,
    getServerLogs,
    loadServerData,
  };
};





