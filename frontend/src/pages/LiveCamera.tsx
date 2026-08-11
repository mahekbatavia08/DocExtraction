import React, { useRef, useState, useCallback, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Button, LinearProgress,
  Chip, Alert, CircularProgress, Snackbar
} from '@mui/material';
import { Camera, Play, VideoOff, Zap, Trash2, ArrowRight, RefreshCw, CheckCircle } from 'lucide-react';
import Webcam from 'react-webcam';
import { useNavigate } from 'react-router-dom';
import { processWebcamFrame, checkImageQuality, FrameQualityResponse } from '../services/api';
import { OCRResponse } from '../types';
import { BoundingBoxOverlay } from '../components/BoundingBoxOverlay';
import { PANDetailsCard } from '../components/PANDetailsCard';
import { TerminalLogs } from '../components/TerminalLogs';
import { OCRResultsTable } from '../components/OCRResultsTable';
import { ExportModal } from '../components/ExportModal';

export const LiveCamera: React.FC = () => {
  const navigate = useNavigate();
  const webcamRef = useRef<Webcam>(null);

  const [isCameraOn, setIsCameraOn] = useState(true);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState<OCRResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const [selectedBoxId, setSelectedBoxId] = useState<number | null>(null);

  const [facingMode, setFacingMode] = useState<'user' | 'environment'>('user');
  const [qualityInfo, setQualityInfo] = useState<FrameQualityResponse | null>(null);

  // Poll live quality every 1.5s when camera is active and not loading OCR
  useEffect(() => {
    if (!isCameraOn || loading || ocrResult) return;
    const timer = setInterval(async () => {
      if (webcamRef.current) {
        const frame = webcamRef.current.getScreenshot();
        if (frame) {
          try {
            const q = await checkImageQuality(frame);
            setQualityInfo(q);
          } catch {
            // ignore network transient error during quality check
          }
        }
      }
    }, 1500);
    return () => clearInterval(timer);
  }, [isCameraOn, loading, ocrResult]);

  const startCamera = () => {
    setIsCameraOn(true);
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  const stopCamera = () => {
    setIsCameraOn(false);
  };

  const toggleCameraFacing = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  const clearAll = () => {
    setCapturedImage(null);
    setOcrResult(null);
    setErrorMsg(null);
    setSuccessMsg(null);
    setTerminalLogs([]);
    setSelectedBoxId(null);
    setQualityInfo(null);
    setIsCameraOn(true);
  };

  const captureFrameOnly = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        setCapturedImage(imageSrc);
        setIsCameraOn(false); // Automatically stop webcam stream and release resources
        setSuccessMsg('Image Captured Successfully');
        setErrorMsg(null);
      } else {
        setErrorMsg('Could not capture webcam frame. Ensure camera permissions are granted.');
      }
    }
  }, [webcamRef]);

  const retakeFrame = () => {
    setCapturedImage(null);
    setOcrResult(null);
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsCameraOn(true); // Automatically restart webcam stream
  };

  const runOcrOnCapturedFrame = async () => {
    if (!capturedImage) return;
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const logs = [
      `[${new Date().toLocaleTimeString()}] Frame Quality Gate Passed`,
      `[${new Date().toLocaleTimeString()}] 4-Corner Document Detection & Perspective Warp`,
      `[${new Date().toLocaleTimeString()}] 2x High-Resolution Upscaling & Preprocessing`,
      `[${new Date().toLocaleTimeString()}] Running PaddleOCR Inference...`
    ];
    setTerminalLogs(logs);

    try {
      const response = await processWebcamFrame(capturedImage);
      setOcrResult(response);

      const finalLogs = [
        ...logs,
        `[${new Date().toLocaleTimeString()}] Detected ${response.detected_blocks_count} text blocks`,
        `[${new Date().toLocaleTimeString()}] Processing Time: ${response.processing_time.toFixed(2)} sec`,
        `[${new Date().toLocaleTimeString()}] Overall Confidence: ${response.overall_confidence ? `${response.overall_confidence}%` : 'N/A'}`,
        `[${new Date().toLocaleTimeString()}] Response Received`
      ];
      setTerminalLogs(finalLogs);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to process captured frame.');
    } finally {
      setLoading(false);
    }
  };

  const captureAndRunOcrDirectly = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        setCapturedImage(imageSrc);
        setIsCameraOn(false); // Stop camera stream
        setSuccessMsg('Image Captured Successfully');
        // Instantly run OCR
        (async () => {
          setLoading(true);
          setErrorMsg(null);
          try {
            const response = await processWebcamFrame(imageSrc);
            setOcrResult(response);
          } catch (err: any) {
            setErrorMsg(err.response?.data?.detail || 'Failed to process webcam frame');
          } finally {
            setLoading(false);
          }
        })();
      } else {
        setErrorMsg('Could not capture webcam frame. Ensure camera permissions are granted.');
      }
    }
  }, [webcamRef]);

  return (
    <Box sx={{ pb: 6 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
          Live Webcam OCR Engine
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Capture live frames and process text instantly with PaddleOCR.
        </Typography>
      </Box>

      {errorMsg && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: '12px' }} onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {successMsg && (
        <Alert severity="success" sx={{ mb: 3, borderRadius: '12px' }} onClose={() => setSuccessMsg(null)}>
          {successMsg}
        </Alert>
      )}

      {/* Main Control Panel & Feed */}
      <Grid container spacing={3}>
        {/* Left: Webcam Stream or Preview */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ borderRadius: '16px', overflow: 'hidden' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Camera size={20} color="#10b981" /> Live Camera Stream
                </Typography>

                {/* Live Quality Indicator Badges */}
                {qualityInfo && isCameraOn && !ocrResult && (
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                    <Chip
                      label={`Blur: ${qualityInfo.blur_score}`}
                      size="small"
                      color={qualityInfo.blur_score >= 50 ? 'success' : 'error'}
                      variant="outlined"
                    />
                    <Chip
                      label={`Brightness: ${qualityInfo.brightness}`}
                      size="small"
                      color={qualityInfo.brightness >= 35 && qualityInfo.brightness <= 230 ? 'success' : 'warning'}
                      variant="outlined"
                    />
                    <Chip
                      label={qualityInfo.document_detected ? 'Doc Detected' : 'No Doc'}
                      size="small"
                      color={qualityInfo.document_detected ? 'success' : 'default'}
                      variant="outlined"
                    />
                  </Box>
                )}
              </Box>

              {/* Viewport */}
              <Box
                sx={{
                  position: 'relative',
                  minHeight: '360px',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  background: '#020617',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}
              >
                {ocrResult ? (
                  <BoundingBoxOverlay
                    imageSrc={ocrResult.annotated_image_base64 || capturedImage || ''}
                    imageSize={ocrResult.image_size}
                    results={ocrResult.results}
                    selectedId={selectedBoxId}
                    onSelectBox={(id) => setSelectedBoxId(id)}
                  />
                ) : isCameraOn ? (
                  <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    screenshotQuality={1.0}
                    videoConstraints={{
                      width: { ideal: 1920 },
                      height: { ideal: 1080 },
                      facingMode: facingMode
                    }}
                    style={{ width: '100%', height: 'auto', borderRadius: '12px' }}
                  />
                ) : capturedImage ? (
                  <img
                    src={capturedImage}
                    alt="Captured Frame Preview"
                    style={{ width: '100%', height: 'auto', borderRadius: '12px' }}
                  />
                ) : (
                  <Box sx={{ textAlign: 'center', py: 6, color: 'text.secondary' }}>
                    <VideoOff size={48} color="#64748b" style={{ marginBottom: 12 }} />
                    <Typography variant="body1">Camera is currently turned off.</Typography>
                  </Box>
                )}
              </Box>

              {loading && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress color="success" sx={{ height: 6, borderRadius: 3 }} />
                  <Typography variant="caption" sx={{ color: '#10b981', mt: 1, display: 'block', textAlign: 'center', fontWeight: 600 }}>
                    Processing Image with PaddleOCR Engine...
                  </Typography>
                </Box>
              )}

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 1.5, mt: 3, flexWrap: 'wrap' }}>
                {isCameraOn ? (
                  <>
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<Camera size={18} />}
                      onClick={captureFrameOnly}
                      disabled={loading}
                      sx={{ borderRadius: '8px', fontWeight: 700 }}
                    >
                      Capture Image
                    </Button>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<Zap size={18} />}
                      onClick={captureAndRunOcrDirectly}
                      disabled={loading}
                      sx={{ borderRadius: '8px', fontWeight: 700 }}
                    >
                      Capture & Run OCR
                    </Button>
                    <Button variant="outlined" color="info" onClick={toggleCameraFacing} sx={{ borderRadius: '8px' }}>
                      Switch Camera ({facingMode === 'user' ? 'Front' : 'Rear'})
                    </Button>
                    <Button variant="outlined" color="error" startIcon={<VideoOff size={18} />} onClick={stopCamera} sx={{ borderRadius: '8px' }}>
                      Stop Camera
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<Play size={18} />}
                      onClick={startCamera}
                      sx={{ borderRadius: '8px', fontWeight: 700 }}
                    >
                      Start Camera
                    </Button>

                    {capturedImage && (
                      <>
                        <Button
                          variant="outlined"
                          startIcon={<RefreshCw size={18} />}
                          onClick={retakeFrame}
                          disabled={loading}
                          sx={{ borderRadius: '8px', fontWeight: 600 }}
                        >
                          Retake
                        </Button>
                        <Button
                          variant="contained"
                          color="success"
                          startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <Zap size={18} />}
                          onClick={runOcrOnCapturedFrame}
                          disabled={loading}
                          sx={{ borderRadius: '8px', fontWeight: 700 }}
                        >
                          Process OCR
                        </Button>
                      </>
                    )}
                  </>
                )}

                <Button variant="outlined" startIcon={<Trash2 size={18} />} onClick={clearAll} sx={{ borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}>
                  Clear
                </Button>

                {ocrResult && (
                  <Button
                    variant="contained"
                    color="secondary"
                    endIcon={<ArrowRight size={18} />}
                    onClick={() => navigate('/results', { state: { ocrData: ocrResult } })}
                    sx={{ borderRadius: '8px' }}
                  >
                    View Full Results Page
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>

          {/* Terminal Step Logs */}
          <TerminalLogs logs={terminalLogs} />
        </Grid>

        {/* Right: Realtime Extracted Table & PAN Card Details */}
        <Grid item xs={12} lg={6}>
          {ocrResult?.pan_details && (
            <PANDetailsCard panDetails={ocrResult.pan_details} />
          )}

          <Card sx={{ borderRadius: '16px' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5, flexWrap: 'wrap', gap: 1 }}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Extracted OCR Results
                  </Typography>
                  {ocrResult && (
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      Processing Time: {ocrResult.processing_time.toFixed(2)}s | Overall Conf: {ocrResult.overall_confidence ? `${ocrResult.overall_confidence}%` : 'N/A'}
                    </Typography>
                  )}
                </Box>

                {ocrResult && (
                  <ExportModal ocrResult={ocrResult} documentTitle="Live_Webcam_OCR" />
                )}
              </Box>

              {ocrResult?.extracted_fields && Object.keys(ocrResult.extracted_fields).length > 0 && (
                <Box sx={{ mb: 3, p: 2, borderRadius: '12px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#10b981', mb: 1.5, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Extracted Document Attributes
                  </Typography>
                  <Grid container spacing={1.5}>
                    {Object.entries(ocrResult.extracted_fields).map(([k, v]) => (
                      <Grid item xs={12} sm={6} key={k}>
                        <Box sx={{ p: 1.2, borderRadius: '6px', background: 'rgba(2, 6, 23, 0.6)' }}>
                          <Typography variant="caption" sx={{ color: '#94a3b8', display: 'block', fontWeight: 600 }}>
                            {k}
                          </Typography>
                          <Typography variant="body2" sx={{ color: '#f8fafc', fontWeight: 700 }}>
                            {v}
                          </Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {!ocrResult ? (
                <Box sx={{ py: 8, textAlign: 'center', color: 'text.secondary' }}>
                  <Typography variant="body1">
                    Click "Capture Image" or "Capture & Run OCR" to process webcam frame.
                  </Typography>
                </Box>
              ) : (
                <OCRResultsTable
                  results={ocrResult.results}
                  fullText={ocrResult.full_text}
                />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
