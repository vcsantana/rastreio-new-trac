import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useCallback } from 'react';

interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

export const useApi = () => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  const apiCall = useCallback(async <T = any>(
    url: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> => {
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Check for authentication errors
      if (response.status === 401 || response.status === 403) {
        console.warn('Authentication error detected, logging out and redirecting to login');
        logout();
        navigate('/login', { replace: true });
        return {
          error: 'Authentication required',
          status: response.status,
        };
      }

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.detail || data.message || 'Request failed',
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      console.error('API call failed:', error);
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }, [token, logout, navigate]);

  return { apiCall };
};
