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
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Tooltip,
  LinearProgress,
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add,
  Delete,
  Visibility,
  Edit,
  Refresh,
  Schema,
  Replay,
  ExpandMore,
  Download,
  Timeline,
} from '@mui/icons-material';
import { OntologyDialog } from './OntologyDialog';
import { OntologyProgressDialog } from './OntologyProgressDialog';
import apiService from '../services/api';
import { Ontology, OntologyStatus } from '../types';
import { formatDateToLocal } from '../utils/dateUtils';

export const OntologiesPage: React.FC = () => {
  const [ontologies, setOntologies] = useState<Ontology[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ontologyToDelete, setOntologyToDelete] = useState<Ontology | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedOntology, setSelectedOntology] = useState<any>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [ontologyToEdit, setOntologyToEdit] = useState<any>(null);
  const [progressDialogOpen, setProgressDialogOpen] = useState(false);
  const [selectedOntologyId, setSelectedOntologyId] = useState<string | null>(null);

  useEffect(() => {
    loadOntologies();
  }, []);

  const loadOntologies = async () => {
    try {
      setLoading(true);
      const response = await apiService.getOntologies();
      setOntologies(response);
    } catch (error) {
      console.error('Failed to load ontologies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (ontology: Ontology) => {
    setOntologyToDelete(ontology);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!ontologyToDelete) return;

    try {
      await apiService.deleteOntology(ontologyToDelete.id);
      setDeleteDialogOpen(false);
      setOntologyToDelete(null);
      loadOntologies();
    } catch (error) {
      console.error('Failed to delete ontology:', error);
    }
  };

  const handleReprocess = async (ontologyId: string) => {
    try {
      await apiService.reprocessOntology(ontologyId);
      loadOntologies(); // Refresh to show updated status
    } catch (error) {
      console.error('Failed to reprocess ontology:', error);
    }
  };

  const handleViewDetails = async (ontologyId: string) => {
    try {
      const ontologyDetail = await apiService.getOntology(ontologyId);
      setSelectedOntology(ontologyDetail);
      setViewDialogOpen(true);
    } catch (error) {
      console.error('Failed to load ontology details:', error);
    }
  };

  const handleEditClick = async (ontologyId: string) => {
    try {
      const ontologyDetail = await apiService.getOntology(ontologyId);
      setOntologyToEdit(ontologyDetail);
      setEditDialogOpen(true);
    } catch (error) {
      console.error('Failed to load ontology for editing:', error);
    }
  };

  const handleEditSave = async (updatedOntology: any) => {
    try {
      await apiService.updateOntology(updatedOntology.id, {
        name: updatedOntology.name,
        description: updatedOntology.description,
        triples: updatedOntology.triples,
      });
      setEditDialogOpen(false);
      setOntologyToEdit(null);
      loadOntologies();
    } catch (error) {
      console.error('Failed to update ontology:', error);
    }
  };

  const handleDownloadOntology = async (ontologyId: string, ontologyName: string) => {
    try {
      const ontologyDetail = await apiService.getOntology(ontologyId);
      
      // Create the JSON data to download
      const jsonData = {
        name: ontologyDetail.name,
        description: ontologyDetail.description,
        version: ontologyDetail.version,
        status: ontologyDetail.status,
        triples: ontologyDetail.triples,
        created_at: ontologyDetail.created_at,
        updated_at: ontologyDetail.updated_at,
      };

      // Create blob and download
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
        type: 'application/json',
      });
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${ontologyName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_ontology.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download ontology:', error);
    }
  };

  const handleViewProgress = (ontologyId: string) => {
    setSelectedOntologyId(ontologyId);
    setProgressDialogOpen(true);
  };

  const handleProgressDialogClose = () => {
    setProgressDialogOpen(false);
    setSelectedOntologyId(null);
    // Refresh ontologies when dialog closes to get latest status
    loadOntologies();
  };

  const getStatusColor = (status: OntologyStatus) => {
    switch (status) {
      case OntologyStatus.ACTIVE:
        return 'success';
      case OntologyStatus.PROCESSING:
        return 'warning';
      case OntologyStatus.ARCHIVED:
        return 'default';
      case OntologyStatus.DRAFT:
        return 'info';
      default:
        return 'default';
    }
  };

  // Using formatDateToLocalToLocal from utils instead of local function

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Ontologies
        </Typography>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2 }}>
          Loading ontologies...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Ontologies
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadOntologies}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Ontology
          </Button>
        </Box>
      </Box>

      {ontologies.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Schema sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            No ontologies yet
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            Create your first AI-powered ontology schema from uploaded documents
          </Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
            size="large"
          >
            Create Your First Ontology
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {ontologies.map((ontology) => (
            <Grid item xs={12} md={6} lg={4} key={ontology.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h3" gutterBottom>
                      {ontology.name}
                    </Typography>
                    <Chip
                      label={ontology.status}
                      color={getStatusColor(ontology.status) as any}
                      size="small"
                    />
                  </Box>
                  
                  {ontology.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {ontology.description}
                    </Typography>
                  )}

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Version {ontology.version}
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Created: {formatDateToLocal(ontology.created_at)}
                    </Typography>
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary">
                    Updated: {formatDateToLocal(ontology.updated_at)}
                  </Typography>
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Box>
                    <Tooltip title="View Details">
                      <IconButton 
                        size="small"
                        onClick={() => handleViewDetails(ontology.id)}
                      >
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton 
                        size="small"
                        onClick={() => handleEditClick(ontology.id)}
                      >
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Download JSON">
                      <IconButton 
                        size="small" 
                        color="primary"
                        onClick={() => handleDownloadOntology(ontology.id, ontology.name)}
                      >
                        <Download />
                      </IconButton>
                    </Tooltip>
                    {ontology.status === OntologyStatus.PROCESSING && (
                      <Tooltip title="View Progress">
                        <IconButton 
                          size="small" 
                          color="primary"
                          onClick={() => handleViewProgress(ontology.id)}
                        >
                          <Timeline />
                        </IconButton>
                      </Tooltip>
                    )}
                    {ontology.status === OntologyStatus.DRAFT && (
                      <Tooltip title="Reprocess with AI">
                        <IconButton 
                          size="small" 
                          color="primary"
                          onClick={() => handleReprocess(ontology.id)}
                        >
                          <Replay />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                  <Tooltip title="Delete">
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={() => handleDeleteClick(ontology)}
                    >
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Dialog */}
      <OntologyDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onOntologyCreated={loadOntologies}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Ontology</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the ontology "{ontologyToDelete?.name}"? 
            This action cannot be undone and will affect any active extractions using this ontology.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Details Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Ontology Details: {selectedOntology?.name}
        </DialogTitle>
        <DialogContent>
          {selectedOntology && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Information
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Description:</strong> {selectedOntology.description || 'No description'}
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Status:</strong> <Chip label={selectedOntology.status} size="small" />
              </Typography>
              <Typography variant="body2" sx={{ mb: 3 }}>
                <strong>Version:</strong> {selectedOntology.version}
              </Typography>

              <Typography variant="h6" gutterBottom>
                Ontology Triples ({selectedOntology.triples?.length || 0})
              </Typography>
              {selectedOntology.triples && selectedOntology.triples.length > 0 ? (
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {selectedOntology.triples.map((triple: any, index: number) => (
                    <Paper key={index} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Subject:</strong> {triple.subject?.entity_type} 
                        {triple.subject?.type_variations && (
                          <span style={{ color: 'gray' }}> ({triple.subject.type_variations.join(', ')})</span>
                        )}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Relationship:</strong> {triple.relationship?.relationship_type}
                        {triple.relationship?.type_variations && (
                          <span style={{ color: 'gray' }}> ({triple.relationship.type_variations.join(', ')})</span>
                        )}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Object:</strong> {triple.object?.entity_type}
                        {triple.object?.type_variations && (
                          <span style={{ color: 'gray' }}> ({triple.object.type_variations.join(', ')})</span>
                        )}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">
                  No triples defined yet. The AI processing may still be in progress.
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Edit Ontology: {ontologyToEdit?.name}
        </DialogTitle>
        <DialogContent>
          {ontologyToEdit && (
            <Box>
              <TextField
                fullWidth
                label="Name"
                value={ontologyToEdit.name}
                onChange={(e) => setOntologyToEdit({...ontologyToEdit, name: e.target.value})}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Description"
                value={ontologyToEdit.description || ''}
                onChange={(e) => setOntologyToEdit({...ontologyToEdit, description: e.target.value})}
                multiline
                rows={3}
                sx={{ mb: 3 }}
              />
              
              <Typography variant="h6" gutterBottom>
                Ontology Triples ({ontologyToEdit.triples?.length || 0})
              </Typography>
              
              {ontologyToEdit.triples && ontologyToEdit.triples.length > 0 ? (
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {ontologyToEdit.triples.map((triple: any, index: number) => (
                    <Accordion key={index} sx={{ mb: 1 }}>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="body2">
                          {triple.subject?.entity_type} → {triple.relationship?.relationship_type} → {triple.object?.entity_type}
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Grid container spacing={2}>
                          <Grid item xs={4}>
                            <Typography variant="subtitle2" gutterBottom>Subject</Typography>
                            <TextField
                              fullWidth
                              size="small"
                              label="Entity Type"
                              value={triple.subject?.entity_type || ''}
                              onChange={(e) => {
                                const updatedTriples = [...ontologyToEdit.triples];
                                updatedTriples[index].subject.entity_type = e.target.value;
                                setOntologyToEdit({...ontologyToEdit, triples: updatedTriples});
                              }}
                              sx={{ mb: 1 }}
                            />
                            <TextField
                              fullWidth
                              size="small"
                              label="Variations (comma separated)"
                              value={triple.subject?.type_variations?.join(', ') || ''}
                              onChange={(e) => {
                                const updatedTriples = [...ontologyToEdit.triples];
                                updatedTriples[index].subject.type_variations = e.target.value.split(',').map(s => s.trim());
                                setOntologyToEdit({...ontologyToEdit, triples: updatedTriples});
                              }}
                            />
                          </Grid>
                          <Grid item xs={4}>
                            <Typography variant="subtitle2" gutterBottom>Relationship</Typography>
                            <TextField
                              fullWidth
                              size="small"
                              label="Relationship Type"
                              value={triple.relationship?.relationship_type || ''}
                              onChange={(e) => {
                                const updatedTriples = [...ontologyToEdit.triples];
                                updatedTriples[index].relationship.relationship_type = e.target.value;
                                setOntologyToEdit({...ontologyToEdit, triples: updatedTriples});
                              }}
                              sx={{ mb: 1 }}
                            />
                            <TextField
                              fullWidth
                              size="small"
                              label="Variations (comma separated)"
                              value={triple.relationship?.type_variations?.join(', ') || ''}
                              onChange={(e) => {
                                const updatedTriples = [...ontologyToEdit.triples];
                                updatedTriples[index].relationship.type_variations = e.target.value.split(',').map(s => s.trim());
                                setOntologyToEdit({...ontologyToEdit, triples: updatedTriples});
                              }}
                            />
                          </Grid>
                          <Grid item xs={4}>
                            <Typography variant="subtitle2" gutterBottom>Object</Typography>
                            <TextField
                              fullWidth
                              size="small"
                              label="Entity Type"
                              value={triple.object?.entity_type || ''}
                              onChange={(e) => {
                                const updatedTriples = [...ontologyToEdit.triples];
                                updatedTriples[index].object.entity_type = e.target.value;
                                setOntologyToEdit({...ontologyToEdit, triples: updatedTriples});
                              }}
                              sx={{ mb: 1 }}
                            />
                            <TextField
                              fullWidth
                              size="small"
                              label="Variations (comma separated)"
                              value={triple.object?.type_variations?.join(', ') || ''}
                              onChange={(e) => {
                                const updatedTriples = [...ontologyToEdit.triples];
                                updatedTriples[index].object.type_variations = e.target.value.split(',').map(s => s.trim());
                                setOntologyToEdit({...ontologyToEdit, triples: updatedTriples});
                              }}
                            />
                          </Grid>
                        </Grid>
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">
                  No triples defined yet.
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={() => handleEditSave(ontologyToEdit)} 
            variant="contained"
            disabled={!ontologyToEdit?.name}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Progress Dialog */}
      <OntologyProgressDialog
        open={progressDialogOpen}
        onClose={handleProgressDialogClose}
        ontologyId={selectedOntologyId}
      />
    </Box>
  );
};