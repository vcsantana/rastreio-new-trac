export interface Device {
  id: number;
  name: string;
  unique_id: string;
  status: 'online' | 'offline' | 'unknown';
  category: string;
  last_update: string;
  group_id: number | null;
  disabled: boolean;
  protocol?: string;
  attributes?: Record<string, any>;
}
