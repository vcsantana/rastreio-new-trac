import React from 'react';
import { Box, Chip, Tooltip, IconButton } from '@mui/material';
import { Wifi, WifiOff, Refresh } from '@mui/icons-material';
import { useWebSocket } from '../../hooks/useWebSocket';

export const WebSocketStatus: React.FC = () => {
  const { connected, connectionError, sendMessage } = useWebSocket();

  const handleReconnect = () => {
    // Send a test message to trigger reconnection
    sendMessage({ type: 'heartbeat' });
  };

  const getStatusColor = () => {
    if (connected) return 'success';
    if (connectionError) return 'error';
    return 'default';
  };

  const getStatusIcon = () => {
    if (connected) return <Wifi />;
    return <WifiOff />;
  };

  const getStatusText = () => {
    if (connected) return 'Connected';
    if (connectionError) return 'Error';
    return 'Disconnected';
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Tooltip title={connectionError || (connected ? 'WebSocket connected' : 'WebSocket disconnected')}>
        <Chip
          icon={getStatusIcon()}
          label={getStatusText()}
          color={getStatusColor() as any}
          size="small"
          variant={connected ? 'filled' : 'outlined'}
        />
      </Tooltip>
      
      {!connected && (
        <Tooltip title="Reconnect">
          <IconButton size="small" onClick={handleReconnect}>
            <Refresh />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );
};
