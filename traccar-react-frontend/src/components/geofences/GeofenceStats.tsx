/**
 * Geofence Statistics Component
 * Displays statistics and metrics for geofences
 */

import React from 'react';
import {
  Card,
  CardContent,
  Grid,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Avatar,
  CircularProgress
} from '@mui/material';
import {
  Map as MapIcon,
  CheckCircle as ActiveIcon,
  Cancel as DisabledIcon,
  Circle as CircleIcon,
  Square as SquareIcon,
  Timeline as TimelineIcon,
  AreaChart as AreaIcon
} from '@mui/icons-material';
import { GeofenceStats as GeofenceStatsType } from '../../types/geofences';

interface GeofenceStatsProps {
  stats: GeofenceStatsType;
  loading?: boolean;
}

const GeofenceStats: React.FC<GeofenceStatsProps> = ({ stats, loading = false }) => {
  const formatArea = (area: number) => {
    if (area < 1000) {
      return `${area.toFixed(0)} m²`;
    } else if (area < 1000000) {
      return `${(area / 1000).toFixed(1)} km²`;
    } else {
      return `${(area / 1000000).toFixed(2)} km²`;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'circle':
        return <CircleIcon />;
      case 'polygon':
        return <SquareIcon />;
      case 'polyline':
        return <TimelineIcon />;
      default:
        return <MapIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'circle':
        return 'primary';
      case 'polygon':
        return 'secondary';
      case 'polyline':
        return 'success';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  const activePercentage = stats.total_geofences > 0 
    ? (stats.active_geofences / stats.total_geofences) * 100 
    : 0;

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Geofence Statistics
        </Typography>
        
        <Grid container spacing={3}>
          {/* Total Geofences */}
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'primary.main', mx: 'auto', mb: 1 }}>
                <MapIcon />
              </Avatar>
              <Typography variant="h4" fontWeight="bold" color="primary">
                {stats.total_geofences}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Geofences
              </Typography>
            </Box>
          </Grid>

          {/* Active Geofences */}
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'success.main', mx: 'auto', mb: 1 }}>
                <ActiveIcon />
              </Avatar>
              <Typography variant="h4" fontWeight="bold" color="success.main">
                {stats.active_geofences}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active
              </Typography>
              <Box sx={{ mt: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={activePercentage}
                  color="success"
                  sx={{ height: 4, borderRadius: 2 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {activePercentage.toFixed(1)}% active
                </Typography>
              </Box>
            </Box>
          </Grid>

          {/* Disabled Geofences */}
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'error.main', mx: 'auto', mb: 1 }}>
                <DisabledIcon />
              </Avatar>
              <Typography variant="h4" fontWeight="bold" color="error.main">
                {stats.disabled_geofences}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Disabled
              </Typography>
            </Box>
          </Grid>

          {/* Total Area */}
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ bgcolor: 'info.main', mx: 'auto', mb: 1 }}>
                <AreaIcon />
              </Avatar>
              <Typography variant="h4" fontWeight="bold" color="info.main">
                {formatArea(stats.total_area)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Area
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Geofences by Type */}
        {Object.keys(stats.geofences_by_type).length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Geofences by Type
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Object.entries(stats.geofences_by_type).map(([type, count]) => (
                <Chip
                  key={type}
                  icon={getTypeIcon(type)}
                  label={`${type}: ${count}`}
                  color={getTypeColor(type) as any}
                  variant="outlined"
                  size="small"
                />
              ))}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default GeofenceStats;
