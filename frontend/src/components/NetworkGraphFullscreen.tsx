import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, AppBar, Toolbar, IconButton, Alert, CircularProgress } from '@mui/material';
import { Close, Download } from '@mui/icons-material';
import { NetworkGraph } from './NetworkGraph';
import { ExtractionNode, ExtractionRelationship } from '../types';

export const NetworkGraphFullscreen: React.FC = () => {
  const [nodes, setNodes] = useState<ExtractionNode[]>([]);
  const [relationships, setRelationships] = useState<ExtractionRelationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    // Get session key from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const sessionKey = urlParams.get('session');

    // Clean up sessionStorage when the window/tab is closed
    const handleBeforeUnload = () => {
      if (sessionKey) {
        sessionStorage.removeItem(sessionKey);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    // StrictMode-safe cleanup function - only remove event listener, not sessionStorage
    const cleanup = () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      // Don't remove sessionStorage here - it causes issues with React StrictMode
      // sessionStorage.removeItem(sessionKey);
    };
    
    if (!sessionKey) {
      setError('No session key provided');
      setLoading(false);
      return;
    }

    // Skip if data is already loaded (prevents React StrictMode double-execution)
    if (dataLoaded) {
      return;
    }

    try {
      // Retrieve data from sessionStorage
      const storedData = sessionStorage.getItem(sessionKey);
      
      if (!storedData) {
        setError('Graph data not found in session storage');
        setLoading(false);
        return;
      }

      const graphData = JSON.parse(storedData);
      
      // Validate the data structure
      if (!graphData.nodes || !Array.isArray(graphData.nodes)) {
        setError('Invalid graph data: missing or invalid nodes array');
        setLoading(false);
        return;
      }

      if (!graphData.relationships || !Array.isArray(graphData.relationships)) {
        setError('Invalid graph data: missing or invalid relationships array');
        setLoading(false);
        return;
      }
      
      setNodes(graphData.nodes);
      setRelationships(graphData.relationships);
      setDataLoaded(true); // Mark data as loaded to prevent double-loading

      // Don't clean up immediately - let the user potentially reload the page
      // sessionStorage.removeItem(sessionKey);
    } catch (err) {
      console.error('Error loading graph data:', err);
      setError('Failed to load graph data from session storage');
    } finally {
      setLoading(false);
    }

    // Return cleanup function
    return cleanup;
  }, [dataLoaded]); // Include dataLoaded in dependencies

  const handleClose = () => {
    // Clean up sessionStorage before closing
    const urlParams = new URLSearchParams(window.location.search);
    const sessionKey = urlParams.get('session');
    if (sessionKey) {
      sessionStorage.removeItem(sessionKey);
    }
    window.close();
  };

  const handleDownload = () => {
    const graphData = { nodes, relationships };
    const dataStr = JSON.stringify(graphData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `network_graph_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: 2
      }}>
        <CircularProgress />
        <Typography variant="h6">Loading network visualization...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3, height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppBar position="static" sx={{ bgcolor: 'primary.main', mb: 3 }}>
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Network Visualization - Error
            </Typography>
            <IconButton
              edge="end"
              color="inherit"
              onClick={handleClose}
              aria-label="close"
            >
              <Close />
            </IconButton>
          </Toolbar>
        </AppBar>
        
        <Alert severity="error" sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
          <Typography variant="h6" gutterBottom>Error Loading Graph</Typography>
          <Typography>{error}</Typography>
        </Alert>
        
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
          This usually happens when the page is refreshed or the session has expired. 
          Please close this window and try opening the full screen view again from the main application.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* App Bar */}
      <AppBar position="static" sx={{ bgcolor: 'primary.main' }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Network Visualization - Fullscreen
          </Typography>
          <Typography variant="body2" sx={{ mr: 2, opacity: 0.8 }}>
            {nodes.length} nodes, {relationships.length} relationships
          </Typography>
          <IconButton
            color="inherit"
            onClick={handleDownload}
            aria-label="download"
            title="Download graph data as JSON"
          >
            <Download />
          </IconButton>
          <IconButton
            edge="end"
            color="inherit"
            onClick={handleClose}
            aria-label="close"
            title="Close"
          >
            <Close />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Network Graph Container */}
      <Box sx={{ 
        flexGrow: 1, 
        p: 2,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <Box sx={{ flexGrow: 1 }}>
          <NetworkGraph 
            nodes={nodes} 
            relationships={relationships} 
            height={window.innerHeight - 120} // Full height minus app bar and padding
          />
        </Box>
        
        {/* Stats */}
        <Paper sx={{ 
          mt: 2, 
          p: 2, 
          display: 'flex', 
          gap: 4,
          justifyContent: 'center',
          backgroundColor: 'background.default'
        }}>
          <Typography variant="body2" color="text.secondary">
            <strong>Nodes:</strong> {nodes.length}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Relationships:</strong> {relationships.length}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Total Elements:</strong> {nodes.length + relationships.length}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};