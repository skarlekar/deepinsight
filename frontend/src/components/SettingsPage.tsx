import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
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
  Palette,
  Storage,
  Api,
  Save,
  Key,
  Email,
  AccountCircle,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { UserSettings, UserSettingsUpdate } from '../types';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState<string>('');

  // Load user settings on component mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        const userSettings = await apiService.getUserSettings();
        setSettings(userSettings);
      } catch (error) {
        console.error('Failed to load settings:', error);
        setError('Failed to load settings');
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  const handleSwitchChange = (field: keyof UserSettings) => (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!settings) return;
    setSettings(prev => prev ? {
      ...prev,
      [field]: event.target.checked,
    } : null);
  };

  const handleSelectChange = (field: keyof UserSettings) => (event: any) => {
    if (!settings) return;
    setSettings(prev => prev ? {
      ...prev,
      [field]: event.target.value,
    } : null);
  };

  const handleTextChange = (field: keyof UserSettings) => (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!settings) return;
    const value = field === 'default_chunk_size' || field === 'default_overlap_percentage' || field === 'max_retries' || field === 'timeout_seconds'
      ? parseInt(event.target.value) || 0
      : event.target.value;
    
    setSettings(prev => prev ? {
      ...prev,
      [field]: value,
    } : null);
  };

  const handleSave = async () => {
    if (!settings) return;
    
    try {
      setSaving(true);
      setError('');
      
      const updateData: UserSettingsUpdate = {
        default_chunk_size: settings.default_chunk_size,
        default_overlap_percentage: settings.default_overlap_percentage,
        email_notifications: settings.email_notifications,
        extraction_complete: settings.extraction_complete,
        ontology_created: settings.ontology_created,
        system_updates: settings.system_updates,
        theme: settings.theme,
        language: settings.language,
        max_retries: settings.max_retries,
        timeout_seconds: settings.timeout_seconds
      };
      
      const updatedSettings = await apiService.updateUserSettings(updateData);
      setSettings(updatedSettings);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      setSaving(true);
      setError('');
      await apiService.resetUserSettings();
      // Reload settings
      const userSettings = await apiService.getUserSettings();
      setSettings(userSettings);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to reset settings:', error);
      setError('Failed to reset settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <Typography>Loading settings...</Typography>
      </Box>
    );
  }

  if (!settings) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load settings. Please refresh the page.
        </Alert>
      </Box>
    );
  }

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
                      checked={settings.email_notifications}
                      onChange={handleSwitchChange('email_notifications')}
                    />
                  }
                  label="Email notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.extraction_complete}
                      onChange={handleSwitchChange('extraction_complete')}
                    />
                  }
                  label="Extraction completion alerts"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.ontology_created}
                      onChange={handleSwitchChange('ontology_created')}
                    />
                  }
                  label="Ontology creation notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.system_updates}
                      onChange={handleSwitchChange('system_updates')}
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
                    value={settings.theme}
                    label="Theme"
                    onChange={handleSelectChange('theme')}
                  >
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="auto">Auto (System)</MenuItem>
                  </Select>
                </FormControl>

                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={settings.language}
                    label="Language"
                    onChange={handleSelectChange('language')}
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
                  value={settings.default_chunk_size}
                  onChange={handleTextChange('default_chunk_size')}
                  helperText="Default text chunk size for processing (characters)"
                  InputProps={{ inputProps: { min: 500, max: 2000, step: 100 } }}
                />
                
                <TextField
                  fullWidth
                  label="Default Overlap Percentage"
                  type="number"
                  value={settings.default_overlap_percentage}
                  onChange={handleTextChange('default_overlap_percentage')}
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
                    value={settings.anthropic_api_key_configured ? '••••••••••••••••••••' : ''}
                    onChange={(e) => {
                      if (!settings) return;
                      setSettings(prev => prev ? {
                        ...prev,
                        anthropic_api_key_configured: e.target.value.length > 0
                      } : null);
                    }}
                    helperText="Your Anthropic API key for AI processing (stored securely)"
                    placeholder="sk-ant-..."
                  />
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    label="Max Retries"
                    type="number"
                    value={settings.max_retries}
                    onChange={handleTextChange('max_retries')}
                    helperText="Maximum API retry attempts"
                    InputProps={{ inputProps: { min: 1, max: 10 } }}
                  />
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    label="Timeout (seconds)"
                    type="number"
                    value={settings.timeout_seconds}
                    onChange={handleTextChange('timeout_seconds')}
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
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button 
              variant="outlined" 
              size="large"
              onClick={handleReset}
              disabled={saving}
            >
              Reset to Defaults
            </Button>
            <Button 
              variant="contained" 
              size="large" 
              startIcon={<Save />}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};