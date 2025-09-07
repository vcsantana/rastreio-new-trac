import { useState, useEffect, useCallback } from 'react';
import { 
  Command, 
  CommandCreate, 
  CommandBulkCreate, 
  CommandStats, 
  CommandQueue,
  CommandType,
  CommandStatus,
  CommandPriority,
  Device
} from '../types';
import { API_ENDPOINTS } from '../api/apiConfig';
import { useAuth } from './useAuth';

interface UseCommandsReturn {
  commands: Command[];
  commandStats: CommandStats | null;
  commandQueue: CommandQueue[];
  commandTypes: CommandType[];
  commandStatuses: CommandStatus[];
  commandPriorities: CommandPriority[];
  loading: boolean;
  error: string | null;
  createCommand: (command: CommandCreate) => Promise<Command>;
  createBulkCommands: (commands: CommandBulkCreate) => Promise<{ created: number; failed: number }>;
  retryCommand: (commandId: number) => Promise<void>;
  cancelCommand: (commandId: number) => Promise<void>;
  retryFailedCommands: (commandIds: number[]) => Promise<void>;
  cancelPendingCommands: (commandIds: number[]) => Promise<void>;
  getDeviceCommands: (deviceId: number) => Promise<Command[]>;
  refreshCommands: () => Promise<void>;
  refreshStats: () => Promise<void>;
  refreshQueue: () => Promise<void>;
}

export const useCommands = (): UseCommandsReturn => {
  const { token, isAuthenticated } = useAuth();
  const [commands, setCommands] = useState<Command[]>([]);
  const [commandStats, setCommandStats] = useState<CommandStats | null>(null);
  const [commandQueue, setCommandQueue] = useState<CommandQueue[]>([]);
  const [commandTypes, setCommandTypes] = useState<CommandType[]>([]);
  const [commandStatuses, setCommandStatuses] = useState<CommandStatus[]>([]);
  const [commandPriorities, setCommandPriorities] = useState<CommandPriority[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWithAuth = useCallback(async (url: string, options: RequestInit = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }, [token]);

  const loadCommandTypes = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const types = await fetchWithAuth(API_ENDPOINTS.COMMAND_TYPES);
      setCommandTypes(types);
    } catch (err) {
      console.error('Error loading command types:', err);
    }
  }, [fetchWithAuth, isAuthenticated]);

  const loadCommandStatuses = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const statuses = await fetchWithAuth(API_ENDPOINTS.COMMAND_STATUSES);
      setCommandStatuses(statuses);
    } catch (err) {
      console.error('Error loading command statuses:', err);
    }
  }, [fetchWithAuth, isAuthenticated]);

  const loadCommandPriorities = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const priorities = await fetchWithAuth(API_ENDPOINTS.COMMAND_PRIORITIES);
      setCommandPriorities(priorities);
    } catch (err) {
      console.error('Error loading command priorities:', err);
    }
  }, [fetchWithAuth, isAuthenticated]);

  const refreshCommands = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWithAuth(API_ENDPOINTS.COMMANDS);
      setCommands(data.items || data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load commands');
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, isAuthenticated]);

  const refreshStats = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const stats = await fetchWithAuth(API_ENDPOINTS.COMMAND_STATS);
      setCommandStats(stats);
    } catch (err) {
      console.error('Error loading command stats:', err);
    }
  }, [fetchWithAuth, isAuthenticated]);

  const refreshQueue = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const queue = await fetchWithAuth(API_ENDPOINTS.COMMAND_QUEUE);
      setCommandQueue(queue.items || queue);
    } catch (err) {
      console.error('Error loading command queue:', err);
    }
  }, [fetchWithAuth, isAuthenticated]);

  const createCommand = useCallback(async (command: CommandCreate): Promise<Command> => {
    if (!isAuthenticated) throw new Error('User not authenticated');
    setLoading(true);
    setError(null);
    try {
      const newCommand = await fetchWithAuth(API_ENDPOINTS.COMMANDS, {
        method: 'POST',
        body: JSON.stringify(command),
      });
      await refreshCommands();
      return newCommand;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create command';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, refreshCommands, isAuthenticated]);

  const createBulkCommands = useCallback(async (commands: CommandBulkCreate): Promise<{ created: number; failed: number }> => {
    if (!isAuthenticated) throw new Error('User not authenticated');
    setLoading(true);
    setError(null);
    try {
      const result = await fetchWithAuth(API_ENDPOINTS.COMMAND_BULK, {
        method: 'POST',
        body: JSON.stringify(commands),
      });
      await refreshCommands();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create bulk commands';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, refreshCommands, isAuthenticated]);

  const retryCommand = useCallback(async (commandId: number): Promise<void> => {
    if (!isAuthenticated) throw new Error('User not authenticated');
    setLoading(true);
    setError(null);
    try {
      await fetchWithAuth(API_ENDPOINTS.COMMAND_RETRY, {
        method: 'POST',
        body: JSON.stringify({ command_ids: [commandId] }),
      });
      await refreshCommands();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to retry command';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, refreshCommands, isAuthenticated]);

  const cancelCommand = useCallback(async (commandId: number): Promise<void> => {
    if (!isAuthenticated) throw new Error('User not authenticated');
    setLoading(true);
    setError(null);
    try {
      await fetchWithAuth(API_ENDPOINTS.COMMAND_CANCEL, {
        method: 'POST',
        body: JSON.stringify({ command_ids: [commandId] }),
      });
      await refreshCommands();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cancel command';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, refreshCommands, isAuthenticated]);

  const retryFailedCommands = useCallback(async (commandIds: number[]): Promise<void> => {
    if (!isAuthenticated) throw new Error('User not authenticated');
    setLoading(true);
    setError(null);
    try {
      await fetchWithAuth(API_ENDPOINTS.COMMAND_RETRY, {
        method: 'POST',
        body: JSON.stringify({ command_ids: commandIds }),
      });
      await refreshCommands();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to retry commands';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, refreshCommands, isAuthenticated]);

  const cancelPendingCommands = useCallback(async (commandIds: number[]): Promise<void> => {
    if (!isAuthenticated) throw new Error('User not authenticated');
    setLoading(true);
    setError(null);
    try {
      await fetchWithAuth(API_ENDPOINTS.COMMAND_CANCEL, {
        method: 'POST',
        body: JSON.stringify({ command_ids: commandIds }),
      });
      await refreshCommands();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cancel commands';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, refreshCommands, isAuthenticated]);

  const getDeviceCommands = useCallback(async (deviceId: number): Promise<Command[]> => {
    if (!isAuthenticated) return [];
    try {
      const commands = await fetchWithAuth(API_ENDPOINTS.DEVICE_COMMANDS(deviceId));
      return commands.items || commands;
    } catch (err) {
      console.error('Error loading device commands:', err);
      return [];
    }
  }, [fetchWithAuth, isAuthenticated]);

  // Load initial data
  useEffect(() => {
    if (isAuthenticated) {
      loadCommandTypes();
      loadCommandStatuses();
      loadCommandPriorities();
      refreshCommands();
      refreshStats();
      refreshQueue();
    }
  }, [isAuthenticated, loadCommandTypes, loadCommandStatuses, loadCommandPriorities, refreshCommands, refreshStats, refreshQueue]);

  return {
    commands,
    commandStats,
    commandQueue,
    commandTypes,
    commandStatuses,
    commandPriorities,
    loading,
    error,
    createCommand,
    createBulkCommands,
    retryCommand,
    cancelCommand,
    retryFailedCommands,
    cancelPendingCommands,
    getDeviceCommands,
    refreshCommands,
    refreshStats,
    refreshQueue,
  };
};
