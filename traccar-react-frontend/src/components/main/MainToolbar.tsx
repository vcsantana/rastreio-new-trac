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
        placeholder="Search devices..."
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
              primary="Show all devices"
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
            <InputLabel>Device Status</InputLabel>
            <Select
              label="Device Status"
              value={filter.statuses}
              onChange={(e) => handleFilterChange('statuses', e.target.value)}
              multiple
            >
              <MenuItem value="online">
                Online ({deviceStatusCount('online')})
              </MenuItem>
              <MenuItem value="offline">
                Offline ({deviceStatusCount('offline')})
              </MenuItem>
              <MenuItem value="unknown">
                Unknown ({deviceStatusCount('unknown')})
              </MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small">
            <InputLabel>Groups</InputLabel>
            <Select
              label="Groups"
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
            <InputLabel>Sort By</InputLabel>
            <Select
              label="Sort By"
              value={filterSort}
              onChange={(e) => setFilterSort(e.target.value)}
              displayEmpty
            >
              <MenuItem value="">None</MenuItem>
              <MenuItem value="name">Name</MenuItem>
              <MenuItem value="lastUpdate">Last Update</MenuItem>
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
              label="Filter Map"
            />
          </FormGroup>
        </div>
      </Popover>

      <IconButton 
        edge="end" 
        onClick={() => navigate('/devices')}
        size="small"
      >
        <Tooltip title="Add Device">
          <AddIcon />
        </Tooltip>
      </IconButton>
    </Toolbar>
  );
};

export default MainToolbar;
