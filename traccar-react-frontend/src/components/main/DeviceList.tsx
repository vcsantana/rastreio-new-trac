import React, { useEffect, useState } from 'react';
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { Paper, Box } from '@mui/material';
import { useDevices } from '../../hooks/useDevices';
import { usePositions } from '../../hooks/usePositions';
import DeviceRow from './DeviceRow';

interface DeviceListProps {
  devices: any[];
  selectedDeviceId?: number;
  onDeviceSelect?: (deviceId: number) => void;
  style?: React.CSSProperties;
}

const DeviceList: React.FC<DeviceListProps> = ({
  devices,
  selectedDeviceId,
  onDeviceSelect,
  style,
}) => {
  const { positions } = usePositions();
  const [, setTime] = useState(Date.now());

  // Update time every minute for relative time display
  useEffect(() => {
    const interval = setInterval(() => setTime(Date.now()), 60000);
    return () => clearInterval(interval);
  }, []);

  const getPositionForDevice = (deviceId: number) => {
    return positions.find(pos => pos.deviceId === deviceId);
  };

  const Row = ({ index, style: rowStyle }: { index: number; style: React.CSSProperties }) => {
    const device = devices[index];
    const position = getPositionForDevice(device.id);

    return (
      <DeviceRow
        device={device}
        index={index}
        data={devices}
        style={rowStyle}
        position={position}
        selected={selectedDeviceId === device.id}
        onSelect={onDeviceSelect}
      />
    );
  };

  if (devices.length === 0) {
    return (
      <Paper 
        sx={{ 
          height: '100%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          p: 2,
        }}
      >
        <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
          No devices found
        </Box>
      </Paper>
    );
  }

  return (
    <Paper 
      sx={{ 
        height: '100%', 
        overflow: 'hidden',
        ...style,
      }}
    >
      <AutoSizer>
        {({ height, width }) => (
          <List
            height={height}
            width={width}
            itemCount={devices.length}
            itemSize={72}
            overscanCount={10}
          >
            {Row}
          </List>
        )}
      </AutoSizer>
    </Paper>
  );
};

export default DeviceList;
