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

  return {
    groups,
    loading,
    error,
    fetchGroups,
  };
};