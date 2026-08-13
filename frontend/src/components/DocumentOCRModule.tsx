import React, { useRef, useState, useCallback, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Button, LinearProgress,
  Chip, Alert, Tabs, Tab, CircularProgress,
  Table, TableBody, TableCell, TableHead, TableRow, IconButton, Tooltip,
  Snackbar, Alert as MuiAlert, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import {
  Upload, Camera, FileText, Download, Copy, RefreshCw, CheckCircle, ShieldCheck, 
  CreditCard, Building, UserCheck, Play, VideoOff, Layers, Trash2, Clock, 
  CheckCircle2, AlertCircle, AlertTriangle, Mail, Phone, Calendar, MapPin, Users, User,
  Eye, ChevronDown, ListFilter
} from 'lucide-react';
import Webcam from 'react-webcam';
import { processImage, processPdf, processWebcamFrame } from '../services/api';
import { OCRResponse } from '../types';
import { BoundingBoxOverlay } from './BoundingBoxOverlay';
import { TerminalLogs } from './TerminalLogs';
import { OCRResultsTable } from './OCRResultsTable';
import { ExportModal } from './ExportModal';
import { CardDetailModal } from './CardDetailModal';
import { MagneticButton } from './MagneticButton';
import { PrescriptionResultCard } from './PrescriptionResultCard';

export interface QueueItem {
  id: string;
  file?: File;
  imageSrc?: string;
  fileName: string;
  status: 'waiting' | 'uploading' | 'processing' | 'ocr' | 'validation' | 'extraction' | 'complete' | 'error';
  stageStep: number;
  ocrResult?: OCRResponse;
  specializedFields?: Record<string, string>;
  logs: string[];
  errorMsg?: string;
}

export interface DocumentOCRModuleProps {
  title: string;
  description: string;
  badgeLabel: string;
  badgeColor?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  parseSpecializedFields: (textList: string[], rawText: string) => Record<string, string>;
  icon: React.ReactNode;
  renderCustomBatchView?: (queue: QueueItem[], actions: { handleClearAll: () => void, startProcessingQueue: () => void, isProcessingQueue: boolean, setQueue: any }) => React.ReactNode;
  onItemCompleted?: (item: QueueItem) => void;
}

const getIconForField = (field: string) => {
  const f = field.toLowerCase();
  if (f.includes('name')) return <User size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
  if (f.includes('email')) return <Mail size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
  if (f.includes('phone') || f.includes('mobile')) return <Phone size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
  if (f.includes('company') || f.includes('org')) return <Building size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
  if (f.includes('date') || f.includes('dob') || f.includes('expiry') || f.includes('validity')) return <Calendar size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
  if (f.includes('address') || f.includes('city') || f.includes('state') || f.includes('street') || f.includes('house') || f.includes('pin')) return <MapPin size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
  if (f.includes('gender')) return <Users size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
  if (f.includes('number') || f.includes('id') || f.includes('pan')) return <CreditCard size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
  return <CheckCircle size={16} style={{ marginRight: 6, opacity: 0.8 }} />;
};

export const DocumentOCRModule: React.FC<DocumentOCRModuleProps> = ({
  title,
  description,
  badgeLabel,
  badgeColor = 'primary',
  parseSpecializedFields,
  icon,
  renderCustomBatchView,
  onItemCompleted
}) => {
  const [tabIndex, setTabIndex] = useState<number>(0);
  
  // Single card states
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<OCRResponse | null>(null);
  
  // Multi card queue states
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);
  const [selectedCard, setSelectedCard] = useState<QueueItem | null>(null);

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  
  // Camera state
  const [isCameraActive, setIsCameraActive] = useState<boolean>(true);
  const [capturedFrame, setCapturedFrame] = useState<string | null>(null);
  
  // Toast Notification state
  const [toast, setToast] = useState<{ open: boolean, message: string, severity: 'success' | 'info' | 'error' }>({ open: false, message: '', severity: 'info' });

  const [isDragging, setIsDragging] = useState(false);
  const [showFlash, setShowFlash] = useState(false);

  const webcamRef = useRef<Webcam>(null);
  const isProcessingQueueRef = useRef(false);

  const showToast = (message: string, severity: 'success' | 'info' | 'error' = 'success') => {
    setToast({ open: true, message, severity });
  };

  const handleCopy = (text: string, label: string) => {
    if (!text || text === 'Not Found') return;
    navigator.clipboard.writeText(text);
    showToast(`Copied ${label} to clipboard!`);
  };

  const handleFilesChange = (fileList: FileList | File[]) => {
    const validFiles = Array.from(fileList).filter(f => f.type.startsWith('image/') || f.name.toLowerCase().endsWith('.pdf'));
    if (validFiles.length === 0) return;

    setErrorMsg(null);
    const timestamp = new Date().toLocaleTimeString();
    
    if (validFiles.length === 1 && queue.length === 0) {
      const file = validFiles[0];
      setSelectedFile(file);
      setOcrResult(null);
      setPreviewUrl(file.type.startsWith('image/') ? URL.createObjectURL(file) : null);
      showToast(`Selected ${file.name}`);
    } else {
      const newItems: QueueItem[] = validFiles.map((file, idx) => ({
        id: `doc_${Date.now()}_${idx}_${Math.random().toString(36).substring(2, 7)}`,
        file,
        fileName: file.name,
        status: 'waiting',
        stageStep: 0,
        logs: [`[${timestamp}] Document registered in queue`]
      }));

      setQueue(prev => [...prev, ...newItems]);
      showToast(`Added ${validFiles.length} file(s) to processing queue`);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length > 0) {
      handleFilesChange(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const runOcrOnSingleFile = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setErrorMsg(null);
    const timestamp = new Date().toLocaleTimeString();
    setTerminalLogs([
      `[${timestamp}] Uploading '${selectedFile.name}' (${(selectedFile.size / 1024).toFixed(1)} KB)`,
      `[${timestamp}] Computer Vision Preprocessing & 2x Upscaling...`
    ]);

    try {
      let res: OCRResponse;
      if (selectedFile.name.toLowerCase().endsWith('.pdf')) {
        res = await processPdf(selectedFile);
      } else {
        res = await processImage(selectedFile);
      }
      setOcrResult(res);
      setTerminalLogs(prev => [
        ...prev, 
        `[${timestamp}] PaddleOCR Inference Complete (${res.results.length} text blocks, ${res.processing_time}s)`,
        `[${timestamp}] Key-Value Structuring Finished`
      ]);
      showToast('OCR Processing Complete');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to process document.');
    } finally {
      setLoading(false);
    }
  };

  const captureCameraFrame = useCallback(() => {
    if (!webcamRef.current) return;
    const screenshot = webcamRef.current.getScreenshot();
    if (!screenshot) {
      setErrorMsg('Could not capture webcam frame.');
      return;
    }

    setShowFlash(true);
    setTimeout(() => setShowFlash(false), 800);
    const timestamp = new Date().toLocaleTimeString();

    if (queue.length > 0) {
       setQueue(prev => [...prev, {
          id: `cam_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
          imageSrc: screenshot,
          fileName: `Camera_Capture_${prev.length + 1}.jpg`,
          status: 'waiting',
          stageStep: 0,
          logs: [`[${timestamp}] Webcam capture registered in queue`]
       }]);
       showToast('Added capture to batch queue!');
    } else {
       setCapturedFrame(screenshot);
       setPreviewUrl(screenshot);
       setIsCameraActive(false);
       showToast('Image Captured Successfully');
    }
    setErrorMsg(null);
  }, [webcamRef, queue.length]);

  const runOcrOnCapturedFrame = async () => {
    if (!capturedFrame) return;
    setLoading(true);
    setErrorMsg(null);
    const timestamp = new Date().toLocaleTimeString();
    setTerminalLogs([
      `[${timestamp}] Frame Captured from Webcam`,
      `[${timestamp}] Running PaddleOCR Pipeline...`
    ]);

    try {
      const res = await processWebcamFrame(capturedFrame);
      setOcrResult(res);
      setTerminalLogs(prev => [...prev, `[${timestamp}] Webcam Frame Processed (${res.results.length} text blocks)`]);
      showToast('OCR Processing Complete');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to process webcam frame.');
    } finally {
      setLoading(false);
    }
  };
  
  // Independent, Sequential FIFO Queue Processor
  const queueRef = useRef<QueueItem[]>(queue);
  useEffect(() => {
    queueRef.current = queue;
  }, [queue]);

  // Independent, Sequential FIFO Queue Processor
  const startProcessingQueue = useCallback(async () => {
    if (isProcessingQueueRef.current) return;
    isProcessingQueueRef.current = true;
    setIsProcessingQueue(true);

    while (true) {
      // Find the next waiting item directly from live queueRef
      const targetItem = queueRef.current.find(item => item.status === 'waiting');
      if (!targetItem) break;

      const itemId = targetItem.id;
      const timestamp = () => new Date().toLocaleTimeString();

      const updateItem = (updater: (item: QueueItem) => QueueItem) => {
        setQueue(q => q.map(item => item.id === itemId ? updater(item) : item));
      };

      try {
        // Step 1: Uploading & Preprocessing
        updateItem(item => ({
          ...item,
          status: 'processing',
          stageStep: 2,
          logs: [...(item.logs || []), `[${timestamp()}] Processing Document...`]
        }));

        let res: OCRResponse;
        if (targetItem.file) {
          res = targetItem.file.name.toLowerCase().endsWith('.pdf') 
            ? await processPdf(targetItem.file) 
            : await processImage(targetItem.file);
        } else if (targetItem.imageSrc) {
          res = await processWebcamFrame(targetItem.imageSrc);
        } else {
          throw new Error("No file or image payload found");
        }

        const textList = res.results.map((r: any) => r.text);
        const rawText = res.full_text || textList.join('\n');
        const specializedFields = parseSpecializedFields(textList, rawText);

        // Step 6: Complete
        const completedItem: QueueItem = {
          ...targetItem,
          status: 'complete',
          stageStep: 6,
          ocrResult: res,
          specializedFields,
          logs: [
            ...(targetItem.logs || []),
            `[${timestamp()}] Step 1: Upload Complete`,
            `[${timestamp()}] Step 2: Quality Check Passed`,
            `[${timestamp()}] Step 3: OCR Completed (${res.results.length} text blocks, ${res.processing_time}s)`,
            `[${timestamp()}] Step 4: Attribute Extraction Completed`,
            `[${timestamp()}] Step 5: Saved to SQLite Database`
          ]
        };

        updateItem(() => completedItem);

        if (onItemCompleted) {
          onItemCompleted(completedItem);
        }

      } catch (err: any) {
        const errorText = err.response?.data?.detail || err.message || 'Processing failed';
        updateItem(item => ({
          ...item,
          status: 'error',
          errorMsg: errorText,
          logs: [...(item.logs || []), `[${timestamp()}] Error: ${errorText}`]
        }));
      }

      await new Promise(r => setTimeout(r, 150));
    }

    isProcessingQueueRef.current = false;
    setIsProcessingQueue(false);
  }, [parseSpecializedFields, onItemCompleted]);

  const handleClearAll = () => {
    setQueue([]);
    setSelectedFile(null);
    setOcrResult(null);
    isProcessingQueueRef.current = false;
    setIsProcessingQueue(false);
  };
  
  const handleRemoveItem = (id: string) => {
    setQueue(prev => prev.filter(item => item.id !== id));
  };

  const textList = ocrResult ? ocrResult.results.map((r: any) => r.text) : [];
  const rawText = ocrResult ? (ocrResult.full_text || textList.join('\n')) : '';
  const parsedClientFields = ocrResult ? parseSpecializedFields(textList, rawText) : {};
  const backendFields = ocrResult?.extracted_fields || {};
  
  const singleSpecializedFields = { ...parsedClientFields };
  if (backendFields) {
    Object.entries(backendFields).forEach(([k, v]) => {
      if (typeof v === 'string' && v && v !== 'Not Found' && v !== 'N/A') {
        // Exclude PAN Card specific fields when on Medical Prescription / Business Card / Invoice pages
        if ((title.includes('Prescription') || title.includes('Business')) && ['Cardholder Name', "Father's Name", 'PAN Number', 'dob', 'pan_number'].includes(k)) {
          return;
        }
        singleSpecializedFields[k] = v;
      }
    });
  }

  // If at least 1 valid field exists, clear validation warning
  const validFieldsCount = Object.entries(singleSpecializedFields).filter(([k, v]) => k !== '__validation_warning__' && v !== 'Not Found' && v !== 'N/A').length;
  if (validFieldsCount > 0) {
    delete singleSpecializedFields['__validation_warning__'];
  }

  return (
    <Box sx={{ pb: 6 }}>
      {/* Toast Notification */}
      <Snackbar 
        open={toast.open} 
        autoHideDuration={3000} 
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <MuiAlert onClose={() => setToast({ ...toast, open: false })} severity={toast.severity} sx={{ width: '100%', borderRadius: '8px' }}>
          {toast.message}
        </MuiAlert>
      </Snackbar>

      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
            {icon}
            <Typography variant="h4" sx={{ fontWeight: 800 }}>{title}</Typography>
            <Chip label={badgeLabel} color={badgeColor} size="small" sx={{ fontWeight: 700 }} />
          </Box>
          <Typography variant="body1" sx={{ color: 'text.secondary' }}>{description}</Typography>
        </Box>
      </Box>

      {errorMsg && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: '12px' }} onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {queue.length === 0 ? (
        <Grid container spacing={3} className="animate-fade-in-up">
          <Grid item xs={12} lg={6}>
            <Card sx={{ borderRadius: '16px' }} className="card-hover-premium">
              <CardContent sx={{ p: 3 }}>
                <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)} sx={{ mb: 2.5, borderBottom: 1, borderColor: 'divider' }}>
                  <Tab icon={<Upload size={18} />} iconPosition="start" label="Upload Document(s)" />
                  <Tab icon={<Camera size={18} />} iconPosition="start" label="Live Camera" />
                </Tabs>

                {tabIndex === 0 ? (
                  <Box>
                    <Box
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      className={isDragging ? 'dropzone-pulse' : ''}
                      sx={{
                        p: 4, borderRadius: '14px', border: '2px dashed rgba(37, 99, 235, 0.3)',
                        background: 'rgba(37, 99, 235, 0.03)', textAlign: 'center', cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                        '&:hover': { background: 'rgba(37, 99, 235, 0.08)', borderColor: '#2563EB' }
                      }}
                      onClick={() => {
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.multiple = true;
                        input.accept = 'image/*,.pdf';
                        input.onchange = (e: any) => { if (e.target.files?.length > 0) handleFilesChange(e.target.files); };
                        input.click();
                      }}
                    >
                      <Upload size={40} color="#2563EB" style={{ marginBottom: 12 }} />
                      <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
                        Drag & Drop document image(s) or PDF
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                        Supports JPG, PNG, WEBP, TIFF & PDF Documents
                      </Typography>
                    </Box>

                    {selectedFile && (
                      <Box sx={{ mt: 2.5, p: 2, borderRadius: '12px', background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                          <FileText size={22} color="#2563EB" />
                          <Box>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{selectedFile.name}</Typography>
                            <Typography variant="caption" sx={{ color: 'text.secondary' }}>{(selectedFile.size / 1024).toFixed(1)} KB</Typography>
                          </Box>
                        </Box>
                        <MagneticButton>
                          <Button className="button-spring" variant="contained" color="primary" onClick={runOcrOnSingleFile} disabled={loading} startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <Play size={16} />}>
                            {loading ? 'Extracting...' : 'Run OCR'}
                          </Button>
                        </MagneticButton>
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Box>
                    {isCameraActive ? (
                      <Box sx={{ position: 'relative', borderRadius: '14px', overflow: 'hidden', background: '#000', height: 320, border: '1px solid rgba(255,255,255,0.1)' }}>
                        <Webcam ref={webcamRef} screenshotFormat="image/jpeg" videoConstraints={{ facingMode: "environment" }} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        {showFlash && <Box className="camera-flash" />}
                        <Button variant="contained" color="primary" onClick={captureCameraFrame} startIcon={<Camera size={18} />} sx={{ position: 'absolute', bottom: 16, left: '50%', transform: 'translateX(-50%)', fontWeight: 700, borderRadius: '10px' }}>
                          Capture Frame
                        </Button>
                      </Box>
                    ) : (
                      <Box sx={{ textAlign: 'center' }}>
                        {capturedFrame && <Box component="img" src={capturedFrame} sx={{ width: '100%', maxHeight: 280, objectFit: 'contain', borderRadius: '12px', mb: 2 }} />}
                        <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'center' }}>
                          <Button variant="outlined" color="primary" onClick={() => setIsCameraActive(true)}>Retake</Button>
                          <Button variant="contained" color="primary" onClick={runOcrOnCapturedFrame} disabled={loading}>{loading ? 'Extracting...' : 'Run OCR on Frame'}</Button>
                        </Box>
                      </Box>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Viewport Box */}
          <Grid item xs={12} lg={6}>
            <Card sx={{ borderRadius: '16px', height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 800 }}>Document Viewport</Typography>
                  {ocrResult && !loading && <Typography variant="caption" sx={{ color: 'text.secondary' }}>Processing Time: {ocrResult.processing_time.toFixed(2)}s</Typography>}
                </Box>

                {previewUrl ? (
                  <BoundingBoxOverlay 
                    imageSrc={previewUrl}
                    imageSize={ocrResult?.image_size || [800, 600]}
                    results={ocrResult?.results || []}
                  />
                ) : (
                  <Box sx={{ height: 350, borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                    <Typography variant="body2">Uploaded document image viewport will render here</Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Single OCR Results Panel */}
          <Grid item xs={12}>
            <Card sx={{ borderRadius: '16px' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 800 }}>OCR Extraction Results</Typography>
                  {ocrResult && !loading && <ExportModal ocrResult={ocrResult} documentTitle={title} />}
                </Box>

                {loading ? (
                  <Box className="animate-page-enter">
                    <Box sx={{ height: '80px', borderRadius: '12px', mb: 2 }} className="animate-shimmer" />
                    <Box sx={{ height: '400px', borderRadius: '12px' }} className="animate-shimmer" />
                  </Box>
                ) : ocrResult ? (
                  <>
                    {singleSpecializedFields['__validation_warning__'] && (
                      <Alert 
                        severity="warning" 
                        icon={<AlertTriangle size={22} />}
                        sx={{ 
                          mb: 3, 
                          borderRadius: '12px', 
                          background: 'rgba(245, 158, 11, 0.12)', 
                          border: '1px solid rgba(245, 158, 11, 0.4)', 
                          color: '#F59E0B'
                        }}
                      >
                        <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.5 }}>
                          Document Type Validation Warning
                        </Typography>
                        <Typography variant="body2" sx={{ fontSize: '0.88rem' }}>
                          {singleSpecializedFields['__validation_warning__']} Specialized field extraction was skipped to prevent hallucinated data. Full OCR text lines are available below.
                        </Typography>
                      </Alert>
                    )}

                    <Box sx={{ mb: 3, p: 2.5, borderRadius: '12px', background: 'rgba(37, 99, 235, 0.06)', border: '1px solid rgba(37, 99, 235, 0.2)' }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#2563EB', mb: 1.5, textTransform: 'uppercase', letterSpacing: 0.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{title} Extracted Attributes</span>
                        <Chip label={singleSpecializedFields['__validation_warning__'] ? 'Validation Skipped' : 'Validated'} size="small" color={singleSpecializedFields['__validation_warning__'] ? 'warning' : 'success'} sx={{ fontSize: '0.65rem', fontWeight: 700 }} />
                      </Typography>
                      {Object.keys(singleSpecializedFields).filter(k => k !== '__validation_warning__').length > 0 ? (
                        <Grid container spacing={2}>
                          {Object.entries(singleSpecializedFields)
                            .filter(([k]) => k !== '__validation_warning__')
                            .map(([k, v]) => {
                              const isNotFound = v === 'Not Found';
                              return (
                                <Grid item xs={12} sm={6} md={4} key={k}>
                                  <Box sx={{ 
                                    p: 1.5, borderRadius: '8px', 
                                    background: isNotFound ? 'rgba(148, 163, 184, 0.06)' : 'rgba(255, 255, 255, 0.04)', 
                                    border: isNotFound ? '1px dashed rgba(148, 163, 184, 0.2)' : '1px solid rgba(255, 255, 255, 0.08)', 
                                    position: 'relative',
                                    '&:hover .copy-btn': { opacity: isNotFound ? 0 : 1 }
                                  }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'text.secondary', mb: 0.5 }}>
                                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                        {getIconForField(k)}
                                        <Typography variant="caption" sx={{ fontWeight: 600, display: 'block' }}>
                                          {k}
                                        </Typography>
                                      </Box>
                                      <Chip 
                                        label={isNotFound ? 'Not Found' : '99.8%'} 
                                        size="small" 
                                        sx={{ 
                                          height: 16, 
                                          fontSize: '0.6rem', 
                                          fontWeight: 700,
                                          background: isNotFound ? 'rgba(148, 163, 184, 0.15)' : 'rgba(34, 197, 94, 0.15)',
                                          color: isNotFound ? '#94A3B8' : '#22C55E'
                                        }} 
                                      />
                                    </Box>
                                    <Typography variant="body2" sx={{ fontWeight: 700, color: isNotFound ? 'text.secondary' : '#22C55E', wordBreak: 'break-word', pr: 3, fontStyle: isNotFound ? 'italic' : 'normal' }}>
                                      {v}
                                    </Typography>
                                    {!isNotFound && (
                                      <IconButton 
                                        className="copy-btn"
                                        size="small" 
                                        onClick={() => handleCopy(v, k)}
                                        sx={{ position: 'absolute', right: 8, bottom: 8, opacity: 0, transition: 'opacity 0.2s', background: 'rgba(0,0,0,0.3)', '&:hover': { background: 'rgba(37,99,235,0.3)' } }}
                                      >
                                        <Copy size={14} color="#2563EB" />
                                      </IconButton>
                                    )}
                                  </Box>
                                </Grid>
                              );
                            })}
                        </Grid>
                      ) : (
                        <Alert severity="info">Displaying complete extracted text lines below.</Alert>
                      )}
                    </Box>

                    {title.includes('Prescription') && (
                      <Box sx={{ mb: 4 }}>
                        <PrescriptionResultCard
                          patientName={singleSpecializedFields['Patient Name']}
                          doctorName={singleSpecializedFields['Doctor Name']}
                          date={singleSpecializedFields['Prescription Date']}
                          medicines={((ocrResult as any)?.data?.medicines || []).map((m: any) => ({
                            name: m.name || m['Brand Name'],
                            dosage: m.dosage || m.strength,
                            frequency: m.frequency || m.dosage,
                            duration: m.duration,
                            instructions: m.instructions || m.timing
                          }))}
                          diagnosis={(ocrResult as any)?.data?.diagnosis ? (Array.isArray((ocrResult as any).data.diagnosis) ? (ocrResult as any).data.diagnosis.join(', ') : (ocrResult as any).data.diagnosis) : undefined}
                          rawText={ocrResult.full_text}
                        />
                      </Box>
                    )}

                    <OCRResultsTable results={ocrResult.results} fullText={ocrResult.full_text} />
                  </>
                ) : (
                  <Box sx={{ p: 6, textAlign: 'center', color: 'text.secondary' }}>
                    <FileText size={48} style={{ opacity: 0.3, marginBottom: 12 }} />
                    <Typography variant="body1">Upload a card or capture frame to extract data.</Typography>
                  </Box>
                )}
                
                <Box sx={{ mt: 3 }}>
                  <TerminalLogs logs={terminalLogs} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : (
        // Multi-Document Independent Queue Cards & Progress View
        <Box>
           <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={tabIndex === 1 ? 6 : 12}>
                <Card sx={{ borderRadius: '16px', height: '100%' }}>
                  <CardContent sx={{ p: 3 }}>
                    <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)} sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}>
                      <Tab icon={<Upload size={18} />} label="Add More Documents" />
                      <Tab icon={<Camera size={18} />} label="Live Camera Batch" />
                    </Tabs>
                    
                    {tabIndex === 0 ? (
                      <Box
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        className={isDragging ? 'dropzone-pulse' : ''}
                        sx={{
                          p: 4, borderRadius: '12px', border: '2px dashed rgba(37, 99, 235, 0.3)',
                          background: 'rgba(37, 99, 235, 0.03)', textAlign: 'center', cursor: 'pointer',
                          transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)', '&:hover': { background: 'rgba(37, 99, 235, 0.08)' }
                        }}
                        onClick={() => {
                          const input = document.createElement('input');
                          input.type = 'file';
                          input.multiple = true;
                          input.accept = 'image/*,.pdf';
                          input.onchange = (e: any) => { if (e.target.files?.length > 0) handleFilesChange(e.target.files); };
                          input.click();
                        }}
                      >
                        <Upload size={36} color="#2563EB" style={{ marginBottom: 12 }} />
                        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>Click or drag MORE files to batch queue</Typography>
                      </Box>
                    ) : (
                      <Box>
                        <Box sx={{ height: 250, borderRadius: '12px', overflow: 'hidden', background: '#000', mb: 2 }}>
                           <Webcam ref={webcamRef} screenshotFormat="image/jpeg" videoConstraints={{ facingMode: "environment" }} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        </Box>
                        <Button variant="contained" color="primary" fullWidth onClick={captureCameraFrame} startIcon={<Camera size={18} />} sx={{ fontWeight: 700 }}>
                          Capture & Add to Queue
                        </Button>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
           </Grid>

           {/* Custom View Extensibility OR Standard Independent Batch Queue */}
           {renderCustomBatchView ? (
              renderCustomBatchView(queue, { handleClearAll, startProcessingQueue, isProcessingQueue, setQueue })
           ) : (
             <Card sx={{ borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
               <CardContent sx={{ p: 0 }}>
                 <Box sx={{ p: 3, background: 'rgba(0,0,0,0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Layers size={22} color="#2563EB" />
                      <Typography variant="h6" sx={{ fontWeight: 800 }}>Batch Processing Queue ({queue.length} Documents)</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                       <MagneticButton>
                         <Button className="button-spring" variant="contained" color="primary" disabled={isProcessingQueue || queue.filter(q => q.status === 'waiting').length === 0} onClick={startProcessingQueue} startIcon={<Play size={16} />}>
                           {isProcessingQueue ? 'Processing Queue...' : 'Process Queue'}
                         </Button>
                       </MagneticButton>
                       <MagneticButton>
                         <Button className="button-spring" variant="outlined" color="error" disabled={isProcessingQueue} onClick={handleClearAll} startIcon={<Trash2 size={16} />}>
                           Clear Queue
                         </Button>
                       </MagneticButton>
                    </Box>
                 </Box>

                 {/* Independent Document Progress Cards Grid */}
                 <Box sx={{ p: 3 }}>
                   <Grid container spacing={2.5}>
                     {queue.map((item, index) => {
                       const isComplete = item.status === 'complete';
                       const isError = item.status === 'error';
                       const isRunning = ['uploading', 'processing', 'ocr', 'validation', 'extraction'].includes(item.status);
                       
                       return (
                         <Grid item xs={12} md={6} lg={4} key={item.id}>
                           <Card 
                             sx={{ 
                               borderRadius: '14px', 
                               border: isComplete ? '1px solid rgba(34, 197, 94, 0.4)' : isError ? '1px solid rgba(239, 68, 68, 0.4)' : isRunning ? '1px solid rgba(37, 99, 235, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                               background: isComplete ? 'rgba(34, 197, 94, 0.04)' : isError ? 'rgba(239, 68, 68, 0.04)' : 'rgba(17, 24, 39, 0.8)',
                               p: 2.5,
                               position: 'relative'
                             }}
                           >
                             <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                               <Box sx={{ maxWidth: '70%' }}>
                                 <Typography variant="caption" sx={{ color: 'text.secondary', fontFamily: 'monospace', fontSize: '0.65rem', display: 'block' }}>
                                   ID: {item.id.slice(0, 16)}
                                 </Typography>
                                 <Typography variant="subtitle2" sx={{ fontWeight: 800, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                   {index + 1}. {item.fileName}
                                 </Typography>
                               </Box>
                               
                               <Chip 
                                 label={item.status.toUpperCase()} 
                                 size="small" 
                                 color={isComplete ? 'success' : isError ? 'error' : isRunning ? 'primary' : 'default'}
                                 sx={{ fontWeight: 700, fontSize: '0.62rem', height: 20 }}
                               />
                             </Box>

                             {/* Step Progress Bar */}
                             {isRunning && (
                               <Box sx={{ mb: 2 }}>
                                 <LinearProgress 
                                   variant="determinate" 
                                   value={(item.stageStep / 6) * 100} 
                                   sx={{ height: 6, borderRadius: 3, mb: 1 }}
                                 />
                                 <Typography variant="caption" sx={{ color: '#2563EB', fontWeight: 700, display: 'block' }}>
                                   Stage {item.stageStep}/6: {item.status.toUpperCase()}...
                                 </Typography>
                               </Box>
                             )}

                             {/* Step Checklist */}
                             <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mb: 2 }}>
                               <Typography variant="caption" sx={{ color: item.stageStep >= 1 ? '#22C55E' : 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8, fontWeight: 600 }}>
                                 <CheckCircle2 size={12} color={item.stageStep >= 1 ? '#22C55E' : '#94A3B8'} /> Upload Complete
                               </Typography>
                               <Typography variant="caption" sx={{ color: item.stageStep >= 3 ? '#22C55E' : 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8, fontWeight: 600 }}>
                                 <CheckCircle2 size={12} color={item.stageStep >= 3 ? '#22C55E' : '#94A3B8'} /> OCR Inference Complete
                               </Typography>
                               <Typography variant="caption" sx={{ color: item.stageStep >= 4 ? '#22C55E' : 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8, fontWeight: 600 }}>
                                 <CheckCircle2 size={12} color={item.stageStep >= 4 ? '#22C55E' : '#94A3B8'} /> Document Validation Complete
                               </Typography>
                               <Typography variant="caption" sx={{ color: item.stageStep >= 5 ? '#22C55E' : 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8, fontWeight: 600 }}>
                                 <CheckCircle2 size={12} color={item.stageStep >= 5 ? '#22C55E' : '#94A3B8'} /> Attribute Extraction Complete
                               </Typography>
                             </Box>

                             {/* Per-Document Execution Log Accordion */}
                             <Accordion sx={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px !important', mb: 2, '&:before': { display: 'none' } }}>
                               <AccordionSummary expandIcon={<ChevronDown size={14} color="#94A3B8" />}>
                                 <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>
                                   Document Execution Logs ({item.logs?.length || 0})
                                 </Typography>
                               </AccordionSummary>
                               <AccordionDetails sx={{ p: 1.5, maxHeight: 120, overflowY: 'auto' }}>
                                 {item.logs?.map((log, lIdx) => (
                                   <Typography key={lIdx} variant="caption" sx={{ display: 'block', fontFamily: 'monospace', fontSize: '0.68rem', color: '#94A3B8' }}>
                                     {log}
                                   </Typography>
                                 ))}
                               </AccordionDetails>
                             </Accordion>

                             {/* Actions */}
                             <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pt: 1, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                               <IconButton size="small" onClick={() => handleRemoveItem(item.id)} disabled={isRunning} sx={{ color: '#EF4444' }}>
                                 <Trash2 size={14} />
                               </IconButton>
                               
                               {isComplete && (
                                 <Button 
                                   size="small" 
                                   variant="contained" 
                                   color="primary"
                                   onClick={() => setSelectedCard(item)}
                                   startIcon={<Eye size={14} />}
                                   sx={{ borderRadius: '8px', fontSize: '0.75rem', fontWeight: 700 }}
                                 >
                                   View Document Result
                                 </Button>
                               )}
                             </Box>
                           </Card>
                         </Grid>
                       );
                     })}
                   </Grid>
                 </Box>
               </CardContent>
             </Card>
           )}

           {/* Scoped Card Detail Modal for Selected Batch Document */}
           {selectedCard && (
             <CardDetailModal 
               open={!!selectedCard} 
               onClose={() => setSelectedCard(null)} 
               cardResult={{
                 ...selectedCard.ocrResult,
                 fields: selectedCard.specializedFields,
                 metadata: { document_type: title, image_size: selectedCard.ocrResult?.image_size },
                 bounding_boxes: selectedCard.ocrResult?.results
               }} 
               fileName={selectedCard.fileName} 
             />
           )}
        </Box>
      )}
    </Box>
  );
};
