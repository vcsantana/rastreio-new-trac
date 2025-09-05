import { useState } from 'react';
import { API_ENDPOINTS } from '../api/apiConfig';
import { useAuth } from '../contexts/AuthContext';

export interface Group {
  id: number;
  name: string;
  description?: string;
  person_id?: number;
  created_at: string;
  updated_at?: string;
  person_name?: string;
  device_count?: number;
  disabled?: boolean;
}

export interface GroupCreate {
  name: string;
  description?: string;
  person_id?: number;
  disabled?: boolean;
}

export interface GroupUpdate {
  name?: string;
  description?: string;
  person_id?: number;
  disabled?: boolean;
}

export const useGroups = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchGroups = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.GROUPS, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setGroups(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const createGroup = async (groupData: GroupCreate): Promise<Group | null> => {
    try {
      const response = await fetch(API_ENDPOINTS.GROUPS, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(groupData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const newGroup = await response.json();
      setGroups(prev => [...prev, newGroup]);
      return newGroup;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    }
  };

  const updateGroup = async (groupId: number, groupData: GroupUpdate): Promise<Group | null> => {
    try {
      const response = await fetch(`${API_ENDPOINTS.GROUPS}/${groupId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(groupData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const updatedGroup = await response.json();
      setGroups(prev => prev.map(group => group.id === groupId ? updatedGroup : group));
      return updatedGroup;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    }
  };

  const deleteGroup = async (groupId: number): Promise<boolean> => {
    try {
      const response = await fetch(`${API_ENDPOINTS.GROUPS}/${groupId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setGroups(prev => prev.filter(group => group.id !== groupId));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return false;
    }
  };

  const toggleGroupStatus = async (groupId: number): Promise<boolean> => {
    try {
      const group = groups.find(g => g.id === groupId);
      if (!group) return false;

      const response = await fetch(`${API_ENDPOINTS.GROUPS}/${groupId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ disabled: !group.disabled }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const updatedGroup = await response.json();
      setGroups(prev => prev.map(g => g.id === groupId ? updatedGroup : g));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return false;
    }
  };

  return {
    groups,
    loading,
    error,
    setError,
    fetchGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    toggleGroupStatus,
  };
};