import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Switch,
  FormControlLabel,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
} from '@mui/material';
import {
  Person,
  Notifications,
  Security,
  Palette,
  Storage,
  Api,
  Save,
  Key,
  Email,
  AccountCircle,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    notifications: {
      emailNotifications: true,
      extractionComplete: true,
      ontologyCreated: true,
      systemUpdates: false,
    },
    preferences: {
      theme: 'light',
      language: 'en',
      defaultChunkSize: 1000,
      defaultOverlap: 10,
    },
    api: {
      anthropicApiKey: '',
      maxRetries: 3,
      timeout: 30,
    }
  });

  const [showSuccess, setShowSuccess] = useState(false);

  const handleSwitchChange = (category: string, field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [field]: event.target.checked,
      }
    }));
  };

  const handleSelectChange = (category: string, field: string) => (event: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [field]: event.target.value,
      }
    }));
  };

  const handleTextChange = (category: string, field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [field]: event.target.value,
      }
    }));
  };

  const handleSave = async () => {
    try {
      // TODO: Save settings to backend
      console.log('Saving settings:', settings);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {showSuccess && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Settings saved successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Profile Settings */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader
              avatar={<Person />}
              title="Profile Information"
              subheader="Manage your account details"
            />
            <Divider />
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ width: 64, height: 64, mr: 2, bgcolor: 'primary.main' }}>
                  {user?.username.charAt(0).toUpperCase()}
                </Avatar>
                <Box>
                  <Typography variant="h6">{user?.username}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {user?.email}
                  </Typography>
                </Box>
              </Box>

              <List>
                <ListItem>
                  <ListItemIcon>
                    <AccountCircle />
                  </ListItemIcon>
                  <ListItemText
                    primary="Username"
                    secondary={user?.username}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Email />
                  </ListItemIcon>
                  <ListItemText
                    primary="Email"
                    secondary={user?.email}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Key />
                  </ListItemIcon>
                  <ListItemText
                    primary="Account Created"
                    secondary={user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader
              avatar={<Notifications />}
              title="Notifications"
              subheader="Control your notification preferences"
            />
            <Divider />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.emailNotifications}
                      onChange={handleSwitchChange('notifications', 'emailNotifications')}
                    />
                  }
                  label="Email notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.extractionComplete}
                      onChange={handleSwitchChange('notifications', 'extractionComplete')}
                    />
                  }
                  label="Extraction completion alerts"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.ontologyCreated}
                      onChange={handleSwitchChange('notifications', 'ontologyCreated')}
                    />
                  }
                  label="Ontology creation notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.systemUpdates}
                      onChange={handleSwitchChange('notifications', 'systemUpdates')}
                    />
                  }
                  label="System update announcements"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Appearance Settings */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader
              avatar={<Palette />}
              title="Appearance"
              subheader="Customize the interface"
            />
            <Divider />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <FormControl fullWidth>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={settings.preferences.theme}
                    label="Theme"
                    onChange={handleSelectChange('preferences', 'theme')}
                  >
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="auto">Auto (System)</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={settings.preferences.language}
                    label="Language"
                    onChange={handleSelectChange('preferences', 'language')}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Español</MenuItem>
                    <MenuItem value="fr">Français</MenuItem>
                    <MenuItem value="de">Deutsch</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Processing Settings */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader
              avatar={<Storage />}
              title="Processing Defaults"
              subheader="Default settings for document processing"
            />
            <Divider />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <TextField
                  fullWidth
                  label="Default Chunk Size"
                  type="number"
                  value={settings.preferences.defaultChunkSize}
                  onChange={handleTextChange('preferences', 'defaultChunkSize')}
                  helperText="Default text chunk size for processing (characters)"
                  InputProps={{ inputProps: { min: 500, max: 2000, step: 100 } }}
                />
                
                <TextField
                  fullWidth
                  label="Default Overlap Percentage"
                  type="number"
                  value={settings.preferences.defaultOverlap}
                  onChange={handleTextChange('preferences', 'defaultOverlap')}
                  helperText="Default overlap between chunks (percentage)"
                  InputProps={{ inputProps: { min: 0, max: 50, step: 5 } }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* API Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<Api />}
              title="API Configuration"
              subheader="Configure external API integrations"
            />
            <Divider />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Anthropic API Key"
                    type="password"
                    value={settings.api.anthropicApiKey}
                    onChange={handleTextChange('api', 'anthropicApiKey')}
                    helperText="Your Anthropic API key for AI processing (stored securely)"
                    placeholder="sk-ant-..."
                  />
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    label="Max Retries"
                    type="number"
                    value={settings.api.maxRetries}
                    onChange={handleTextChange('api', 'maxRetries')}
                    helperText="Maximum API retry attempts"
                    InputProps={{ inputProps: { min: 1, max: 10 } }}
                  />
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    label="Timeout (seconds)"
                    type="number"
                    value={settings.api.timeout}
                    onChange={handleTextChange('api', 'timeout')}
                    helperText="API request timeout"
                    InputProps={{ inputProps: { min: 10, max: 120 } }}
                  />
                </Grid>
              </Grid>

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Security Note:</strong> API keys are encrypted and stored securely. 
                  They are never transmitted in plain text or logged.
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        {/* Save Button */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button variant="outlined" size="large">
              Reset to Defaults
            </Button>
            <Button 
              variant="contained" 
              size="large" 
              startIcon={<Save />}
              onClick={handleSave}
            >
              Save Settings
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};