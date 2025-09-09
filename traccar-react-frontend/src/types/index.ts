export interface Position {
  id: number;
  deviceId: number;
  latitude: number;
  longitude: number;
  course?: number;
  speed?: number;
  fixTime?: string;
  serverTime?: string;
  deviceTime?: string;
  altitude?: number;
  valid?: boolean;
  address?: string;
  accuracy?: number;
  attributes?: Record<string, any>;
}

export interface Device {
  id: number;
  name: string;
  status: string;
  category?: string;
  lastUpdate?: string;
  attributes?: Record<string, any>;
}

export interface User {
  id: number;
  name: string;
  email: string;
  admin?: boolean;
  disabled?: boolean;
  attributes?: Record<string, any>;
}

export interface Group {
  id: number;
  name: string;
  description?: string;
  attributes?: Record<string, any>;
}

export interface Person {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  attributes?: Record<string, any>;
}

export interface UnknownDevice {
  id: number;
  name: string;
  uniqueId: string;
  lastUpdate?: string;
  attributes?: Record<string, any>;
}

// Command System Types
export type CommandType = 
  | 'REBOOT' | 'SETTIME' | 'SETINTERVAL' | 'SETOVERSPEED' | 'SETGEOFENCE'
  | 'SETOUTPUT' | 'SETINPUT' | 'SETACCELERATION' | 'SETDECELERATION' | 'SETTURN'
  | 'SETIDLE' | 'SETPARKING' | 'SETMOVEMENT' | 'SETVIBRATION' | 'SETDOOR' | 'SETPOWER'
  | 'SET_INTERVAL' | 'SET_ACCURACY' | 'SET_BATTERY_SAVER' | 'SET_ALARM'
  | 'SET_GEOFENCE' | 'SET_SPEED_LIMIT' | 'SET_ENGINE_STOP' | 'SET_ENGINE_START'
  | 'CUSTOM' | 'PING' | 'STATUS' | 'CONFIG';

export type CommandStatus = 
  | 'PENDING' | 'SENT' | 'DELIVERED' | 'EXECUTED' | 'FAILED' 
  | 'TIMEOUT' | 'CANCELLED' | 'EXPIRED';

export type CommandPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'CRITICAL';

export interface Command {
  id: number;
  device_id: number;
  user_id: number;
  command_type: CommandType;
  priority: CommandPriority;
  status: CommandStatus;
  parameters?: Record<string, any>;
  raw_command?: string;
  sent_at?: string;
  delivered_at?: string;
  executed_at?: string;
  failed_at?: string;
  response?: string;
  error_message?: string;
  retry_count: number;
  max_retries: number;
  expires_at?: string;
  created_at: string;
  updated_at: string;
  device?: Device;
  user?: User;
}

export interface CommandCreate {
  device_id: number;
  command_type: CommandType;
  priority?: CommandPriority;
  parameters?: Record<string, any>;
  raw_command?: string;
  max_retries?: number;
  expires_at?: string;
}

export interface CommandBulkCreate {
  device_ids: number[];
  command_type: CommandType;
  priority?: CommandPriority;
  parameters?: Record<string, any>;
  raw_command?: string;
  max_retries?: number;
  expires_at?: string;
}

export interface CommandStats {
  total_commands: number;
  commands_by_status: Record<CommandStatus, number>;
  commands_by_priority: Record<CommandPriority, number>;
  commands_by_type: Record<CommandType, number>;
  success_rate: number;
  average_execution_time: number;
}

export interface CommandQueue {
  id: number;
  command_id: number;
  priority: CommandPriority;
  scheduled_at: string;
  queued_at: string;
  attempts: number;
  last_attempt_at?: string;
  next_attempt_at?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  command?: Command;
}

// Re-export geofence types
export * from './geofences';
