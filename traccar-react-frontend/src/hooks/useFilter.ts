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
  setFilteredDevices: (devices: Device[]) => void;
  setFilteredPositions: (positions: Position[]) => void;
}

export const useFilter = ({
  keyword,
  filter,
  filterSort,
  filterMap,
  positions,
  setFilteredDevices,
  setFilteredPositions,
}: UseFilterProps) => {
  const [devices, setDevices] = useState<Device[]>([]);

  // Fetch devices (this would normally come from a hook)
  useEffect(() => {
    // This is a placeholder - in real implementation, this would come from useDevices hook
    // For now, we'll use the positions to create device data
    const deviceMap = new Map<number, Device>();
    
    positions.forEach(position => {
      const deviceId = position.deviceId || position.device_id || position.unknown_device_id;
      if (deviceId && !deviceMap.has(deviceId)) {
        deviceMap.set(deviceId, {
          id: deviceId,
          name: `Device ${deviceId}`,
          unique_id: `device_${deviceId}`,
          status: 'online',
          category: 'default',
          last_update: position.server_time || position.device_time || position.fix_time,
          group_id: null,
          disabled: false,
        });
      }
    });

    setDevices(Array.from(deviceMap.values()));
  }, [positions]);

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
      const deviceId = position.deviceId || position.device_id || position.unknown_device_id;
      return deviceId && deviceIds.has(deviceId);
    });

    setFilteredPositions(filteredPositions);
  }, [devices, keyword, filter, filterSort, positions, setFilteredDevices, setFilteredPositions]);

  return {
    devices,
    filteredDevices: devices, // This will be updated by the effect above
  };
};
