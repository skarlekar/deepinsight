import React, { useState } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Login } from './components/Login';
import { Register } from './components/Register';
import { DocumentUpload } from './components/DocumentUpload';
import { Logout } from '@mui/icons-material';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

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
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Dashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Documents" />
            <Tab label="Ontologies" />
            <Tab label="Extractions" />
            <Tab label="Exports" />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h5" gutterBottom>
            Document Management
          </Typography>
          <DocumentUpload 
            onUploadSuccess={(doc) => {
              console.log('Document uploaded:', doc);
              // Optionally refresh document list or show success message
            }}
            onUploadError={(error) => {
              console.error('Upload error:', error);
              // Show error message to user
            }}
          />
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h5" gutterBottom>
            Ontology Management
          </Typography>
          <Typography variant="body1">
            Create and manage ontologies from your uploaded documents.
          </Typography>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h5" gutterBottom>
            Data Extraction
          </Typography>
          <Typography variant="body1">
            Extract structured data using your ontologies.
          </Typography>
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h5" gutterBottom>
            Export to Graph Databases
          </Typography>
          <Typography variant="body1">
            Export your extracted data to Neo4j or AWS Neptune.
          </Typography>
        </TabPanel>
      </Box>
    </Container>
  );
};

const AuthScreen: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);

  return isLogin ? (
    <Login onSwitchToRegister={() => setIsLogin(false)} />
  ) : (
    <Register onSwitchToLogin={() => setIsLogin(true)} />
  );
};

const AppContent: React.FC = () => {
  const { user, loading, logout, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            DeepInsight
          </Typography>
          {isAuthenticated && user && (
            <Box display="flex" alignItems="center" gap={2}>
              <Typography variant="body2">
                Welcome, {user.username}
              </Typography>
              <Button 
                color="inherit" 
                onClick={logout}
                startIcon={<Logout />}
                size="small"
              >
                Logout
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      <main>
        {isAuthenticated ? <Dashboard /> : <AuthScreen />}
      </main>
    </>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;