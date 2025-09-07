import React, { useState } from 'react';
import {
  Box,
  FormControl,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  InputLabel,
  TextField,
  Button,
  Paper,
  Typography,
  Stack
} from '@mui/material';

interface RouteControlsProps {
  showRoutes: boolean;
  onShowRoutesChange: (show: boolean) => void;
  showSpeedColors: boolean;
  onShowSpeedColorsChange: (show: boolean) => void;
  routeColor: string;
  onRouteColorChange: (color: string) => void;
  routeWidth: number;
  onRouteWidthChange: (width: number) => void;
  routeOpacity: number;
  onRouteOpacityChange: (opacity: number) => void;
  fromTime: Date | null;
  onFromTimeChange: (date: Date | null) => void;
  toTime: Date | null;
  onToTimeChange: (date: Date | null) => void;
  onApplyFilters: () => void;
  onClearFilters: () => void;
}

const RouteControls: React.FC<RouteControlsProps> = ({
  showRoutes,
  onShowRoutesChange,
  showSpeedColors,
  onShowSpeedColorsChange,
  routeColor,
  onRouteColorChange,
  routeWidth,
  onRouteWidthChange,
  routeOpacity,
  onRouteOpacityChange,
  fromTime,
  onFromTimeChange,
  toTime,
  onToTimeChange,
  onApplyFilters,
  onClearFilters
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const predefinedColors = [
    { name: 'Azul', value: '#3b82f6' },
    { name: 'Verde', value: '#10b981' },
    { name: 'Vermelho', value: '#ef4444' },
    { name: 'Amarelo', value: '#f59e0b' },
    { name: 'Roxo', value: '#8b5cf6' },
    { name: 'Rosa', value: '#ec4899' }
  ];

  return (
    <Paper 
      sx={{ 
        position: 'absolute', 
        top: 10, 
        right: 10, 
        p: 2, 
        minWidth: 300,
        zIndex: 1000,
        maxHeight: '80vh',
        overflow: 'auto'
      }}
    >
      <Stack spacing={2}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Controles de Rota</Typography>
          <Button
            size="small"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Recolher' : 'Expandir'}
          </Button>
        </Box>

        <FormControlLabel
          control={
            <Switch
              checked={showRoutes}
              onChange={(e) => onShowRoutesChange(e.target.checked)}
            />
          }
          label="Mostrar Rotas"
        />

        {showRoutes && (
          <>
            <FormControlLabel
              control={
                <Switch
                  checked={showSpeedColors}
                  onChange={(e) => onShowSpeedColorsChange(e.target.checked)}
                  disabled={!showRoutes}
                />
              }
              label="Cores por Velocidade"
            />

            {!showSpeedColors && (
              <FormControl fullWidth>
                <InputLabel>Cor da Rota</InputLabel>
                <Select
                  value={routeColor}
                  onChange={(e) => onRouteColorChange(e.target.value)}
                  label="Cor da Rota"
                >
                  {predefinedColors.map((color) => (
                    <MenuItem key={color.value} value={color.value}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Box
                          width={20}
                          height={20}
                          bgcolor={color.value}
                          borderRadius={1}
                          border="1px solid #ccc"
                        />
                        {color.name}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}

            <TextField
              label="Largura da Linha"
              type="number"
              value={routeWidth}
              onChange={(e) => onRouteWidthChange(Number(e.target.value))}
              inputProps={{ min: 1, max: 10 }}
              fullWidth
            />

            <TextField
              label="Opacidade"
              type="number"
              value={routeOpacity}
              onChange={(e) => onRouteOpacityChange(Number(e.target.value))}
              inputProps={{ min: 0.1, max: 1, step: 0.1 }}
              fullWidth
            />

            {isExpanded && (
              <>
                <Typography variant="subtitle2">Filtros de Tempo</Typography>
                
                <TextField
                  label="Data Inicial"
                  type="datetime-local"
                  value={fromTime ? fromTime.toISOString().slice(0, 16) : ''}
                  onChange={(e) => onFromTimeChange(e.target.value ? new Date(e.target.value) : null)}
                  fullWidth
                />

                <TextField
                  label="Data Final"
                  type="datetime-local"
                  value={toTime ? toTime.toISOString().slice(0, 16) : ''}
                  onChange={(e) => onToTimeChange(e.target.value ? new Date(e.target.value) : null)}
                  fullWidth
                />

                <Box display="flex" gap={1}>
                  <Button
                    variant="contained"
                    onClick={onApplyFilters}
                    fullWidth
                  >
                    Aplicar Filtros
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={onClearFilters}
                    fullWidth
                  >
                    Limpar
                  </Button>
                </Box>
              </>
            )}
          </>
        )}
      </Stack>
    </Paper>
  );
};

export default RouteControls;
