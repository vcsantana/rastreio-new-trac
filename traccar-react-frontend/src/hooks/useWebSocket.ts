import { useWebSocket as useWebSocketContext } from '../contexts/WebSocketContext';
import { useEffect, useState, useCallback, useMemo } from 'react';

export const useWebSocket = () => {
  const {
    connected,
    subscribe,
    unsubscribe,
    sendMessage,
    lastMessage,
    connectionError,
  } = useWebSocketContext();

  return {
    connected,
    subscribe,
    unsubscribe,
    sendMessage,
    lastMessage,
    connectionError,
  };
};

// Hook for subscribing to specific message types
export const useWebSocketSubscription = (subscriptionType: string) => {
  const { subscribe, unsubscribe, lastMessage } = useWebSocketContext();
  const [messages, setMessages] = useState<any[]>([]);

  // Memoize the message handler to prevent unnecessary re-renders
  const handleNewMessage = useCallback((newMessage: any) => {
    if (newMessage && newMessage.type === subscriptionType) {
      setMessages(prev => [...prev, newMessage]);
    }
  }, [subscriptionType]);

  useEffect(() => {
    if (subscriptionType) {
      subscribe(subscriptionType);
      
      return () => {
        unsubscribe(subscriptionType);
      };
    }
  }, [subscriptionType]); // Removed subscribe/unsubscribe from dependencies

  useEffect(() => {
    if (lastMessage) {
      handleNewMessage(lastMessage);
    }
  }, [lastMessage, handleNewMessage]);

  // Memoize the return value to prevent unnecessary re-renders
  return useMemo(() => ({
    messages,
    lastMessage,
  }), [messages, lastMessage]);
};

// Hook for position updates
export const usePositionUpdates = () => {
  const { messages, lastMessage } = useWebSocketSubscription('positions');
  
  // Memoize the filtered messages to prevent unnecessary re-renders
  const positionMessages = useMemo(() => 
    messages.filter(msg => msg.type === 'position'), 
    [messages]
  );
  
  // Memoize the return value
  return useMemo(() => ({
    positions: positionMessages.map(msg => msg.data),
    lastPosition: positionMessages[positionMessages.length - 1]?.data || null,
  }), [positionMessages]);
};

// Hook for device status updates
export const useDeviceStatusUpdates = () => {
  const { messages, lastMessage } = useWebSocketSubscription('devices');
  
  // Memoize the filtered messages to prevent unnecessary re-renders
  const deviceMessages = useMemo(() => 
    messages.filter(msg => msg.type === 'device_status'), 
    [messages]
  );
  
  // Memoize the return value
  return useMemo(() => ({
    deviceUpdates: deviceMessages.map(msg => msg.data),
    lastDeviceUpdate: deviceMessages[deviceMessages.length - 1]?.data || null,
  }), [deviceMessages]);
};

// Hook for event updates
export const useEventUpdates = () => {
  const { messages, lastMessage } = useWebSocketSubscription('events');
  
  const eventMessages = messages.filter(msg => msg.type === 'event');
  
  return {
    events: eventMessages.map(msg => msg.data),
    lastEvent: eventMessages[eventMessages.length - 1]?.data || null,
  };
};
