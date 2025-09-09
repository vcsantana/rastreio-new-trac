export interface Event {
  id: number;
  device_id: number;
  device_name?: string;
  event_type: string;
  event_time: string;
  position_id?: number;
  position_data?: {
    latitude: number;
    longitude: number;
    speed: number;
    course: number;
  };
  attributes?: Record<string, any>;
  maintenance_id?: number;
  geofence_id?: number;
  geofence_name?: string;
  created_at: string;
  updated_at: string;
}

export interface EventFilters {
  device_id?: number;
  event_type?: string;
  start_time?: string;
  end_time?: string;
  page?: number;
  size?: number;
}

export interface EventListResponse {
  events: Event[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface EventStats {
  total_events: number;
  events_by_type: Record<string, number>;
  events_by_device: Record<string, number>;
  recent_events: Event[];
  period: string;
}

export interface EventTypeInfo {
  name: string;
  description: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  icon: string;
  color: string;
}

export const EVENT_TYPES = [
  'deviceOnline',
  'deviceOffline',
  'deviceMoving',
  'deviceStopped',
  'deviceOverspeed',
  'deviceFuelDrop',
  'deviceFuelFill',
  'deviceIgnitionOn',
  'deviceIgnitionOff',
  'deviceMaintenance',
  'deviceCommandResult',
  'deviceDriverChanged',
  'geofenceEnter',
  'geofenceExit',
  'alarm',
  'commandResult',
  'deviceUnknown',
  'deviceUpdate',
  'deviceDelete',
  'deviceCreate',
  'userLogin',
  'userLogout',
  'userCreate',
  'userUpdate',
  'userDelete',
  'groupCreate',
  'groupUpdate',
  'groupDelete',
  'driverCreate',
  'driverUpdate',
  'driverDelete',
  'geofenceCreate',
  'geofenceUpdate',
  'geofenceDelete',
  'maintenanceCreate',
  'maintenanceUpdate',
  'maintenanceDelete',
  'calendarCreate',
  'calendarUpdate',
  'calendarDelete',
  'computedAttributeCreate',
  'computedAttributeUpdate',
  'computedAttributeDelete',
  'accumulatorCreate',
  'accumulatorUpdate',
  'accumulatorDelete',
  'connectionOpen',
  'connectionClose',
  'connectionLost',
  'connectionRestored',
  'announcementCreate',
  'announcementUpdate',
  'announcementDelete'
] as const;

export const EVENT_TYPE_INFO: Record<string, EventTypeInfo> = {
  deviceOnline: {
    name: 'Device Online',
    description: 'Device came online',
    category: 'device',
    severity: 'low',
    icon: 'online',
    color: '#4caf50'
  },
  deviceOffline: {
    name: 'Device Offline',
    description: 'Device went offline',
    category: 'device',
    severity: 'medium',
    icon: 'offline',
    color: '#f44336'
  },
  deviceMoving: {
    name: 'Device Moving',
    description: 'Device started moving',
    category: 'motion',
    severity: 'low',
    icon: 'moving',
    color: '#2196f3'
  },
  deviceStopped: {
    name: 'Device Stopped',
    description: 'Device stopped moving',
    category: 'motion',
    severity: 'low',
    icon: 'stopped',
    color: '#ff9800'
  },
  deviceOverspeed: {
    name: 'Overspeed',
    description: 'Device exceeded speed limit',
    category: 'alarm',
    severity: 'high',
    icon: 'speed',
    color: '#f44336'
  },
  deviceFuelDrop: {
    name: 'Fuel Drop',
    description: 'Significant fuel level drop detected',
    category: 'alarm',
    severity: 'high',
    icon: 'fuel',
    color: '#ff5722'
  },
  deviceFuelFill: {
    name: 'Fuel Fill',
    description: 'Fuel tank was filled',
    category: 'fuel',
    severity: 'low',
    icon: 'fuel',
    color: '#4caf50'
  },
  deviceIgnitionOn: {
    name: 'Ignition On',
    description: 'Vehicle ignition turned on',
    category: 'ignition',
    severity: 'low',
    icon: 'ignition',
    color: '#4caf50'
  },
  deviceIgnitionOff: {
    name: 'Ignition Off',
    description: 'Vehicle ignition turned off',
    category: 'ignition',
    severity: 'low',
    icon: 'ignition',
    color: '#ff9800'
  },
  deviceMaintenance: {
    name: 'Maintenance',
    description: 'Maintenance event',
    category: 'maintenance',
    severity: 'medium',
    icon: 'maintenance',
    color: '#ff9800'
  },
  deviceCommandResult: {
    name: 'Command Result',
    description: 'Command execution result',
    category: 'command',
    severity: 'low',
    icon: 'command',
    color: '#2196f3'
  },
  deviceDriverChanged: {
    name: 'Driver Changed',
    description: 'Driver assignment changed',
    category: 'driver',
    severity: 'low',
    icon: 'driver',
    color: '#9c27b0'
  },
  geofenceEnter: {
    name: 'Geofence Enter',
    description: 'Device entered geofence',
    category: 'geofence',
    severity: 'medium',
    icon: 'geofence',
    color: '#4caf50'
  },
  geofenceExit: {
    name: 'Geofence Exit',
    description: 'Device exited geofence',
    category: 'geofence',
    severity: 'medium',
    icon: 'geofence',
    color: '#f44336'
  },
  alarm: {
    name: 'Alarm',
    description: 'General alarm event',
    category: 'alarm',
    severity: 'critical',
    icon: 'alarm',
    color: '#f44336'
  },
  commandResult: {
    name: 'Command Result',
    description: 'Command execution completed',
    category: 'command',
    severity: 'low',
    icon: 'command',
    color: '#2196f3'
  }
};

export interface EventNotification {
  id: string;
  event: Event;
  read: boolean;
  created_at: string;
}

export interface EventReport {
  start_date: string;
  end_date: string;
  device_ids?: number[];
  event_types?: string[];
  total_events: number;
  events_by_type: Record<string, number>;
  events_by_device: Record<string, number>;
  events: Event[];
}
