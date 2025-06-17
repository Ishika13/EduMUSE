import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  Button,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemSecondaryAction,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import { PictureAsPdf, Refresh, MoreVert, Summarize, Quiz, Podcasts, MusicNote, Delete } from '@mui/icons-material';
import FileUpload from './FileUpload';

export default function FileList({ onFileSelect, selectedFile, onAction, isLoading }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingFile, setProcessingFile] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedActionFile, setSelectedActionFile] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://127.0.0.1:5000/files');
      
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files);
        setError(null);
      } else {
        setError('Failed to load files');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error fetching files:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = (result) => {
    // Refresh the file list when upload succeeds
    fetchFiles();
  };

  const handleUploadError = (errorMsg) => {
    // You could set a global error here if needed
    console.error('Upload failed:', errorMsg);
  };

  const handleActionMenuOpen = (event, file) => {
    setAnchorEl(event.currentTarget);
    setSelectedActionFile(file);
  };

  const handleActionMenuClose = () => {
    setAnchorEl(null);
    setSelectedActionFile(null);
  };

  const handleActionSelect = (action) => {
    if (selectedActionFile && onAction) {
      // Set the processing file to show loading indicator
      setProcessingFile(selectedActionFile.filename);
      
      // Call the action handler with isPdf=true since we're processing a whole file
      onAction(action, selectedActionFile.filename, true);
      
      // Close the menu
      handleActionMenuClose();
    }
  };

  const handleDeleteClick = () => {
    // Store the file to delete and open the confirmation dialog
    setFileToDelete(selectedActionFile);
    setDeleteDialogOpen(true);
    handleActionMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (!fileToDelete) return;

    try {
      setLoading(true);
      const response = await fetch('http://127.0.0.1:5000/delete-file', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: fileToDelete.filename }),
      });

      if (response.ok) {
        // If the file was deleted successfully, refresh the file list
        fetchFiles();
        
        // If the deleted file was selected, clear the selection
        if (selectedFile?.filename === fileToDelete.filename) {
          onFileSelect(null);
        }
      } else {
        const errorData = await response.json();
        setError(`Failed to delete file: ${errorData.error || 'Unknown error'}`);
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error deleting file:', err);
    } finally {
      setLoading(false);
      setDeleteDialogOpen(false);
      setFileToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setFileToDelete(null);
  };

  // Reset processingFile when isLoading becomes false
  useEffect(() => {
    if (!isLoading && processingFile) {
      setProcessingFile(null);
    }
  }, [isLoading]);

  useEffect(() => {
    fetchFiles();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchFiles}
          fullWidth
        >
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">
          Documents
        </Typography>
      </Box>
      
      {/* File Upload Component */}
      <FileUpload 
        onUploadSuccess={handleUploadSuccess}
        onUploadError={handleUploadError}
      />
      
      <Divider sx={{ mb: 1 }} />
      
      <List dense>
        {files.map((file) => (
          <ListItem 
            key={file.filename} 
            disablePadding
            secondaryAction={
              <Tooltip title="Generate AI Content">
                <IconButton 
                  edge="end" 
                  size="small"
                  onClick={(e) => handleActionMenuOpen(e, file)}
                  disabled={isLoading}
                >
                  <MoreVert fontSize="small" />
                </IconButton>
              </Tooltip>
            }
          >
            <ListItemButton
              selected={selectedFile?.filename === file.filename}
              onClick={() => onFileSelect(file)}
              disabled={isLoading && processingFile === file.filename}
            >
              <ListItemIcon>
                {isLoading && processingFile === file.filename ? (
                  <CircularProgress size={20} color="primary" />
                ) : file.type === 'podcast' ? (
                  <MusicNote color="primary" />
                ) : (
                  <PictureAsPdf color="error" />
                )}
              </ListItemIcon>
              <ListItemText 
                primary={file.filename}
                primaryTypographyProps={{
                  variant: 'body2',
                  noWrap: true
                }}
                secondary={isLoading && processingFile === file.filename ? "Processing..." : null}
                secondaryTypographyProps={{
                  variant: 'caption',
                  color: 'primary'
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
        
        {/* Action Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleActionMenuClose}
        >
          {/* Conditionally render menu items based on file type */}
          {selectedActionFile && selectedActionFile.type === 'pdf' ? [
            // PDF file actions
            <MenuItem key="summarize" onClick={() => handleActionSelect('summarize')}>
              <ListItemIcon>
                <Summarize fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Generate Summary" />
            </MenuItem>,
            <MenuItem key="assess" onClick={() => handleActionSelect('assess')}>
              <ListItemIcon>
                <Quiz fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Generate Assessment" />
            </MenuItem>,
            <MenuItem key="podcast" onClick={() => handleActionSelect('podcast')}>
              <ListItemIcon>
                <Podcasts fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="Generate Podcast" />
            </MenuItem>,
            <Divider key="divider" />,
            <MenuItem key="delete" onClick={handleDeleteClick}>
              <ListItemIcon>
                <Delete fontSize="small" color="error" />
              </ListItemIcon>
              <ListItemText primary="Delete File" primaryTypographyProps={{ color: 'error' }} />
            </MenuItem>
          ] : selectedActionFile && selectedActionFile.type === 'podcast' ? [
            // Podcast file actions
            <MenuItem key="delete" onClick={handleDeleteClick}>
              <ListItemIcon>
                <Delete fontSize="small" color="error" />
              </ListItemIcon>
              <ListItemText primary="Delete File" primaryTypographyProps={{ color: 'error' }} />
            </MenuItem>
          ] : null}
        </Menu>
      </List>

      {files.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
          No files found. Upload a PDF to get started.
        </Typography>
      )}

      <Button
        variant="text"
        startIcon={<Refresh />}
        onClick={fetchFiles}
        size="small"
        sx={{ mt: 1, width: '100%' }}
        disabled={loading}
      >
        Refresh List
      </Button>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">
          Confirm Delete
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-dialog-description">
            Are you sure you want to delete "{fileToDelete?.filename}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
