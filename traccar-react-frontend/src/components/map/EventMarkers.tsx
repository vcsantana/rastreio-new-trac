import React, { useCallback, useMemo, useEffect, useRef } from 'react';
import { Box, Typography, Chip, IconButton, Tooltip } from '@mui/material';
import maplibregl from 'maplibre-gl';
import {
  Event as EventIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Speed as SpeedIcon,
  Settings as SettingsIcon,
  DeviceHub as DeviceIcon,
  LocationOn as LocationIcon,
  Schedule as ScheduleIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { Event, EventTypeInfo } from '../../types/events';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface EventMarkersProps {
  events: Event[];
  eventTypeInfo: Record<string, EventTypeInfo>;
  onEventSelect?: (event: Event) => void;
  showPopup?: boolean;
  clusterEvents?: boolean;
  maxZoom?: number;
  minZoom?: number;
  map?: maplibregl.Map | null;
}

const EventMarkers: React.FC<EventMarkersProps> = ({
  events,
  eventTypeInfo,
  onEventSelect,
  showPopup = true,
  clusterEvents = false,
  maxZoom = 18,
  minZoom = 1,
  map,
}) => {
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const popupsRef = useRef<maplibregl.Popup[]>([]);

  // Get event icon based on type
  const getEventIcon = (eventType: string) => {
    const typeInfo = eventTypeInfo[eventType];
    if (!typeInfo) return <EventIcon />;

    switch (typeInfo.icon) {
      case 'online':
        return <CheckCircleIcon color="success" />;
      case 'offline':
        return <ErrorIcon color="error" />;
      case 'moving':
        return <SpeedIcon color="primary" />;
      case 'stopped':
        return <CheckCircleIcon color="warning" />;
      case 'speed':
        return <SpeedIcon color="error" />;
      case 'fuel':
        return <WarningIcon color="warning" />;
      case 'ignition':
        return <CheckCircleIcon color="info" />;
      case 'maintenance':
        return <SettingsIcon color="warning" />;
      case 'command':
        return <CheckCircleIcon color="primary" />;
      case 'driver':
        return <DeviceIcon color="secondary" />;
      case 'geofence':
        return <CheckCircleIcon color="primary" />;
      case 'alarm':
        return <WarningIcon color="error" />;
      default:
        return <EventIcon />;
    }
  };

  // Get event severity color
  const getEventSeverityColor = (eventType: string) => {
    const typeInfo = eventTypeInfo[eventType];
    if (!typeInfo) return 'default';

    switch (typeInfo.severity) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  // Get marker color based on severity
  const getMarkerColor = (eventType: string) => {
    const typeInfo = eventTypeInfo[eventType];
    if (!typeInfo) return '#666666';

    switch (typeInfo.severity) {
      case 'low':
        return '#4caf50';
      case 'medium':
        return '#ff9800';
      case 'high':
        return '#f44336';
      case 'critical':
        return '#d32f2f';
      default:
        return '#666666';
    }
  };

  // Format event time
  const formatEventTime = (eventTime: string) => {
    try {
      return format(new Date(eventTime), 'dd/MM/yyyy HH:mm:ss', { locale: ptBR });
    } catch {
      return eventTime;
    }
  };

  // Format relative time
  const formatRelativeTime = (eventTime: string) => {
    try {
      const now = new Date();
      const eventDate = new Date(eventTime);
      const diffInMinutes = Math.floor((now.getTime() - eventDate.getTime()) / (1000 * 60));

      if (diffInMinutes < 1) return 'Just now';
      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
      if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
      return `${Math.floor(diffInMinutes / 1440)}d ago`;
    } catch {
      return '';
    }
  };

  // Filter events with position data
  const eventsWithPosition = useMemo(() => {
    return events.filter(event => event.position_data);
  }, [events]);

  // Handle event click
  const handleEventClick = useCallback((event: Event) => {
    if (onEventSelect) {
      onEventSelect(event);
    }
  }, [onEventSelect]);

  // Create marker element
  const createMarkerElement = (event: Event) => {
    const markerColor = getMarkerColor(event.event_type);
    const typeInfo = eventTypeInfo[event.event_type];

    const element = document.createElement('div');
    element.style.width = '24px';
    element.style.height = '24px';
    element.style.borderRadius = '50%';
    element.style.backgroundColor = markerColor;
    element.style.border = '2px solid white';
    element.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
    element.style.display = 'flex';
    element.style.alignItems = 'center';
    element.style.justifyContent = 'center';
    element.style.cursor = 'pointer';
    element.style.transition = 'transform 0.2s';
    element.title = `${typeInfo?.name || event.event_type} - ${event.device_name || `Device ${event.device_id}`}`;

    // Add hover effect
    element.addEventListener('mouseenter', () => {
      element.style.transform = 'scale(1.2)';
    });
    element.addEventListener('mouseleave', () => {
      element.style.transform = 'scale(1)';
    });

    // Add click handler
    element.addEventListener('click', () => {
      handleEventClick(event);
    });

    return element;
  };

  // Create popup content
  const createPopupContent = (event: Event) => {
    const typeInfo = eventTypeInfo[event.event_type];
    const popupElement = document.createElement('div');
    popupElement.style.padding = '8px';
    popupElement.style.minWidth = '200px';

    popupElement.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <div style="color: ${getMarkerColor(event.event_type)};">
          ${typeInfo?.name || event.event_type}
        </div>
        <span style="background: ${getMarkerColor(event.event_type)}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px;">
          ${typeInfo?.severity || 'unknown'}
        </span>
      </div>
      <div style="margin-bottom: 4px;">
        <strong>Device:</strong> ${event.device_name || `ID: ${event.device_id}`}
      </div>
      <div style="margin-bottom: 4px;">
        <strong>Time:</strong> ${formatEventTime(event.event_time)}
      </div>
      <div style="margin-bottom: 4px;">
        <strong>Location:</strong> ${event.position_data?.latitude.toFixed(6)}, ${event.position_data?.longitude.toFixed(6)}
      </div>
      ${event.position_data?.speed ? `<div><strong>Speed:</strong> ${event.position_data.speed} km/h</div>` : ''}
    `;

    return popupElement;
  };

  // Update markers when events or map changes
  useEffect(() => {
    if (!map) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    popupsRef.current.forEach(popup => popup.remove());
    markersRef.current = [];
    popupsRef.current = [];

    // Add new markers
    eventsWithPosition.forEach((event) => {
      if (!event.position_data) return;

      const markerElement = createMarkerElement(event);
      const marker = new maplibregl.Marker(markerElement)
        .setLngLat([event.position_data.longitude, event.position_data.latitude])
        .addTo(map);

      markersRef.current.push(marker);

      // Add popup if enabled
      if (showPopup) {
        const popupContent = createPopupContent(event);
        const popup = new maplibregl.Popup({
          closeButton: false,
          closeOnClick: false,
        })
          .setDOMContent(popupContent)
          .setLngLat([event.position_data.longitude, event.position_data.latitude]);

        marker.setPopup(popup);
        popupsRef.current.push(popup);
      }
    });

    // Cleanup function
    return () => {
      markersRef.current.forEach(marker => marker.remove());
      popupsRef.current.forEach(popup => popup.remove());
      markersRef.current = [];
      popupsRef.current = [];
    };
  }, [map, eventsWithPosition, showPopup, eventTypeInfo, handleEventClick]);

  // This component doesn't render anything directly
  return null;
};

export default EventMarkers;