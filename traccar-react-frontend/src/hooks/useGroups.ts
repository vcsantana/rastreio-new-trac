import { useState, useCallback, useEffect } from 'react';
import { API_ENDPOINTS, getAuthHeaders } from '../api/apiConfig';

export interface Group {
  id: number;
  name: string;
  description?: string;
  disabled: boolean;
  created_at: string;
  updated_at?: string;
  device_count: number;
}

export interface CreateGroupData {
  name: string;
  description?: string;
  disabled?: boolean;
}

export interface UpdateGroupData {
  name?: string;
  description?: string;
  disabled?: boolean;
}

export const useGroups = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all groups
  const fetchGroups = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.GROUPS, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch groups: ${response.statusText}`);
      }

      const groupsData = await response.json();
      setGroups(groupsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch groups');
      console.error('Error fetching groups:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create a new group
  const createGroup = useCallback(async (groupData: CreateGroupData): Promise<Group | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.GROUPS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(groupData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create group: ${response.statusText}`);
      }

      const newGroup = await response.json();
      setGroups(prev => [...prev, newGroup]);
      return newGroup;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create group');
      console.error('Error creating group:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update an existing group
  const updateGroup = useCallback(async (groupId: number, groupData: UpdateGroupData): Promise<Group | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const url = `${API_ENDPOINTS.GROUPS}/${groupId}`;
      const headers = {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      };
      
      console.log('Updating group:', { url, headers, groupData });
      
      const response = await fetch(url, {
        method: 'PUT',
        headers,
        body: JSON.stringify(groupData),
      });

      console.log('Update response:', { status: response.status, statusText: response.statusText });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Update error response:', errorText);
        throw new Error(`Failed to update group: ${response.statusText}`);
      }

      const updatedGroup = await response.json();
      console.log('Updated group:', updatedGroup);
      
      setGroups(prev => prev.map(group => 
        group.id === groupId ? updatedGroup : group
      ));
      return updatedGroup;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update group');
      console.error('Error updating group:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete a group
  const deleteGroup = useCallback(async (groupId: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.GROUPS}/${groupId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Delete error response:', errorText);
        throw new Error(`Failed to delete group: ${response.statusText}`);
      }

      setGroups(prev => prev.filter(group => group.id !== groupId));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete group');
      console.error('Error deleting group:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // Toggle group status (enable/disable)
  const toggleGroupStatus = useCallback(async (groupId: number): Promise<boolean> => {
    const group = groups.find(g => g.id === groupId);
    if (!group) return false;

    const updated = await updateGroup(groupId, { disabled: !group.disabled });
    return updated !== null;
  }, [groups, updateGroup]);

  // Load groups on mount
  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  return {
    groups,
    loading,
    error,
    fetchGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    toggleGroupStatus,
  };
};
