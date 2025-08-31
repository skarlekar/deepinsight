import React, { useState } from 'react';
import { Box, CssBaseline } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Sidebar } from './Sidebar';
import { Dashboard } from './Dashboard';
import { DocumentsPage } from './DocumentsPage';
import { OntologiesPage } from './OntologiesPage';
import { ExtractionsPage } from './ExtractionsPage';
import { DatabasesPage } from './DatabasesPage';
import { SettingsPage } from './SettingsPage';

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
        return <DocumentsPage />;
      case 'ontologies':
        return <OntologiesPage />;
      case 'extractions':
        return <ExtractionsPage />;
      case 'databases':
        return <DatabasesPage />;
      case 'settings':
        return <SettingsPage />;
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