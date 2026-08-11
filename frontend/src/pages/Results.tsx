import React, { useState } from 'react';
import { Box, Grid, Card, CardContent, Typography, Button, Chip, Snackbar, Alert, Divider } from '@mui/material';
import { ArrowLeft, FileText } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { OCRResponse } from '../types';
import { BoundingBoxOverlay } from '../components/BoundingBoxOverlay';
import { PANDetailsCard } from '../components/PANDetailsCard';
import { TerminalLogs } from '../components/TerminalLogs';
import { OCRResultsTable } from '../components/OCRResultsTable';
import { ExportModal } from '../components/ExportModal';

export const Results: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const ocrData: OCRResponse | undefined = location.state?.ocrData;
  const originalImage: string | undefined = location.state?.originalImage;

  const [selectedBoxId, setSelectedBoxId] = useState<number | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  if (!ocrData) {
    return (
      <Box sx={{ py: 10, textAlign: 'center' }}>
        <Typography variant="h5" sx={{ mb: 2, color: 'text.secondary' }}>
          No active OCR document loaded.
        </Typography>
        <Button variant="contained" startIcon={<ArrowLeft size={18} />} onClick={() => navigate('/upload-image')}>
          Upload a Document
        </Button>
      </Box>
    );
  }

  const imageSrc = ocrData.annotated_image_base64 || originalImage || '';

  return (
    <Box sx={{ pb: 6 }}>
      {/* Top Bar */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
            Document Extraction Output
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>
            Source: {ocrData.image_name || 'Document'} | Detected Lines: {ocrData.detected_blocks_count} | Processing Time: {ocrData.processing_time.toFixed(2)}s
          </Typography>
        </Box>

        {/* Export Toolbar */}
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<ArrowLeft size={18} />}
            onClick={() => navigate(-1)}
            sx={{ borderRadius: '8px', textTransform: 'none' }}
          >
            Back
          </Button>

          <ExportModal ocrResult={ocrData} documentTitle={ocrData.image_name || 'Document'} />
        </Box>
      </Box>

      {/* Main Split Layout */}
      <Grid container spacing={3}>
        {/* Left Side: Extracted Output Card & Redesigned Table */}
        <Grid item xs={12} lg={6}>
          {ocrData.pan_details && (
            <PANDetailsCard panDetails={ocrData.pan_details} />
          )}

          {ocrData.extracted_fields && Object.keys(ocrData.extracted_fields).length > 0 && (
            <Card sx={{ borderRadius: '16px', mb: 3, background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, color: '#10b981', display: 'flex', alignItems: 'center', gap: 1 }}>
                  <FileText size={20} /> Extracted Document Key-Value Fields
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(ocrData.extracted_fields).map(([key, value]) => (
                    <Grid item xs={12} sm={6} key={key}>
                      <Box sx={{ p: 1.5, borderRadius: '8px', background: 'rgba(2, 6, 23, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
                        <Typography variant="caption" sx={{ color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, display: 'block' }}>
                          {key}
                        </Typography>
                        <Typography variant="body1" sx={{ fontWeight: 700, color: '#f8fafc', mt: 0.2 }}>
                          {value}
                        </Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          )}

          <Card sx={{ borderRadius: '16px', mb: 3 }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <FileText size={22} color="#10b981" /> Extracted Text Lines
                </Typography>
                <Chip
                  label={`${ocrData.results.length} text lines`}
                  color="success"
                  variant="outlined"
                  size="small"
                />
              </Box>

              <Divider sx={{ borderColor: 'rgba(255,255,255,0.08)', mb: 2.5 }} />

              {/* Redesigned OCR Results Table */}
              <OCRResultsTable
                results={ocrData.results}
                fullText={ocrData.full_text}
              />
            </CardContent>
          </Card>

          {/* Terminal Logs */}
          <TerminalLogs
            logs={[
              `Image Name      : ${ocrData.image_name || 'Document'}`,
              `Image Size      : ${ocrData.image_size[0]}x${ocrData.image_size[1]} px`,
              `OCR Time        : ${ocrData.processing_time.toFixed(2)} sec`,
              `Detected Lines  : ${ocrData.detected_blocks_count}`,
              `Overall Conf    : ${ocrData.overall_confidence ? `${ocrData.overall_confidence}%` : 'N/A'}`,
              `Memory Usage    : ${ocrData.memory_usage_mb} MB`
            ]}
          />
        </Grid>

        {/* Right Side: Visual Document Preview with Green Bounding Boxes */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ borderRadius: '16px', height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                Document Visual Overlay
              </Typography>
              <BoundingBoxOverlay
                imageSrc={imageSrc}
                imageSize={ocrData.image_size}
                results={ocrData.results}
                selectedId={selectedBoxId}
                onSelectBox={(id) => setSelectedBoxId(id)}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Toast Notification */}
      <Snackbar open={!!toastMsg} autoHideDuration={3000} onClose={() => setToastMsg(null)}>
        <Alert severity="success" sx={{ borderRadius: '12px' }} onClose={() => setToastMsg(null)}>
          {toastMsg}
        </Alert>
      </Snackbar>
    </Box>
  );
};
