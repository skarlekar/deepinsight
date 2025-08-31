import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
} from '@mui/material';
import {
  Storage,
  Download,
  Refresh,
  Launch,
  CloudDownload,
  Timeline,
  AccountTree,
} from '@mui/icons-material';
import { DatabaseDialog } from './DatabaseDialog';
import apiService from '../services/api';
import { Extraction, ExtractionStatus } from '../types';

export const DatabasesPage: React.FC = () => {
  const [extractions, setExtractions] = useState<Extraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [recentExports, setRecentExports] = useState<any[]>([]);

  useEffect(() => {
    loadExtractions();
  }, []);

  const loadExtractions = async () => {
    try {
      setLoading(true);
      const response = await apiService.getExtractions();
      setExtractions(response.filter(ext => ext.status === ExtractionStatus.COMPLETED));
    } catch (error) {
      console.error('Failed to load extractions:', error);
    } finally {
      setLoading(false);
    }
  };

  const completedExtractions = extractions.filter(ext => ext.status === ExtractionStatus.COMPLETED);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Database Export
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadExtractions}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Storage />}
            onClick={() => setExportDialogOpen(true)}
            disabled={completedExtractions.length === 0}
          >
            Export to Database
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Export Options */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Supported Database Formats
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <AccountTree sx={{ mr: 2, color: 'primary.main' }} />
                      <Typography variant="h6">
                        Neo4j
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      Export as CSV files optimized for Neo4j's LOAD CSV command. 
                      Includes separate files for nodes and relationships with proper headers.
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemIcon>
                          <CloudDownload fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary="nodes.csv" 
                          secondary="Entity nodes with properties"
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <CloudDownload fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary="relationships.csv" 
                          secondary="Relationship edges with properties"
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      onClick={() => setExportDialogOpen(true)}
                      disabled={completedExtractions.length === 0}
                    >
                      Export to Neo4j
                    </Button>
                    <Button size="small" startIcon={<Launch />} href="https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/" target="_blank">
                      Import Guide
                    </Button>
                  </CardActions>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Timeline sx={{ mr: 2, color: 'primary.main' }} />
                      <Typography variant="h6">
                        AWS Neptune
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      Export as CSV files compatible with Amazon Neptune's bulk loader. 
                      Follows Neptune's specific format requirements for vertices and edges.
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemIcon>
                          <CloudDownload fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary="vertices.csv" 
                          secondary="Graph vertices with metadata"
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemIcon>
                          <CloudDownload fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary="edges.csv" 
                          secondary="Graph edges with relationships"
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      onClick={() => setExportDialogOpen(true)}
                      disabled={completedExtractions.length === 0}
                    >
                      Export to Neptune
                    </Button>
                    <Button size="small" startIcon={<Launch />} href="https://docs.aws.amazon.com/neptune/latest/userguide/bulk-load.html" target="_blank">
                      Import Guide
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            </Grid>
          </Paper>

          {/* Available Extractions */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Available Extractions for Export
            </Typography>
            
            {completedExtractions.length === 0 ? (
              <Alert severity="info">
                No completed extractions available for export. Complete an extraction first to export data to databases.
              </Alert>
            ) : (
              <List>
                {completedExtractions.map((extraction, index) => (
                  <React.Fragment key={extraction.id}>
                    <ListItem>
                      <ListItemIcon>
                        <Storage color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary={`Extraction ${extraction.id.slice(0, 8)}...`}
                        secondary={
                          <Box>
                            <Typography variant="body2" component="span">
                              Completed: {new Date(extraction.completed_at!).toLocaleString()}
                            </Typography>
                            <br />
                            <Typography variant="body2" component="span" color="text.secondary">
                              Document: {extraction.document_id.slice(0, 8)}... | 
                              Ontology: {extraction.ontology_id.slice(0, 8)}...
                            </Typography>
                          </Box>
                        }
                      />
                      <Box>
                        <Tooltip title="Export this extraction">
                          <IconButton 
                            edge="end" 
                            onClick={() => setExportDialogOpen(true)}
                          >
                            <Download />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItem>
                    {index < completedExtractions.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Export Status */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Export Statistics
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Total Completed Extractions
              </Typography>
              <Typography variant="h4" color="success.main">
                {completedExtractions.length}
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" gutterBottom>
              Export Tips
            </Typography>
            <List dense>
              <ListItem sx={{ px: 0 }}>
                <ListItemText
                  primary="Neo4j Format"
                  secondary="Best for graph analytics and complex queries"
                />
              </ListItem>
              <ListItem sx={{ px: 0 }}>
                <ListItemText
                  primary="Neptune Format"
                  secondary="Optimized for AWS cloud deployments"
                />
              </ListItem>
              <ListItem sx={{ px: 0 }}>
                <ListItemText
                  primary="Download Links"
                  secondary="CSV downloads expire after 24 hours"
                />
              </ListItem>
            </List>
          </Paper>

          {/* Recent Activity */}
          {recentExports.length > 0 && (
            <Paper sx={{ p: 3, mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Recent Exports
              </Typography>
              
              <List dense>
                {recentExports.slice(0, 5).map((exportItem, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemIcon>
                      <Download fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={exportItem.format}
                      secondary={new Date(exportItem.timestamp).toLocaleString()}
                    />
                    <Chip label="Ready" size="small" color="success" />
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* Export Dialog */}
      <DatabaseDialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        onExportComplete={loadExtractions}
      />
    </Box>
  );
};