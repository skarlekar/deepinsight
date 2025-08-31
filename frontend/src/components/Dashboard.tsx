import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
} from '@mui/material';
import {
  Upload,
  Schema,
  DataUsage,
  Settings,
  TrendingUp,
  Description,
  CheckCircle,
  Error as ErrorIcon,
  PlayArrow,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import apiService from '../services/api';
import { Document, Ontology, Extraction } from '../types';
import { UploadDialog } from './UploadDialog';
import { OntologyDialog } from './OntologyDialog';
import { ExtractionDialog } from './ExtractionDialog';
import { DatabaseDialog } from './DatabaseDialog';

interface DashboardStats {
  documents: number;
  ontologies: number;
  extractions: number;
  completed: number;
}

interface RecentActivity {
  type: 'document' | 'ontology' | 'extraction';
  title: string;
  status: string;
  timestamp: string;
}

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    documents: 0,
    ontologies: 0,
    extractions: 0,
    completed: 0,
  });
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Dialog states
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [ontologyDialogOpen, setOntologyDialogOpen] = useState(false);
  const [extractionDialogOpen, setExtractionDialogOpen] = useState(false);
  const [databaseDialogOpen, setDatabaseDialogOpen] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [documents, ontologies, extractions] = await Promise.all([
        apiService.getDocuments(1, 100),
        apiService.getOntologies(),
        apiService.getExtractions(),
      ]);

      setStats({
        documents: documents.total,
        ontologies: ontologies.length,
        extractions: extractions.length,
        completed: extractions.filter(e => e.status === 'completed').length,
      });

      const activities: RecentActivity[] = [
        ...documents.documents.slice(0, 3).map(doc => ({
          type: 'document' as const,
          title: doc.original_filename,
          status: doc.status,
          timestamp: doc.created_at,
        })),
        ...ontologies.slice(0, 3).map(ont => ({
          type: 'ontology' as const,
          title: ont.name,
          status: ont.status,
          timestamp: ont.created_at,
        })),
        ...extractions.slice(0, 3).map(ext => ({
          type: 'extraction' as const,
          title: `Extraction ${ext.id.slice(0, 8)}`,
          status: ext.status,
          timestamp: ext.created_at,
        })),
      ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, 5);

      setRecentActivity(activities);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'active':
        return 'success';
      case 'processing':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'document':
        return <Description />;
      case 'ontology':
        return <Schema />;
      case 'extraction':
        return <DataUsage />;
      default:
        return <CheckCircle />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Welcome back, {user?.username}!
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Here's what's happening with your projects today.
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Statistics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Documents
                  </Typography>
                  <Typography variant="h4">
                    {stats.documents}
                  </Typography>
                </Box>
                <Description color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Ontologies
                  </Typography>
                  <Typography variant="h4">
                    {stats.ontologies}
                  </Typography>
                </Box>
                <Schema color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Active Extractions
                  </Typography>
                  <Typography variant="h4">
                    {stats.extractions}
                  </Typography>
                </Box>
                <DataUsage color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Completed Tasks
                  </Typography>
                  <Typography variant="h4">
                    {stats.completed}
                  </Typography>
                </Box>
                <CheckCircle color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<Upload />}
                  onClick={() => setUploadDialogOpen(true)}
                  sx={{ py: 2, flexDirection: 'column', height: '100px' }}
                >
                  Upload Document
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Schema />}
                  onClick={() => setOntologyDialogOpen(true)}
                  sx={{ py: 2, flexDirection: 'column', height: '100px' }}
                >
                  Create Ontology
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<PlayArrow />}
                  onClick={() => setExtractionDialogOpen(true)}
                  sx={{ py: 2, flexDirection: 'column', height: '100px' }}
                >
                  Start Extraction
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Settings />}
                  onClick={() => setDatabaseDialogOpen(true)}
                  sx={{ py: 2, flexDirection: 'column', height: '100px' }}
                >
                  Configure Database
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List>
              {recentActivity.length > 0 ? (
                recentActivity.map((activity, index) => (
                  <ListItem key={index} divider={index < recentActivity.length - 1}>
                    <ListItemIcon>
                      {getActivityIcon(activity.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.title}
                      secondary={new Date(activity.timestamp).toLocaleDateString()}
                    />
                    <Chip
                      size="small"
                      label={activity.status}
                      color={getStatusColor(activity.status) as any}
                    />
                  </ListItem>
                ))
              ) : (
                <ListItem>
                  <ListItemText
                    primary="No recent activity"
                    secondary="Start by uploading a document"
                  />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        {/* Getting Started */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: 'primary.main', color: 'white' }}>
            <Typography variant="h6" gutterBottom>
              Getting Started with DeepInsight
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={3}>
                <Typography variant="body2">
                  <strong>1. Upload Documents</strong><br />
                  Upload your PDF, DOCX, TXT, or MD files to begin analysis.
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2">
                  <strong>2. Create Ontologies</strong><br />
                  Let AI analyze your documents and create knowledge schemas.
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2">
                  <strong>3. Extract Data</strong><br />
                  Process documents using ontologies to extract structured data.
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2">
                  <strong>4. Export Results</strong><br />
                  Export your graph data to Neo4j or AWS Neptune formats.
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      {/* Dialog Components */}
      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUploadComplete={loadDashboardData}
      />
      
      <OntologyDialog
        open={ontologyDialogOpen}
        onClose={() => setOntologyDialogOpen(false)}
        onOntologyCreated={loadDashboardData}
      />
      
      <ExtractionDialog
        open={extractionDialogOpen}
        onClose={() => setExtractionDialogOpen(false)}
        onExtractionStarted={loadDashboardData}
      />
      
      <DatabaseDialog
        open={databaseDialogOpen}
        onClose={() => setDatabaseDialogOpen(false)}
        onExportComplete={loadDashboardData}
      />
    </Box>
  );
};