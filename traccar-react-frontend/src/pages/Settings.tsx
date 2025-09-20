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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
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
  Language as LanguageIcon,
  Palette as PaletteIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from '../hooks/useTranslation';

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
  const { t, changeLanguage, getCurrentLanguage, getAvailableLanguages } = useTranslation();
  const [activeTab, setActiveTab] = useState(0);
  const [darkMode, setDarkMode] = useState(false);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const serverSettingsItems = [
    {
      title: t('settings.serverConfiguration'),
      description: t('settings.serverConfigurationDescription'),
      icon: <SettingsIcon />,
      path: '/settings/server',
      adminOnly: true,
    },
    {
      title: t('settings.securitySettings'),
      description: t('settings.securitySettingsDescription'),
      icon: <SecurityIcon />,
      path: '/settings/security',
      adminOnly: true,
    },
    {
      title: t('settings.notificationSettings'),
      description: t('settings.notificationSettingsDescription'),
      icon: <NotificationsIcon />,
      path: '/settings/notifications',
      adminOnly: true,
    },
    {
      title: t('settings.systemInformation'),
      description: t('settings.systemInformationDescription'),
      icon: <InfoIcon />,
      path: '/settings/system',
      adminOnly: true,
    },
  ];

  const userSettingsItems = [
    {
      title: t('settings.userManagementTitle'),
      description: t('settings.userManagementDescription'),
      icon: <PersonIcon />,
      path: '/users',
      adminOnly: true,
    },
    {
      title: t('settings.deviceManagement'),
      description: t('settings.deviceManagementDescription'),
      icon: <DevicesIcon />,
      path: '/devices',
      adminOnly: false,
    },
    {
      title: t('settings.groupManagement'),
      description: t('settings.groupManagementDescription'),
      icon: <GroupIcon />,
      path: '/groups',
      adminOnly: false,
    },
    {
      title: t('settings.commandTemplates'),
      description: t('settings.commandTemplatesDescription'),
      icon: <AssignmentIcon />,
      path: '/settings/commands',
      adminOnly: true,
    },
  ];

  const personalSettingsItems = [
    {
      title: t('settings.language'),
      description: t('settings.languageDescription'),
      icon: <LanguageIcon />,
      type: 'language',
    },
    {
      title: t('settings.theme'),
      description: t('settings.themeDescription'),
      icon: <PaletteIcon />,
      type: 'theme',
    },
    {
      title: t('settings.notifications'),
      description: t('settings.notificationsDescription'),
      icon: <NotificationsIcon />,
      type: 'notifications',
    },
  ];

  const filteredServerSettings = serverSettingsItems.filter(item => 
    !item.adminOnly || user?.is_admin
  );

  const filteredUserSettings = userSettingsItems.filter(item => 
    !item.adminOnly || user?.is_admin
  );

  const handleLanguageChange = (event: any) => {
    changeLanguage(event.target.value);
  };

  const handleThemeChange = (event: any) => {
    setDarkMode(event.target.checked);
    // TODO: Implement theme change logic
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        {t('settings.title')}
      </Typography>

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="settings tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<SettingsIcon />} label={t('settings.serverSettings')} />
          <Tab icon={<PersonIcon />} label={t('settings.userManagement')} />
          <Tab icon={<PersonIcon />} label="Personal" />
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

        {/* Personal Settings Tab */}
        <TabPanel value={activeTab} index={2}>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
            {personalSettingsItems.map((item, index) => (
              <Card key={index}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ mr: 2, color: 'primary.main' }}>
                      {item.icon}
                    </Box>
                    <Typography variant="h6" component="h2">
                      {item.title}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {item.description}
                  </Typography>
                  
                  {item.type === 'language' && (
                    <FormControl fullWidth>
                      <InputLabel>{t('settings.language')}</InputLabel>
                      <Select
                        value={getCurrentLanguage()}
                        onChange={handleLanguageChange}
                        label={t('settings.language')}
                      >
                        {getAvailableLanguages().map((lang) => (
                          <MenuItem key={lang.code} value={lang.code}>
                            {lang.nativeName}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                  
                  {item.type === 'theme' && (
                    <FormControlLabel
                      control={
                        <Switch
                          checked={darkMode}
                          onChange={handleThemeChange}
                        />
                      }
                      label={darkMode ? 'Dark Mode' : 'Light Mode'}
                    />
                  )}
                  
                  {item.type === 'notifications' && (
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Enable Notifications"
                    />
                  )}
                </CardContent>
              </Card>
            ))}
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Settings;
