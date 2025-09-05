import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS, getAuthHeaders } from '../api/apiConfig';

export interface Person {
  id: number;
  name: string;
  person_type: 'physical' | 'legal';
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  active: boolean;
  cpf?: string;
  birth_date?: string;
  cnpj?: string;
  company_name?: string;
  trade_name?: string;
  created_at: string;
  updated_at?: string;
  group_count?: number;
}

export interface CreatePersonData {
  name: string;
  person_type: 'physical' | 'legal';
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  active?: boolean;
  cpf?: string;
  birth_date?: string;
  cnpj?: string;
  company_name?: string;
  trade_name?: string;
}

export interface UpdatePersonData {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  active?: boolean;
  cpf?: string;
  birth_date?: string;
  cnpj?: string;
  company_name?: string;
  trade_name?: string;
}

export const usePersons = () => {
  const [persons, setPersons] = useState<Person[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPersons = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.PERSONS, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch persons: ${response.statusText}`);
      }

      const data = await response.json();
      setPersons(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch persons');
      console.error('Error fetching persons:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createPerson = useCallback(async (personData: CreatePersonData): Promise<Person | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.PERSONS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(personData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to create person: ${errorText}`);
      }

      const newPerson = await response.json();
      setPersons(prev => [...prev, newPerson]);
      return newPerson;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create person');
      console.error('Error creating person:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const updatePerson = useCallback(async (personId: number, personData: UpdatePersonData): Promise<Person | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.PERSONS}/${personId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(personData),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to update person: ${errorText}`);
      }

      const updatedPerson = await response.json();
      setPersons(prev => prev.map(person => 
        person.id === personId ? updatedPerson : person
      ));
      return updatedPerson;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update person');
      console.error('Error updating person:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const deletePerson = useCallback(async (personId: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.PERSONS}/${personId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to delete person: ${errorText}`);
      }

      setPersons(prev => prev.filter(person => person.id !== personId));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete person');
      console.error('Error deleting person:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const togglePersonStatus = useCallback(async (personId: number): Promise<boolean> => {
    const person = persons.find(p => p.id === personId);
    if (!person) return false;

    return await updatePerson(personId, { active: !person.active }) !== null;
  }, [persons, updatePerson]);

  useEffect(() => {
    fetchPersons();
  }, [fetchPersons]);

  return {
    persons,
    loading,
    error,
    fetchPersons,
    createPerson,
    updatePerson,
    deletePerson,
    togglePersonStatus,
  };
};
