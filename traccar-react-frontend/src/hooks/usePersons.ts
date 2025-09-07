import { useState, useCallback } from 'react';
import { API_ENDPOINTS } from '../api/apiConfig';
import { useAuth } from '../contexts/AuthContext';

export interface Person {
  id: number;
  name: string;
  person_type: 'physical' | 'legal';
  cpf?: string;
  birth_date?: string;
  cnpj?: string;
  company_name?: string;
  trade_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  active: boolean;
  created_at: string;
  updated_at?: string;
  group_count?: number;
}

export interface CreatePersonData {
  name: string;
  person_type: 'physical' | 'legal';
  cpf?: string;
  birth_date?: string;
  cnpj?: string;
  company_name?: string;
  trade_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  active: boolean;
}

export interface UpdatePersonData extends Partial<CreatePersonData> {
  id?: number;
}

export const usePersons = () => {
  const [persons, setPersons] = useState<Person[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchPersons = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.PERSONS}/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setPersons(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [token]);

  const createPerson = useCallback(async (personData: Partial<Person>): Promise<Person | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.PERSONS}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(personData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const newPerson = await response.json();
      setPersons(prev => [...prev, newPerson]);
      return newPerson;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create person');
      return null;
    } finally {
      setLoading(false);
    }
  }, [token]);

  const updatePerson = useCallback(async (id: number, personData: Partial<Person>): Promise<Person | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.PERSONS}/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(personData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const updatedPerson = await response.json();
      setPersons(prev => prev.map(person => 
        person.id === id ? updatedPerson : person
      ));
      return updatedPerson;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update person');
      return null;
    } finally {
      setLoading(false);
    }
  }, [token]);

  const deletePerson = useCallback(async (id: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_ENDPOINTS.PERSONS}/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      setPersons(prev => prev.filter(person => person.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete person');
      return false;
    } finally {
      setLoading(false);
    }
  }, [token]);

  const togglePersonStatus = useCallback(async (id: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      const person = persons.find(p => p.id === id);
      if (!person) {
        throw new Error('Person not found');
      }

      const response = await fetch(`${API_ENDPOINTS.PERSONS}/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ active: !person.active }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const updatedPerson = await response.json();
      setPersons(prev => prev.map(person => 
        person.id === id ? updatedPerson : person
      ));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle person status');
      return false;
    } finally {
      setLoading(false);
    }
  }, [token, persons]);

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