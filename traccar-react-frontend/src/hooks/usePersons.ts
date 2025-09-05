import { useState } from 'react';
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

export const usePersons = () => {
  const [persons, setPersons] = useState<Person[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const fetchPersons = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.PERSONS, {
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
  };

  return {
    persons,
    loading,
    error,
    fetchPersons,
  };
};