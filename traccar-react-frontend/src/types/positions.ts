export interface Position {
  id: number;
  deviceId: number;
  latitude: number;
  longitude: number;
  course?: number;
  speed?: number;
  altitude?: number;
  fixTime: string;
  address?: string;
  attributes?: Record<string, any>;
}
