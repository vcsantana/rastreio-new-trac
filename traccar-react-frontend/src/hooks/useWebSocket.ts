import { useWebSocket as useWebSocketContext } from '../contexts/WebSocketContext';
import { useEffect, useState } from 'react';

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

  useEffect(() => {
    if (subscriptionType) {
      subscribe(subscriptionType);
      
      return () => {
        unsubscribe(subscriptionType);
      };
    }
  }, [subscriptionType, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage) {
      setMessages(prev => [...prev, lastMessage]);
    }
  }, [lastMessage]);

  return {
    messages,
    lastMessage,
  };
};

// Hook for position updates
export const usePositionUpdates = () => {
  const { messages, lastMessage } = useWebSocketSubscription('positions');
  
  const positionMessages = messages.filter(msg => msg.type === 'position');
  
  return {
    positions: positionMessages.map(msg => msg.data),
    lastPosition: positionMessages[positionMessages.length - 1]?.data || null,
  };
};

// Hook for device status updates
export const useDeviceStatusUpdates = () => {
  const { messages, lastMessage } = useWebSocketSubscription('devices');
  
  const deviceMessages = messages.filter(msg => msg.type === 'device_status');
  
  return {
    deviceUpdates: deviceMessages.map(msg => msg.data),
    lastDeviceUpdate: deviceMessages[deviceMessages.length - 1]?.data || null,
  };
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
