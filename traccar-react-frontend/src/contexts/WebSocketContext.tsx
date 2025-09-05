import React, { createContext, useContext, ReactNode, useEffect, useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';

interface WebSocketMessage {
  type: 'position' | 'event' | 'device_status' | 'heartbeat' | 'error' | 'info';
  data: any;
  timestamp: string;
}

interface WebSocketContextType {
  connected: boolean;
  subscribe: (type: string) => void;
  unsubscribe: (type: string) => void;
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  connectionError: string | null;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [heartbeatInterval, setHeartbeatInterval] = useState<NodeJS.Timeout | null>(null);
  
  const { user, token } = useAuth();

  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds

  const connect = useCallback(() => {
    if (!user || !token) {
      console.log('No user or token available for WebSocket connection');
      return;
    }

    try {
      const wsUrl = `ws://localhost:8000/ws/${user.id}`;
      console.log('Connecting to WebSocket:', wsUrl);
      
      const newSocket = new WebSocket(wsUrl);
      
      newSocket.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setConnectionError(null);
        setReconnectAttempts(0);
        
        // Start heartbeat
        const interval = setInterval(() => {
          if (newSocket.readyState === WebSocket.OPEN) {
            newSocket.send(JSON.stringify({ type: 'heartbeat' }));
          }
        }, 30000); // Send heartbeat every 30 seconds
        
        setHeartbeatInterval(interval);
      };

      newSocket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          // Handle different message types
          switch (message.type) {
            case 'position':
              console.log('Position update received:', message.data);
              // You can dispatch to Redux store here if needed
              break;
            case 'event':
              console.log('Event received:', message.data);
              break;
            case 'device_status':
              console.log('Device status update:', message.data);
              break;
            case 'heartbeat':
              console.log('Heartbeat received');
              break;
            case 'error':
              console.error('WebSocket error:', message.data);
              break;
            case 'info':
              console.log('WebSocket info:', message.data);
              break;
            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      newSocket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnected(false);
        setSocket(null);
        
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
          setHeartbeatInterval(null);
        }
        
        // Attempt to reconnect if not a manual close
        if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, reconnectDelay);
        }
      };

      newSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };

      setSocket(newSocket);
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionError('Failed to create WebSocket connection');
    }
  }, [user, token, reconnectAttempts, heartbeatInterval]);

  const disconnect = useCallback(() => {
    if (socket) {
      socket.close(1000, 'Manual disconnect');
      setSocket(null);
    }
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      setHeartbeatInterval(null);
    }
    setConnected(false);
  }, [socket, heartbeatInterval]);

  const subscribe = useCallback((type: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'subscribe',
        data: { type }
      }));
      console.log(`Subscribed to ${type}`);
    }
  }, [socket]);

  const unsubscribe = useCallback((type: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'unsubscribe',
        data: { type }
      }));
      console.log(`Unsubscribed from ${type}`);
    }
  }, [socket]);

  const sendMessage = useCallback((message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, [socket]);

  // Connect when user is available
  useEffect(() => {
    if (user && token && !connected) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [user, token, connect, disconnect, connected]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  const value: WebSocketContextType = {
    connected,
    subscribe,
    unsubscribe,
    sendMessage,
    lastMessage,
    connectionError,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};
