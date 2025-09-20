import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Toolbar,
  IconButton,
  OutlinedInput,
  InputAdornment,
  Popover,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Badge,
  ListItemButton,
  ListItemText,
  Tooltip,
} from '@mui/material';
import {
  Map as MapIcon,
  ViewList as ViewListIcon,
  Add as AddIcon,
  Tune as TuneIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useDevices } from '../../hooks/useDevices';
import { useGroups } from '../../hooks/useGroups';
import { useTranslation } from '../../hooks/useTranslation';
import DeviceRow from './DeviceRow';

interface MainToolbarProps {
  filteredDevices: any[];
  devicesOpen: boolean;
  setDevicesOpen: (open: boolean) => void;
  keyword: string;
  setKeyword: (keyword: string) => void;
  filter: {
    statuses: string[];
    groups: number[];
  };
  setFilter: (filter: any) => void;
  filterSort: string;
  setFilterSort: (sort: string) => void;
  filterMap: boolean;
  setFilterMap: (filter: boolean) => void;
}

const MainToolbar: React.FC<MainToolbarProps> = ({
  filteredDevices,
  devicesOpen,
  setDevicesOpen,
  keyword,
  setKeyword,
  filter,
  setFilter,
  filterSort,
  setFilterSort,
  filterMap,
  setFilterMap,
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { devices } = useDevices();
  const { groups } = useGroups();
  const { t } = useTranslation();

  const toolbarRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [filterAnchorEl, setFilterAnchorEl] = useState<HTMLElement | null>(null);
  const [devicesAnchorEl, setDevicesAnchorEl] = useState<HTMLElement | null>(null);

  const deviceStatusCount = (status: string) => 
    devices.filter((d) => d.status === status).length;

  const handleFilterChange = (field: string, value: any) => {
    setFilter({ ...filter, [field]: value });
  };

  return (
    <Toolbar 
      ref={toolbarRef}
      sx={{ 
        display: 'flex',
        gap: 1,
        minHeight: '48px !important',
        px: 1,
      }}
    >
      <IconButton 
        edge="start" 
        onClick={() => setDevicesOpen(!devicesOpen)}
        size="small"
      >
        {devicesOpen ? <MapIcon /> : <ViewListIcon />}
      </IconButton>
      
      <OutlinedInput
        ref={inputRef}
        placeholder={t('menu.searchDevices')}
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        onFocus={() => setDevicesAnchorEl(toolbarRef.current)}
        onBlur={() => setDevicesAnchorEl(null)}
        endAdornment={
          <InputAdornment position="end">
            <IconButton 
              size="small" 
              edge="end" 
              onClick={(e) => setFilterAnchorEl(inputRef.current)}
            >
              <Badge 
                color="info" 
                variant="dot" 
                invisible={!filter.statuses.length && !filter.groups.length}
              >
                <TuneIcon fontSize="small" />
              </Badge>
            </IconButton>
          </InputAdornment>
        }
        size="small"
        fullWidth
      />

      {/* Devices Popover */}
      <Popover
        open={!!devicesAnchorEl && !devicesOpen}
        anchorEl={devicesAnchorEl}
        onClose={() => setDevicesAnchorEl(null)}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        marginThreshold={0}
        PaperProps={{
          style: { 
            width: toolbarRef.current ? 
              `calc(${toolbarRef.current.clientWidth}px - ${theme.spacing(4)})` : 
              '300px' 
          },
        }}
        elevation={1}
        disableAutoFocus
        disableEnforceFocus
      >
        {filteredDevices.slice(0, 3).map((device, index) => (
          <DeviceRow 
            key={device.id} 
            device={device} 
            index={index}
            data={filteredDevices}
          />
        ))}
        {filteredDevices.length > 3 && (
          <ListItemButton 
            alignItems="center" 
            onClick={() => setDevicesOpen(true)}
          >
            <ListItemText
              primary={t('menu.showAllDevices')}
              style={{ textAlign: 'center' }}
            />
          </ListItemButton>
        )}
      </Popover>

      {/* Filter Popover */}
      <Popover
        open={!!filterAnchorEl}
        anchorEl={filterAnchorEl}
        onClose={() => setFilterAnchorEl(null)}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
      >
        <div style={{ 
          display: 'flex',
          flexDirection: 'column',
          padding: theme.spacing(2),
          gap: theme.spacing(2),
          width: 300,
        }}>
          <FormControl size="small">
            <InputLabel>{t('menu.deviceStatus')}</InputLabel>
            <Select
              label={t('menu.deviceStatus')}
              value={filter.statuses}
              onChange={(e) => handleFilterChange('statuses', e.target.value)}
              multiple
            >
              <MenuItem value="online">
                {t('menu.online')} ({deviceStatusCount('online')})
              </MenuItem>
              <MenuItem value="offline">
                {t('menu.offline')} ({deviceStatusCount('offline')})
              </MenuItem>
              <MenuItem value="unknown">
                {t('menu.unknown')} ({deviceStatusCount('unknown')})
              </MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small">
            <InputLabel>{t('menu.groups')}</InputLabel>
            <Select
              label={t('menu.groups')}
              value={filter.groups}
              onChange={(e) => handleFilterChange('groups', e.target.value)}
              multiple
            >
              {groups.map((group) => (
                <MenuItem key={group.id} value={group.id}>
                  {group.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small">
            <InputLabel>{t('menu.sortBy')}</InputLabel>
            <Select
              label={t('menu.sortBy')}
              value={filterSort}
              onChange={(e) => setFilterSort(e.target.value)}
              displayEmpty
            >
              <MenuItem value="">{t('menu.none')}</MenuItem>
              <MenuItem value="name">{t('menu.name')}</MenuItem>
              <MenuItem value="lastUpdate">{t('menu.lastUpdate')}</MenuItem>
            </Select>
          </FormControl>

          <FormGroup>
            <FormControlLabel
              control={
                <Checkbox 
                  checked={filterMap} 
                  onChange={(e) => setFilterMap(e.target.checked)} 
                />
              }
              label={t('menu.filterMap')}
            />
          </FormGroup>
        </div>
      </Popover>

      <IconButton 
        edge="end" 
        onClick={() => navigate('/devices')}
        size="small"
      >
        <Tooltip title={t('menu.addDevice')}>
          <AddIcon />
        </Tooltip>
      </IconButton>
    </Toolbar>
  );
};

export default MainToolbar;
