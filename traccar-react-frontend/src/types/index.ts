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
