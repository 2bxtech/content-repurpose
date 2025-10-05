import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  Container, Typography, Box, Paper, Divider, Button, 
  CircularProgress, Alert, TextField, Chip, Tab, Tabs,
  Grid, Card, CardContent
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import ReactMarkdown from 'react-markdown';
import { getTransformation } from '../services/transformationService';
import { getDocument } from '../services/documentService';
import { Transformation, TransformationStatus, Document } from '../types';

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
      id={`transformation-tabpanel-${index}`}
      aria-labelledby={`transformation-tab-${index}`}
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

const TransformationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [transformation, setTransformation] = useState<Transformation | null>(null);
  const [document, setDocument] = useState<Document | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [isPolling, setIsPolling] = useState(false);
  // Use any type to avoid TypeScript errors with setTimeout
  const pollingTimer = useRef<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const transformationData = await getTransformation(id);
        setTransformation(transformationData);
        setEditedContent(transformationData.result || '');
        
        // If the transformation has a document, fetch it
        if (transformationData.document_id) {
          const documentData = await getDocument(transformationData.document_id);
          setDocument(documentData);
        }
        
        // Start polling if the transformation is pending or processing
        if (
          transformationData.status === TransformationStatus.PENDING || 
          transformationData.status === TransformationStatus.PROCESSING
        ) {
          startPolling();
        }
      } catch (err: any) {
        console.error('Error fetching transformation:', err);
        setError('Failed to load transformation details.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Clean up polling timer on unmount
    return () => {
      if (pollingTimer.current) {
        clearTimeout(pollingTimer.current);
      }
    };
  }, [id]);

  const startPolling = () => {
    setIsPolling(true);
    pollingTimer.current = setTimeout(pollTransformation, 5000);
  };

  const pollTransformation = async () => {
    if (!id) return;
    
    try {
      const updatedTransformation = await getTransformation(id);
      setTransformation(updatedTransformation);
      setEditedContent(updatedTransformation.result || '');
      
      // Continue polling if still processing
      if (
        updatedTransformation.status === TransformationStatus.PENDING || 
        updatedTransformation.status === TransformationStatus.PROCESSING
      ) {
        pollingTimer.current = setTimeout(pollTransformation, 5000);
      } else {
        setIsPolling(false);
      }
    } catch (err) {
      console.error('Error polling transformation:', err);
      setIsPolling(false);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const toggleEditMode = () => {
    setEditMode(!editMode);
  };

  const saveEditedContent = () => {
    // In a real app, we'd call an API to save the edited content
    setTransformation(prev => {
      if (!prev) return null;
      return { ...prev, result: editedContent };
    });
    setEditMode(false);
  };

  const exportAsFile = (format: 'txt' | 'md') => {
    if (!transformation || !transformation.result) {
      console.error('No transformation result to export');
      return;
    }
    
    try {
      let content = transformation.result;
      let mimeType = 'text/plain';
      let fileExtension = 'txt';
      
      if (format === 'md') {
        mimeType = 'text/markdown';
        fileExtension = 'md';
      }
      
      // Create filename using document title or transformation ID
      const baseFilename = document?.title 
        ? document.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()
        : `transformation_${transformation.id}`;
      
      const filename = `${baseFilename}.${fileExtension}`;
      
      // Create blob and download
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      
      const link = window.document.createElement('a');
      link.href = url;
      link.download = filename;
      window.document.body.appendChild(link);
      link.click();
      
      // Cleanup
      window.document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting file:', err);
      setError('Failed to export file. Please try again.');
    }
  };

  const getStatusColor = (status: TransformationStatus) => {
    switch (status) {
      case TransformationStatus.COMPLETED:
        return 'success';
      case TransformationStatus.PROCESSING:
        return 'warning';
      case TransformationStatus.FAILED:
        return 'error';
      default:
        return 'default';
    }
  };

  const renderTransformationTypeName = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', my: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!transformation && !loading) {
    return (
      <Container maxWidth="lg">
        <Alert severity="error" sx={{ mt: 4 }}>
          Transformation not found or you don't have permission to access it.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      {error && (
        <Alert severity="error" sx={{ mt: 4, mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {transformation && (
        <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <Typography variant="h4" component="h1" gutterBottom>
                {renderTransformationTypeName(transformation.transformation_type)}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Chip 
                label={transformation.status} 
                color={getStatusColor(transformation.status)} 
                sx={{ ml: 2 }}
              />
            </Grid>
          </Grid>
          
          {isPolling && (
            <Alert severity="info" sx={{ mt: 2, mb: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CircularProgress size={20} sx={{ mr: 2 }} />
                <span>Processing content transformation. This may take a few minutes.</span>
              </Box>
            </Alert>
          )}
          
          {document && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6">Source Document</Typography>
              <Typography variant="body1">
                <RouterLink to={`/documents/${document.id}`}>
                  {document.title}
                </RouterLink>
              </Typography>
            </Box>
          )}
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6">Parameters</Typography>
            <Card variant="outlined" sx={{ mt: 1 }}>
              <CardContent>
                {Object.entries(transformation.parameters).map(([key, value]) => (
                  <Typography key={key} variant="body2" component="div" sx={{ mb: 1 }}>
                    <strong>{key.replace(/_/g, ' ')}:</strong> {
                      Array.isArray(value) 
                        ? value.join(', ') 
                        : typeof value === 'object' 
                          ? JSON.stringify(value) 
                          : String(value)
                    }
                  </Typography>
                ))}
              </CardContent>
            </Card>
          </Box>
          
          {transformation.status === TransformationStatus.COMPLETED && transformation.result && (
            <Box sx={{ mt: 4 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item>
                  <Typography variant="h6">Result</Typography>
                </Grid>
                <Grid item sx={{ flexGrow: 1 }} />
                <Grid item>
                  {editMode ? (
                    <Button 
                      startIcon={<SaveIcon />} 
                      variant="contained" 
                      color="primary"
                      onClick={saveEditedContent}
                    >
                      Save
                    </Button>
                  ) : (
                    <Button 
                      startIcon={<EditIcon />} 
                      variant="outlined"
                      onClick={toggleEditMode}
                    >
                      Edit
                    </Button>
                  )}
                </Grid>
                <Grid item>
                  <Button 
                    startIcon={<DownloadIcon />} 
                    variant="outlined"
                    onClick={() => exportAsFile('txt')}
                  >
                    Export as TXT
                  </Button>
                </Grid>
                <Grid item>
                  <Button 
                    startIcon={<DownloadIcon />} 
                    variant="outlined"
                    onClick={() => exportAsFile('md')}
                  >
                    Export as MD
                  </Button>
                </Grid>
              </Grid>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ width: '100%' }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                  <Tabs value={tabValue} onChange={handleTabChange} aria-label="transformation view tabs">
                    <Tab label="Preview" id="transformation-tab-0" />
                    <Tab label="Raw Text" id="transformation-tab-1" />
                  </Tabs>
                </Box>
                
                <TabPanel value={tabValue} index={0}>
                  {editMode ? (
                    <TextField
                      fullWidth
                      multiline
                      rows={20}
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      variant="outlined"
                    />
                  ) : (
                    <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 1, minHeight: '300px' }}>
                      <ReactMarkdown>
                        {transformation.result}
                      </ReactMarkdown>
                    </Box>
                  )}
                </TabPanel>
                
                <TabPanel value={tabValue} index={1}>
                  {editMode ? (
                    <TextField
                      fullWidth
                      multiline
                      rows={20}
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      variant="outlined"
                    />
                  ) : (
                    <Box 
                      component="pre" 
                      sx={{ 
                        p: 2, 
                        border: '1px solid #e0e0e0', 
                        borderRadius: 1,
                        bgcolor: '#f5f5f5',
                        overflowX: 'auto',
                        minHeight: '300px',
                        fontFamily: 'monospace'
                      }}
                    >
                      {transformation.result}
                    </Box>
                  )}
                </TabPanel>
              </Box>
            </Box>
          )}
          
          {transformation.status === TransformationStatus.FAILED && (
            <Alert severity="error" sx={{ mt: 4 }}>
              Transformation failed. Please try again.
            </Alert>
          )}
        </Paper>
      )}
    </Container>
  );
};

export default TransformationDetail;