import { useEffect, useState } from 'react';
import { Device } from '../types/devices';
import { Position } from '../types/positions';

interface FilterState {
  statuses: string[];
  groups: number[];
}

interface UseFilterProps {
  keyword: string;
  filter: FilterState;
  filterSort: string;
  filterMap: boolean;
  positions: Position[];
  devices?: Device[]; // Add devices as optional prop
  setFilteredDevices: (devices: Device[]) => void;
  setFilteredPositions: (positions: Position[]) => void;
}

export const useFilter = ({
  keyword,
  filter,
  filterSort,
  filterMap,
  positions,
  devices: inputDevices = [],
  setFilteredDevices,
  setFilteredPositions,
}: UseFilterProps) => {
  const [devices, setDevices] = useState<Device[]>([]);

  // Use input devices if provided, otherwise create from positions
  useEffect(() => {
    if (inputDevices && inputDevices.length > 0) {
      // Use the real devices data
      setDevices(inputDevices);
    } else if (positions && positions.length > 0) {
      // Fallback: create device data from positions (for backward compatibility)
      const deviceMap = new Map<number, Device>();
      
      positions.forEach(position => {
        const deviceId = position.deviceId || (position as any).device_id || (position as any).unknown_device_id;
        if (deviceId && !deviceMap.has(deviceId)) {
          deviceMap.set(deviceId, {
            id: deviceId,
            name: `Device ${deviceId}`,
            unique_id: `device_${deviceId}`,
            status: 'online',
            category: 'default',
            last_update: (position as any).server_time || (position as any).device_time || position.fixTime,
            group_id: null,
            disabled: false,
          });
        }
      });

      setDevices(Array.from(deviceMap.values()));
    } else {
      // No devices and no positions, clear devices
      setDevices([]);
    }
  }, [positions, inputDevices]);

  useEffect(() => {
    let filtered = [...devices];

    // Filter by keyword
    if (keyword) {
      const lowerKeyword = keyword.toLowerCase();
      filtered = filtered.filter(device =>
        device.name.toLowerCase().includes(lowerKeyword) ||
        device.unique_id.toLowerCase().includes(lowerKeyword)
      );
    }

    // Filter by status
    if (filter.statuses.length > 0) {
      filtered = filtered.filter(device =>
        filter.statuses.includes(device.status)
      );
    }

    // Filter by groups
    if (filter.groups.length > 0) {
      filtered = filtered.filter(device =>
        device.group_id && filter.groups.includes(device.group_id)
      );
    }

    // Sort
    if (filterSort) {
      filtered.sort((a, b) => {
        switch (filterSort) {
          case 'name':
            return a.name.localeCompare(b.name);
          case 'lastUpdate':
            return new Date(b.last_update).getTime() - new Date(a.last_update).getTime();
          default:
            return 0;
        }
      });
    }

    setFilteredDevices(filtered);

    // Filter positions based on filtered devices
    const deviceIds = new Set(filtered.map(device => device.id));
    const filteredPositions = positions.filter(position => {
      const deviceId = position.deviceId || (position as any).device_id || (position as any).unknown_device_id;
      return deviceId && deviceIds.has(deviceId);
    });

    setFilteredPositions(filteredPositions);
  }, [devices, keyword, filter, filterSort, positions, setFilteredDevices, setFilteredPositions]);

  return {
    devices,
    filteredDevices: devices, // This will be updated by the effect above
  };
};
