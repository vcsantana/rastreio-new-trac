import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardActionArea,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Info as InfoIcon,
  Person as PersonIcon,
  Devices as DevicesIcon,
  Group as GroupIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Settings: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const serverSettingsItems = [
    {
      title: 'Server Configuration',
      description: 'General server settings, map configuration, and system preferences',
      icon: <SettingsIcon />,
      path: '/settings/server',
      adminOnly: true,
    },
    {
      title: 'Security Settings',
      description: 'Access control, permissions, and security policies',
      icon: <SecurityIcon />,
      path: '/settings/security',
      adminOnly: true,
    },
    {
      title: 'Notification Settings',
      description: 'Email, SMS, and webhook notification configurations',
      icon: <NotificationsIcon />,
      path: '/settings/notifications',
      adminOnly: true,
    },
    {
      title: 'System Information',
      description: 'Server health, statistics, and system monitoring',
      icon: <InfoIcon />,
      path: '/settings/system',
      adminOnly: true,
    },
  ];

  const userSettingsItems = [
    {
      title: 'User Management',
      description: 'Manage users, roles, and permissions',
      icon: <PersonIcon />,
      path: '/users',
      adminOnly: true,
    },
    {
      title: 'Device Management',
      description: 'Configure devices, protocols, and device settings',
      icon: <DevicesIcon />,
      path: '/devices',
      adminOnly: false,
    },
    {
      title: 'Group Management',
      description: 'Organize devices and users into groups',
      icon: <GroupIcon />,
      path: '/groups',
      adminOnly: false,
    },
    {
      title: 'Command Templates',
      description: 'Create and manage command templates',
      icon: <AssignmentIcon />,
      path: '/settings/commands',
      adminOnly: true,
    },
  ];

  const filteredServerSettings = serverSettingsItems.filter(item => 
    !item.adminOnly || user?.is_admin
  );

  const filteredUserSettings = userSettingsItems.filter(item => 
    !item.adminOnly || user?.is_admin
  );

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="settings tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<SettingsIcon />} label="Server Settings" />
          <Tab icon={<PersonIcon />} label="User Management" />
        </Tabs>

        {/* Server Settings Tab */}
        <TabPanel value={activeTab} index={0}>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
            {filteredServerSettings.map((item, index) => (
              <Card key={index}>
                <CardActionArea onClick={() => handleNavigation(item.path)}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Box sx={{ mr: 2, color: 'primary.main' }}>
                        {item.icon}
                      </Box>
                      <Typography variant="h6" component="h2">
                        {item.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {item.description}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            ))}
          </Box>
        </TabPanel>

        {/* User Management Tab */}
        <TabPanel value={activeTab} index={1}>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
            {filteredUserSettings.map((item, index) => (
              <Card key={index}>
                <CardActionArea onClick={() => handleNavigation(item.path)}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Box sx={{ mr: 2, color: 'primary.main' }}>
                        {item.icon}
                      </Box>
                      <Typography variant="h6" component="h2">
                        {item.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {item.description}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            ))}
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Settings;
