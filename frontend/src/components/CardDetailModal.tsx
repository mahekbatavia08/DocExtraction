import React from 'react';
import { Modal, Box, Typography, IconButton, Grid, Paper, Divider, Button } from '@mui/material';
import { X, Download } from 'lucide-react';
import { BoundingBoxOverlay } from './BoundingBoxOverlay';

interface CardDetailModalProps {
  open: boolean;
  onClose: () => void;
  cardResult: any;
  fileName: string;
}

export const CardDetailModal: React.FC<CardDetailModalProps> = ({ open, onClose, cardResult, fileName }) => {
  const [selectedBoxId, setSelectedBoxId] = useState<number | null>(null);

  if (!cardResult) return null;

  const fields = cardResult.fields || {};
  const docType = cardResult.metadata?.document_type || 'Business Card';
  const confidenceMap = cardResult.confidence || {};

  const handleExportIndividual = () => {
    const dataStr = JSON.stringify(cardResult, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${fileName}_ocr_result.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Exact Requested Display Order
  const fieldDisplayOrder = [
    { key: 'Name', label: 'NAME' },
    { key: 'Company', label: 'COMPANY' },
    { key: 'Designation', label: 'DESIGNATION' },
    { key: 'Phone', label: 'PHONE' },
    { key: 'Email', label: 'EMAIL' },
    { key: 'Website', label: 'WEBSITE' },
    { key: 'Address', label: 'ADDRESS' }
  ];

  return (
    <Modal open={open} onClose={onClose}>
      <Box sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '90vw',
        maxWidth: 1200,
        maxHeight: '90vh',
        bgcolor: '#0f172a',
        boxShadow: 24,
        borderRadius: 3,
        overflow: 'auto',
        p: 4,
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800 }}>
              {docType} Extraction Details
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              File: {fileName}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Button 
              variant="outlined" 
              startIcon={<Download size={16} />} 
              onClick={handleExportIndividual}
              sx={{ borderColor: 'rgba(255,255,255,0.2)', color: 'white' }}
            >
              Export JSON
            </Button>
            <IconButton onClick={onClose} sx={{ color: 'text.secondary' }}>
              <X />
            </IconButton>
          </Box>
        </Box>
        
        <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)', mb: 3 }} />

        <Grid container spacing={4}>
          <Grid item xs={12} md={5}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, color: '#10b981' }}>
              Extracted Structured Data
            </Typography>
            <Paper sx={{ p: 3, background: 'rgba(0,0,0,0.2)', borderRadius: 2, border: '1px solid rgba(255,255,255,0.05)' }}>
              {fieldDisplayOrder.map(({ key, label }) => {
                const value = fields[key] || fields[key.toLowerCase()];
                const conf = confidenceMap[key.toLowerCase()] || 0.95;
                const isNotFound = !value || value === 'Not Found';

                return (
                  <Box 
                    key={key} 
                    sx={{ 
                      mb: 2.2, 
                      p: 1.2, 
                      borderRadius: '8px', 
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid rgba(255, 255, 255, 0.04)',
                      transition: 'all 0.2s ease',
                      '&:hover': { background: 'rgba(37, 99, 235, 0.1)', borderColor: 'rgba(37, 99, 235, 0.3)' }
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 700, letterSpacing: '0.05em' }}>
                        {label}
                      </Typography>
                      {!isNotFound && (
                        <Typography variant="caption" sx={{ color: '#10b981', fontWeight: 600, fontSize: '0.7rem' }}>
                          Confidence: {Math.round(conf * 100)}%
                        </Typography>
                      )}
                    </Box>
                    <Typography variant="body1" sx={{ fontWeight: 600, color: isNotFound ? '#94A3B8' : '#F8FAFC' }}>
                      {isNotFound ? 'Not Found' : String(value)}
                    </Typography>
                  </Box>
                );
              })}
            </Paper>
          </Grid>
          <Grid item xs={12} md={7}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, color: '#6366f1' }}>
              Document Viewport
            </Typography>
            <Box sx={{ border: '1px solid rgba(255,255,255,0.1)', borderRadius: 2, overflow: 'hidden' }}>
              <BoundingBoxOverlay 
                imageSrc={cardResult.annotated_image_base64 || ''}
                imageSize={cardResult.metadata?.image_size || [800, 600]}
                results={cardResult.bounding_boxes || cardResult.raw_ocr || []}
                selectedId={selectedBoxId}
                onSelectBox={(id) => setSelectedBoxId(id)}
              />
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Modal>
  );
};
