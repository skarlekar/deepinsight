import React, { useState } from 'react';
import { Box, CssBaseline } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Sidebar } from './Sidebar';
import { Dashboard } from './Dashboard';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  components: {
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#fafafa',
        },
      },
    },
  },
});

const drawerWidth = 240;

export const Layout: React.FC = () => {
  const [activeSection, setActiveSection] = useState('dashboard');

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <Dashboard />;
      case 'documents':
        return (
          <Box sx={{ p: 3 }}>
            <h1>Documents</h1>
            <p>Document management coming soon...</p>
          </Box>
        );
      case 'ontologies':
        return (
          <Box sx={{ p: 3 }}>
            <h1>Ontologies</h1>
            <p>Ontology management coming soon...</p>
          </Box>
        );
      case 'extractions':
        return (
          <Box sx={{ p: 3 }}>
            <h1>Extractions</h1>
            <p>Extraction management coming soon...</p>
          </Box>
        );
      case 'databases':
        return (
          <Box sx={{ p: 3 }}>
            <h1>Databases</h1>
            <p>Database configuration coming soon...</p>
          </Box>
        );
      case 'settings':
        return (
          <Box sx={{ p: 3 }}>
            <h1>Settings</h1>
            <p>User settings coming soon...</p>
          </Box>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex' }}>
        <Sidebar 
          activeSection={activeSection} 
          onSectionChange={setActiveSection}
        />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            ml: `${drawerWidth}px`,
            minHeight: '100vh',
            bgcolor: 'background.default',
          }}
        >
          {renderContent()}
        </Box>
      </Box>
    </ThemeProvider>
  );
};