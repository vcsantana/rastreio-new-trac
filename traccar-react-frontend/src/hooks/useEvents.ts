import { useState, useCallback, useEffect } from 'react';
import { useAuth } from './useAuth';
import { useWebSocket } from './useWebSocket';
import {
  Event,
  EventFilters,
  EventListResponse,
  EventStats,
  EventTypeInfo,
  EventNotification,
  EventReport
} from '../types/events';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface UseEventsReturn {
  events: Event[];
  eventStats: EventStats | null;
  eventTypes: string[];
  eventTypeInfo: Record<string, EventTypeInfo>;
  notifications: EventNotification[];
  loading: boolean;
  loadingStats: boolean;
  loadingTypes: boolean;
  error: string | null;
  total: number;
  page: number;
  size: number;
  hasNext: boolean;
  hasPrev: boolean;
  fetchEvents: (filters?: EventFilters) => Promise<void>;
  fetchEvent: (eventId: number) => Promise<Event | null>;
  fetchEventStats: (days?: number) => Promise<void>;
  fetchEventTypes: () => Promise<void>;
  createEvent: (eventData: Partial<Event>) => Promise<Event | null>;
  updateEvent: (eventId: number, eventData: Partial<Event>) => Promise<Event | null>;
  deleteEvent: (eventId: number) => Promise<boolean>;
  cleanupOldEvents: (days: number) => Promise<number>;
  exportEventsCSV: (filters: EventFilters) => Promise<void>;
  generateEventReport: (reportData: Partial<EventReport>) => Promise<EventReport | null>;
  markNotificationAsRead: (notificationId: string) => void;
  clearNotifications: () => void;
  refreshEvents: () => Promise<void>;
}

export const useEvents = (): UseEventsReturn => {
  const { token } = useAuth();
  const { subscribe, unsubscribe, messages } = useWebSocket();
  
  const [events, setEvents] = useState<Event[]>([]);
  const [eventStats, setEventStats] = useState<EventStats | null>(null);
  const [eventTypes, setEventTypes] = useState<string[]>([]);
  const [eventTypeInfo, setEventTypeInfo] = useState<Record<string, EventTypeInfo>>({});
  const [notifications, setNotifications] = useState<EventNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(50);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  const handleError = (err: any, operation: string) => {
    console.error(`Error in ${operation}:`, err);
    setError(err.message || `Failed to ${operation}`);
  };

  const clearError = () => setError(null);

  // Fetch events with filters
  const fetchEvents = useCallback(async (filters: EventFilters = {}) => {
    if (!token) return;
    
    setLoading(true);
    clearError();
    
    try {
      const params = new URLSearchParams();
      
      if (filters.device_id) params.append('device_id', filters.device_id.toString());
      if (filters.event_type) params.append('event_type', filters.event_type);
      if (filters.start_time) params.append('start_time', filters.start_time);
      if (filters.end_time) params.append('end_time', filters.end_time);
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.size) params.append('size', filters.size.toString());
      
      const response = await fetch(`${API_BASE_URL}/api/events/?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: EventListResponse = await response.json();
      setEvents(data.events || []);
      setTotal(data.total);
      setPage(data.page);
      setSize(data.size);
      setHasNext(data.has_next);
      setHasPrev(data.has_prev);
    } catch (err) {
      handleError(err, 'fetchEvents');
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Fetch single event
  const fetchEvent = useCallback(async (eventId: number): Promise<Event | null> => {
    if (!token) return null;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const event: Event = await response.json();
      return event;
    } catch (err) {
      handleError(err, 'fetchEvent');
      return null;
    }
  }, [token]);

  // Fetch event statistics
  const fetchEventStats = useCallback(async (days: number = 7) => {
    if (!token) return;
    
    setLoadingStats(true);
    clearError();
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/events/stats/summary?days=${days}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const stats: EventStats = await response.json();
      setEventStats(stats);
    } catch (err) {
      handleError(err, 'fetchEventStats');
    } finally {
      setLoadingStats(false);
    }
  }, [token]);

  // Fetch event types information
  const fetchEventTypes = useCallback(async () => {
    if (!token) return;
    
    setLoadingTypes(true);
    clearError();
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/events/types/info`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setEventTypes(data.types || []);
      setEventTypeInfo(data.type_info || {});
    } catch (err) {
      handleError(err, 'fetchEventTypes');
    } finally {
      setLoadingTypes(false);
    }
  }, [token]);

  // Create event
  const createEvent = useCallback(async (eventData: Partial<Event>): Promise<Event | null> => {
    if (!token) return null;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/events/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const event: Event = await response.json();
      return event;
    } catch (err) {
      handleError(err, 'createEvent');
      return null;
    }
  }, [token]);

  // Update event
  const updateEvent = useCallback(async (eventId: number, eventData: Partial<Event>): Promise<Event | null> => {
    if (!token) return null;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const event: Event = await response.json();
      return event;
    } catch (err) {
      handleError(err, 'updateEvent');
      return null;
    }
  }, [token]);

  // Delete event
  const deleteEvent = useCallback(async (eventId: number): Promise<boolean> => {
    if (!token) return false;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return true;
    } catch (err) {
      handleError(err, 'deleteEvent');
      return false;
    }
  }, [token]);

  // Cleanup old events
  const cleanupOldEvents = useCallback(async (days: number): Promise<number> => {
    if (!token) return 0;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/events/cleanup?days=${days}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.deleted_count || 0;
    } catch (err) {
      handleError(err, 'cleanupOldEvents');
      return 0;
    }
  }, [token]);

  // Export events to CSV
  const exportEventsCSV = useCallback(async (filters: EventFilters) => {
    if (!token) return;
    
    try {
      const params = new URLSearchParams();
      
      if (filters.start_time) params.append('start_date', filters.start_time);
      if (filters.end_time) params.append('end_date', filters.end_time);
      if (filters.device_id) params.append('device_ids', filters.device_id.toString());
      if (filters.event_type) params.append('event_types', filters.event_type);
      
      const response = await fetch(`${API_BASE_URL}/api/events/reports/export/csv?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `events_${filters.start_time}_to_${filters.end_time}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      handleError(err, 'exportEventsCSV');
    }
  }, [token]);

  // Generate event report
  const generateEventReport = useCallback(async (reportData: Partial<EventReport>): Promise<EventReport | null> => {
    if (!token) return null;
    
    try {
      const params = new URLSearchParams();
      
      if (reportData.start_date) params.append('start_date', reportData.start_date);
      if (reportData.end_date) params.append('end_date', reportData.end_date);
      if (reportData.device_ids) {
        reportData.device_ids.forEach(id => params.append('device_ids', id.toString()));
      }
      
      const response = await fetch(`${API_BASE_URL}/api/events/reports/summary?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const report: EventReport = await response.json();
      return report;
    } catch (err) {
      handleError(err, 'generateEventReport');
      return null;
    }
  }, [token]);

  // Mark notification as read
  const markNotificationAsRead = useCallback((notificationId: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === notificationId 
          ? { ...notification, read: true }
          : notification
      )
    );
  }, []);

  // Clear all notifications
  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Refresh events
  const refreshEvents = useCallback(async () => {
    await fetchEvents({ page, size });
  }, [fetchEvents, page, size]);

  // WebSocket integration for real-time events
  useEffect(() => {
    if (token) {
      subscribe('events');
      
      return () => {
        unsubscribe('events');
      };
    }
  }, [token, subscribe, unsubscribe]);

  // Handle incoming event messages
  useEffect(() => {
    if (!messages) return;
    
    const eventMessages = messages.filter(msg => msg.type === 'events');
    
    if (eventMessages.length > 0) {
      const latestMessage = eventMessages[eventMessages.length - 1];
      
      if (latestMessage.data) {
        const newEvent: Event = latestMessage.data;
        
        // Add to events list
        setEvents(prev => [newEvent, ...prev]);
        
        // Add to notifications
        const notification: EventNotification = {
          id: `event_${newEvent.id}_${Date.now()}`,
          event: newEvent,
          read: false,
          created_at: new Date().toISOString(),
        };
        
        setNotifications(prev => [notification, ...prev]);
      }
    }
  }, [messages]);

  // Load initial data
  useEffect(() => {
    if (token) {
      fetchEventTypes();
      fetchEventStats();
    }
  }, [token, fetchEventTypes, fetchEventStats]);

  return {
    events,
    eventStats,
    eventTypes,
    eventTypeInfo,
    notifications,
    loading,
    loadingStats,
    loadingTypes,
    error,
    total,
    page,
    size,
    hasNext,
    hasPrev,
    fetchEvents,
    fetchEvent,
    fetchEventStats,
    fetchEventTypes,
    createEvent,
    updateEvent,
    deleteEvent,
    cleanupOldEvents,
    exportEventsCSV,
    generateEventReport,
    markNotificationAsRead,
    clearNotifications,
    refreshEvents,
  };
};
