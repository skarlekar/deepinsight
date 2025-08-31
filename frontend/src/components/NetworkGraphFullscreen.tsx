import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, AppBar, Toolbar, IconButton } from '@mui/material';
import { Close } from '@mui/icons-material';
import { NetworkGraph } from './NetworkGraph';
import { ExtractionNode, ExtractionRelationship } from '../types';

export const NetworkGraphFullscreen: React.FC = () => {
  const [nodes, setNodes] = useState<ExtractionNode[]>([]);
  const [relationships, setRelationships] = useState<ExtractionRelationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Get data from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const dataParam = urlParams.get('data');
    
    if (!dataParam) {
      setError('No graph data provided');
      setLoading(false);
      return;
    }

    try {
      const decodedData = decodeURIComponent(dataParam);
      const graphData = JSON.parse(decodedData);
      
      if (graphData.nodes && graphData.relationships) {
        setNodes(graphData.nodes);
        setRelationships(graphData.relationships);
        console.log('Loaded fullscreen graph data:', graphData);
      } else {
        setError('Invalid graph data format');
      }
    } catch (err) {
      console.error('Error parsing graph data:', err);
      setError('Failed to parse graph data');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleClose = () => {
    window.close();
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
        <Typography variant="h6">Loading network visualization...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: 2
      }}>
        <Typography variant="h6" color="error">Error: {error}</Typography>
        <Typography variant="body2" color="text.secondary">
          Please try opening the fullscreen view again from the main application.
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