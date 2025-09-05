import { useState } from 'react';
import { API_ENDPOINTS } from '../api/apiConfig';
import { useAuth } from '../contexts/AuthContext';

export interface User {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  is_admin: boolean;
  phone?: string;
  map?: string;
  latitude?: string;
  longitude?: string;
  zoom?: number;
  coordinate_format?: string;
  expiration_time?: string;
  device_limit?: number;
  user_limit?: number;
  device_readonly?: boolean;
  limit_commands?: boolean;
  disable_reports?: boolean;
  fixed_email?: boolean;
  poi_layer?: string;
  attributes?: any;
  created_at: string;
  updated_at?: string;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  inactive_users: number;
}

export interface UserPermission {
  device_permissions: Array<{ id: number; name: string; unique_id: string }>;
  group_permissions: Array<{ id: number; name: string; description?: string }>;
  managed_users: Array<{ id: number; name: string; email: string }>;
  managers: Array<{ id: number; name: string; email: string }>;
}

export interface UserCreate {
  email: string;
  name: string;
  password: string;
  is_active?: boolean;
  is_admin?: boolean;
  phone?: string;
  map?: string;
  latitude?: string;
  longitude?: string;
  zoom?: number;
  coordinate_format?: string;
  expiration_time?: string;
  device_limit?: number;
  user_limit?: number;
  device_readonly?: boolean;
  limit_commands?: boolean;
  disable_reports?: boolean;
  fixed_email?: boolean;
  poi_layer?: string;
  attributes?: any;
}

export interface UserUpdate {
  email?: string;
  name?: string;
  password?: string;
  is_active?: boolean;
  is_admin?: boolean;
  phone?: string;
  map?: string;
  latitude?: string;
  longitude?: string;
  zoom?: number;
  coordinate_format?: string;
  expiration_time?: string;
  device_limit?: number;
  user_limit?: number;
  device_readonly?: boolean;
  limit_commands?: boolean;
  disable_reports?: boolean;
  fixed_email?: boolean;
  poi_layer?: string;
  attributes?: any;
}

export interface UserPermissionUpdate {
  device_ids?: number[];
  group_ids?: number[];
  managed_user_ids?: number[];
}

export interface UserFilter {
  search?: string;
  is_active?: boolean;
  is_admin?: boolean;
  limit?: number;
  offset?: number;
}

export const useUsers = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchUsers = async (filters: UserFilter = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.is_active !== undefined) params.append('is_active', filters.is_active.toString());
      if (filters.is_admin !== undefined) params.append('is_admin', filters.is_admin.toString());
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.offset) params.append('offset', filters.offset.toString());

      const response = await fetch(`${API_ENDPOINTS.USERS}?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserStats = async (): Promise<UserStats | null> => {
    try {
      const response = await fetch(`${API_ENDPOINTS.USERS}/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    }
  };

  const fetchUser = async (userId: number): Promise<User | null> => {
    try {
      const response = await fetch(`${API_ENDPOINTS.USERS}/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    }
  };

  const createUser = async (userData: UserCreate): Promise<User | null> => {
    try {
      const response = await fetch(API_ENDPOINTS.USERS, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const newUser = await response.json();
      setUsers(prev => [...prev, newUser]);
      return newUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    }
  };

  const updateUser = async (userId: number, userData: UserUpdate): Promise<User | null> => {
    try {
      const response = await fetch(`${API_ENDPOINTS.USERS}/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const updatedUser = await response.json();
      setUsers(prev => prev.map(user => user.id === userId ? updatedUser : user));
      return updatedUser;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    }
  };

  const deleteUser = async (userId: number): Promise<boolean> => {
    try {
      const response = await fetch(`${API_ENDPOINTS.USERS}/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      setUsers(prev => prev.filter(user => user.id !== userId));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return false;
    }
  };

  const fetchUserPermissions = async (userId: number): Promise<UserPermission | null> => {
    try {
      const response = await fetch(`${API_ENDPOINTS.USERS}/${userId}/permissions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    }
  };

  const updateUserPermissions = async (userId: number, permissions: UserPermissionUpdate): Promise<boolean> => {
    try {
      const response = await fetch(`${API_ENDPOINTS.USERS}/${userId}/permissions`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(permissions),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return false;
    }
  };

  return {
    users,
    loading,
    error,
    fetchUsers,
    fetchUserStats,
    fetchUser,
    createUser,
    updateUser,
    deleteUser,
    fetchUserPermissions,
    updateUserPermissions,
  };
};
