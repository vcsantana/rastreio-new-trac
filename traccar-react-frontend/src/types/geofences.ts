/**
 * Geofence types for the React frontend
 * Based on the Python API schemas
 */

export interface Geofence {
  id: number;
  name: string;
  description?: string;
  geometry: string; // GeoJSON string
  type: 'polygon' | 'circle' | 'polyline';
  area?: number; // Calculated area in square meters
  disabled: boolean;
  calendar_id?: number;
  attributes?: string; // JSON string
  created_at: string;
  updated_at?: string;
  
  // Parsed geometry for easier frontend consumption
  geometry_data?: GeoJSONGeometry;
  geometry_type?: string;
  coordinates?: any[];
}

export interface GeofenceCreate {
  name: string;
  description?: string;
  geometry: string;
  type: 'polygon' | 'circle' | 'polyline';
  disabled?: boolean;
  calendar_id?: number;
  attributes?: string;
}

export interface GeofenceUpdate {
  name?: string;
  description?: string;
  geometry?: string;
  type?: 'polygon' | 'circle' | 'polyline';
  disabled?: boolean;
  calendar_id?: number;
  attributes?: string;
}

export interface GeofenceListResponse {
  geofences: Geofence[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface GeofenceStats {
  total_geofences: number;
  active_geofences: number;
  disabled_geofences: number;
  geofences_by_type: Record<string, number>;
  total_area: number;
}

export interface GeofenceTestRequest {
  latitude: number;
  longitude: number;
}

export interface GeofenceTestResponse {
  geofence_id: number;
  geofence_name: string;
  is_inside: boolean;
  distance?: number; // Distance to geofence boundary in meters
}

export interface GeofenceEvent {
  id: number;
  device_id: number;
  geofence_id: number;
  event_type: 'geofenceEnter' | 'geofenceExit';
  event_time: string;
  device?: {
    id: number;
    name: string;
  };
  geofence?: {
    id: number;
    name: string;
  };
}

export interface GeofenceEventStats {
  total_events: number;
  events_by_type: Record<string, number>;
  events_by_geofence: Record<string, number>;
  events_by_device: Record<string, number>;
  recent_events: GeofenceEvent[];
}

// GeoJSON types for geometry handling
export interface GeoJSONGeometry {
  type: 'Polygon' | 'Circle' | 'LineString' | 'Point';
  coordinates: any;
}

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: number[][][]; // Array of linear rings
}

export interface GeoJSONCircle {
  type: 'Circle';
  coordinates: [number, number, number]; // [longitude, latitude, radius_meters]
}

export interface GeoJSONLineString {
  type: 'LineString';
  coordinates: number[][]; // Array of [longitude, latitude] pairs
}

// Filter and search types
export interface GeofenceFilters {
  disabled?: boolean;
  type?: string;
  search?: string;
  page?: number;
  size?: number;
}

export interface GeofenceEventFilters {
  device_id?: number;
  geofence_id?: number;
  event_type?: string;
  limit?: number;
}

// Map integration types
export interface GeofenceMapLayer {
  id: number;
  name: string;
  type: string;
  geometry: GeoJSONGeometry;
  style: {
    fillColor?: string;
    strokeColor?: string;
    strokeWidth?: number;
    fillOpacity?: number;
    strokeOpacity?: number;
  };
  popup?: {
    title: string;
    content: string;
  };
}

// Editor types
export interface GeofenceEditorState {
  mode: 'create' | 'edit' | 'view';
  geofence?: Geofence;
  geometry?: GeoJSONGeometry;
  isDirty: boolean;
  isValid: boolean;
  errors: Record<string, string>;
}

export interface GeofenceDrawingMode {
  type: 'polygon' | 'circle' | 'polyline' | 'none';
  isActive: boolean;
  coordinates: number[][];
}

// Example geometries for reference
export const EXAMPLE_GEOMETRIES = {
  polygon: {
    type: 'Polygon' as const,
    coordinates: [[
      [-46.6333, -23.5505],
      [-46.6300, -23.5505],
      [-46.6300, -23.5480],
      [-46.6333, -23.5480],
      [-46.6333, -23.5505]
    ]]
  },
  circle: {
    type: 'Circle' as const,
    coordinates: [-46.6333, -23.5505, 1000] // [lon, lat, radius_meters]
  },
  polyline: {
    type: 'LineString' as const,
    coordinates: [
      [-46.6333, -23.5505],
      [-46.6300, -23.5480],
      [-46.6250, -23.5450]
    ]
  }
};
