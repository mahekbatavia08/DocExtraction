import React, { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Box, Typography,
  TextField, Button, Chip, IconButton, Alert, Tooltip, Divider, Grid
} from '@mui/material';
import { ShieldAlert, CheckCircle2, Save, X, Eye, AlertTriangle, HelpCircle } from 'lucide-react';
import { reviewDBDocumentField } from '../services/api';
import { DBDocument, ExtractedField } from '../types';
import { soundFx } from '../utils/soundEffects';

interface HumanReviewModalProps {
  open: boolean;
  document: DBDocument | null;
  fieldToReview: ExtractedField | null;
  onClose: () => void;
  onSave: (updatedDoc: DBDocument) => void;
}

export const HumanReviewModal: React.FC<HumanReviewModalProps> = ({
  open,
  document,
  fieldToReview,
  onClose,
  onSave
}) => {
  const [correctedVal, setCorrectedVal] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (fieldToReview) {
      setCorrectedVal(fieldToReview.field_value || '');
      setErrorMsg(null);
    }
  }, [fieldToReview]);

  if (!document || !fieldToReview) return null;

  const confPercent = Math.round((fieldToReview.confidence || 0.5) * 100);
  const tierColor = confPercent >= 90 ? '#10B981' : confPercent >= 70 ? '#3B82F6' : confPercent >= 50 ? '#F59E0B' : '#EF4444';
  const tierLabel = confPercent >= 90 ? 'Verified (90-100%)' : confPercent >= 70 ? 'High Confidence (70-89%)' : confPercent >= 50 ? 'Needs Review (50-69%)' : 'Uncertain (<50%)';

  const handleApprove = async () => {
    soundFx.playClick();
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const res = await reviewDBDocumentField(document.id, fieldToReview.field_name, correctedVal, true);
      onSave(res.document);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to approve field correction.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          background: '#0F172A',
          color: '#F8FAFC',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        }
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ p: 1, borderRadius: '12px', background: 'rgba(245, 158, 11, 0.2)', color: '#F59E0B' }}>
            <ShieldAlert size={22} />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              Human Verification & Review
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              Document ID #{document.id} • {document.original_filename}
            </Typography>
          </Box>
        </Box>
        <IconButton onClick={onClose} size="small" sx={{ color: 'text.secondary' }}>
          <X size={20} />
        </IconButton>
      </DialogTitle>

      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.08)' }} />

      <DialogContent sx={{ py: 3 }}>
        {errorMsg && (
          <Alert severity="error" sx={{ mb: 3, borderRadius: '12px' }}>
            {errorMsg}
          </Alert>
        )}

        {/* Document Image Bounding Box Crop Overlay */}
        {document.image_data && (
          <Box sx={{ mb: 3, p: 1.5, background: 'rgba(0, 0, 0, 0.4)', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.08)', textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: '#94A3B8', fontWeight: 600, display: 'block', mb: 1 }}>
              Visual Document Context Crop (Field Bounding Box)
            </Typography>
            <Box
              component="img"
              src={document.image_data}
              alt="Document Snippet"
              sx={{
                maxHeight: 180,
                maxWidth: '100%',
                objectFit: 'contain',
                borderRadius: '8px',
                border: '2px solid rgba(59, 130, 246, 0.6)'
              }}
            />
          </Box>
        )}

        {/* Field Details */}
        <Box sx={{ mb: 3, p: 2, background: 'rgba(255, 255, 255, 0.03)', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={6}>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>Field Name</Typography>
              <Typography variant="body1" sx={{ fontWeight: 800, color: '#38BDF8' }}>
                {fieldToReview.field_name}
              </Typography>
            </Grid>
            <Grid item xs={6} sx={{ textAlign: 'right' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, display: 'block' }}>Extraction Tier</Typography>
              <Chip
                label={tierLabel}
                size="small"
                sx={{
                  fontWeight: 800,
                  fontSize: '0.72rem',
                  background: `${tierColor}22`,
                  color: tierColor,
                  border: `1px solid ${tierColor}44`
                }}
              />
            </Grid>
          </Grid>
        </Box>

        {/* User Editable Value */}
        <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1, color: '#F8FAFC' }}>
          Corrected / Verified Value:
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={2}
          value={correctedVal}
          onChange={(e) => setCorrectedVal(e.target.value)}
          placeholder="Enter corrected value..."
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.04)',
              color: '#F8FAFC',
              fontWeight: 700
            }
          }}
        />
      </DialogContent>

      <DialogActions sx={{ p: 2.5, gap: 1.5, background: 'rgba(0, 0, 0, 0.2)' }}>
        <Button onClick={onClose} sx={{ color: 'text.secondary', fontWeight: 700 }}>
          Cancel
        </Button>
        <Button
          variant="contained"
          color="primary"
          startIcon={<Save size={18} />}
          disabled={isSubmitting}
          onClick={handleApprove}
          sx={{
            borderRadius: '12px',
            px: 3,
            fontWeight: 800,
            background: 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)'
          }}
        >
          {isSubmitting ? 'Saving...' : 'Approve & Save Field'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
