import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Card, CardContent, Typography, Button, LinearProgress, Chip, Alert,
  Grid, Accordion, AccordionSummary, AccordionDetails, IconButton, Tooltip, Paper
} from '@mui/material';
import {
  FileText, CheckCircle2, AlertCircle, Clock, Trash2, ChevronDown, Play, RotateCcw, Eye, Layers
} from 'lucide-react';
import { OCRResponse } from '../types';
import { processImage, processPdf } from '../services/api';
import { OCRResultsTable } from './OCRResultsTable';
import { ExportModal } from './ExportModal';
import { BoundingBoxOverlay } from './BoundingBoxOverlay';
import { SkeletonLoader } from './SkeletonLoader';

export interface DocumentQueueItem {
  id: string;
  file: File;
  previewUrl: string | null;
  status: 'waiting' | 'processing' | 'complete' | 'error';
  ocrResult: OCRResponse | null;
  errorMsg: string | null;
  progress: number;
}

interface MultiDocumentQueueProps {
  files: File[];
  onClearFiles: () => void;
  onRemoveFile: (index: number) => void;
}

export const MultiDocumentQueue: React.FC<MultiDocumentQueueProps> = ({
  files,
  onClearFiles,
  onRemoveFile
}) => {
  const [queue, setQueue] = useState<DocumentQueueItem[]>([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState<boolean>(false);
  const [expandedId, setExpandedId] = useState<string | false>(false);

  // Synchronize incoming files with queue state
  useEffect(() => {
    setQueue(prev => {
      const existingMap = new Map(prev.map(item => [item.file.name + item.file.size, item]));
      return files.map((file, idx) => {
        const key = file.name + file.size;
        if (existingMap.has(key)) {
          return existingMap.get(key)!;
        }
        return {
          id: `doc_${idx}_${Date.now()}`,
          file,
          previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
          status: 'waiting',
          ocrResult: null,
          errorMsg: null,
          progress: 0
        };
      });
    });
  }, [files]);

  const queueRef = useRef<DocumentQueueItem[]>(queue);
  useEffect(() => {
    queueRef.current = queue;
  }, [queue]);

  const isProcessingQueueRef = useRef(false);

  // Controlled Sequential Queue Processing Engine (Processes 1 document at a time to prevent RAM spikes)
  const startProcessingQueue = async () => {
    if (isProcessingQueueRef.current) return;
    isProcessingQueueRef.current = true;
    setIsProcessingQueue(true);

    while (true) {
      const targetItem = queueRef.current.find(item => item.status === 'waiting');
      if (!targetItem) break;

      const itemId = targetItem.id;
      setQueue(q => q.map(item => item.id === itemId ? { ...item, status: 'processing', progress: 30 } : item));
      setExpandedId(itemId);

      try {
        let res: OCRResponse;
        if (targetItem.file.name.toLowerCase().endsWith('.pdf')) {
          res = await processPdf(targetItem.file);
        } else {
          res = await processImage(targetItem.file);
        }

        setQueue(q => q.map(item => item.id === itemId ? {
          ...item,
          status: 'complete',
          ocrResult: res,
          progress: 100
        } : item));
      } catch (err: any) {
        setQueue(q => q.map(item => item.id === itemId ? {
          ...item,
          status: 'error',
          errorMsg: err.response?.data?.detail || err.message || 'Failed to process document.',
          progress: 100
        } : item));
      }

      await new Promise(r => setTimeout(r, 200));
    }

    isProcessingQueueRef.current = false;
    setIsProcessingQueue(false);
  };

  const completedCount = queue.filter(q => q.status === 'complete').length;
  const processingCount = queue.filter(q => q.status === 'processing').length;
  const waitingCount = queue.filter(q => q.status === 'waiting').length;

  if (queue.length === 0) return null;

  return (
    <Box sx={{ width: '100%', mt: 3 }}>
      {/* Queue Batch Status Bar */}
      <Card sx={{ borderRadius: '16px', mb: 3, background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(2, 6, 23, 0.95) 100%)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Layers size={22} color="#10b981" />
              <Typography variant="h6" sx={{ fontWeight: 800 }}>
                Multi-Document Batch Processing Queue ({queue.length} Files)
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
              <Chip label={`${completedCount} Complete`} color="success" size="small" sx={{ fontWeight: 700 }} />
              {processingCount > 0 && <Chip label={`${processingCount} Processing...`} color="primary" size="small" sx={{ fontWeight: 700 }} />}
              {waitingCount > 0 && <Chip label={`${waitingCount} Waiting`} color="default" size="small" sx={{ fontWeight: 700 }} />}

              <Button
                variant="contained"
                color="success"
                disabled={isProcessingQueue || waitingCount === 0}
                onClick={startProcessingQueue}
                startIcon={<Play size={16} />}
                sx={{ borderRadius: '8px', fontWeight: 700 }}
              >
                {isProcessingQueue ? 'Processing Queue...' : `Process ${waitingCount} Queued Files`}
              </Button>

              <Button
                variant="outlined"
                color="error"
                disabled={isProcessingQueue}
                onClick={onClearFiles}
                startIcon={<Trash2 size={16} />}
                sx={{ borderRadius: '8px', fontWeight: 600 }}
              >
                Clear All
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Queue Items List */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {queue.map((item, index) => {
          const isExpanded = expandedId === item.id;

          return (
            <Accordion
              key={item.id}
              expanded={isExpanded}
              onChange={(_, expanded) => setExpandedId(expanded ? item.id : false)}
              sx={{
                borderRadius: '14px !important',
                background: item.status === 'processing' ? 'rgba(16, 185, 129, 0.05)' : '#020617',
                border: item.status === 'processing' ? '1px solid #10b981' : '1px solid rgba(255, 255, 255, 0.08)',
                overflow: 'hidden',
                '&:before': { display: 'none' }
              }}
            >
              <AccordionSummary expandIcon={<ChevronDown color="#94a3b8" />}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', pr: 2, gap: 2, flexWrap: 'wrap' }}>
                  {/* Left: Thumbnail & Document Title */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {item.previewUrl ? (
                      <img src={item.previewUrl} alt={item.file.name} style={{ width: 44, height: 44, borderRadius: 6, objectFit: 'cover' }} />
                    ) : (
                      <Box sx={{ width: 44, height: 44, borderRadius: '8px', background: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <FileText size={22} color="#a855f7" />
                      </Box>
                    )}

                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#f8fafc' }}>
                        Document {index + 1}: {item.file.name}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                        {(item.file.size / (1024 * 1024)).toFixed(2)} MB | {item.file.type || 'PDF Document'}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Right: Status Badges & Quick Metadata */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {item.status === 'waiting' && (
                      <Chip icon={<Clock size={14} />} label="Waiting in Queue" size="small" variant="outlined" sx={{ fontWeight: 600 }} />
                    )}

                    {item.status === 'processing' && (
                      <Chip icon={<Layers size={14} color="#10b981" />} label="Processing OCR..." color="primary" size="small" sx={{ fontWeight: 700 }} />
                    )}

                    {item.status === 'complete' && item.ocrResult && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Chip icon={<CheckCircle2 size={14} />} label="✓ OCR Complete" color="success" size="small" sx={{ fontWeight: 700 }} />
                        <Typography variant="caption" sx={{ color: '#10b981', fontWeight: 700 }}>
                          {item.ocrResult.processing_time.toFixed(2)}s | {item.ocrResult.detected_blocks_count} blocks
                        </Typography>
                      </Box>
                    )}

                    {item.status === 'error' && (
                      <Chip icon={<AlertCircle size={14} />} label="✗ Processing Error" color="error" size="small" sx={{ fontWeight: 700 }} />
                    )}

                    <Tooltip title="Remove Document from Queue">
                      <IconButton size="small" onClick={(e) => { e.stopPropagation(); onRemoveFile(index); }}>
                        <Trash2 size={16} color="#64748b" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              </AccordionSummary>

              <AccordionDetails sx={{ borderTop: '1px solid rgba(255, 255, 255, 0.05)', pt: 3 }}>
                {item.status === 'processing' && (
                  <Box sx={{ mb: 2 }}>
                    <LinearProgress color="success" sx={{ height: 6, borderRadius: 3 }} />
                    <SkeletonLoader type="table" />
                  </Box>
                )}

                {item.status === 'error' && (
                  <Alert severity="error" sx={{ borderRadius: '10px' }}>
                    {item.errorMsg || 'Failed to process document.'}
                  </Alert>
                )}

                {item.status === 'complete' && item.ocrResult && (
                  <Box>
                    {/* Header Controls for Individual Document */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 700, color: '#10b981' }}>
                        Extracted Data for {item.file.name}
                      </Typography>
                      <ExportModal ocrResult={item.ocrResult} documentTitle={item.file.name} />
                    </Box>

                    <Grid container spacing={3}>
                      {/* Left: Redesigned OCR Results Table */}
                      <Grid item xs={12} lg={7}>
                        <OCRResultsTable
                          results={item.ocrResult.results}
                          fullText={item.ocrResult.full_text}
                        />
                      </Grid>

                      {/* Right: Bounding Box Overlay & Image Viewport */}
                      <Grid item xs={12} lg={5}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                          Document Visual Viewport & Bounding Boxes
                        </Typography>
                        <BoundingBoxOverlay
                          imageSrc={item.ocrResult.annotated_image_base64 || item.previewUrl || ''}
                          imageSize={item.ocrResult.image_size || [800, 600]}
                          results={item.ocrResult.results}
                        />
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          );
        })}
      </Box>
    </Box>
  );
};
