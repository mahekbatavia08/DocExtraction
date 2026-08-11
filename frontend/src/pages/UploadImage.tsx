import React, { useState } from 'react';
import { Box, Card, CardContent, Typography, Alert } from '@mui/material';
import { UploadCloud, Layers } from 'lucide-react';
import { MultiDocumentQueue } from '../components/MultiDocumentQueue';
import { TerminalLogs } from '../components/TerminalLogs';

export const UploadImage: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] Multi-Document OCR Engine Ready`
  ]);

  const handleFilesSelect = (fileList: FileList | File[]) => {
    const validFiles: File[] = [];
    Array.from(fileList).forEach(file => {
      if (file.type.startsWith('image/') || file.name.toLowerCase().endsWith('.pdf')) {
        validFiles.push(file);
      }
    });

    if (validFiles.length === 0) {
      setErrorMsg('Please select valid image or PDF document files.');
      return;
    }

    setErrorMsg(null);
    setSelectedFiles(prev => [...prev, ...validFiles]);
    setTerminalLogs(prev => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] Added ${validFiles.length} file(s) to queue. Total: ${selectedFiles.length + validFiles.length}`
    ]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelect(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
  };

  return (
    <Box sx={{ pb: 6, maxWidth: '1100px', mx: 'auto' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
          Multi-Document & Image OCR Engine
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Upload single or multiple document files (PNG, JPG, WEBP, PDF) for batch processing.
        </Typography>
      </Box>

      {errorMsg && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: '12px' }} onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {/* Drag & Drop Multi-File Card */}
      <Card sx={{ borderRadius: '20px', mb: 3 }}>
        <CardContent sx={{ p: 4 }}>
          <Box
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            sx={{
              border: '2px dashed',
              borderColor: dragActive ? '#10b981' : 'rgba(255, 255, 255, 0.15)',
              borderRadius: '16px',
              p: 5,
              textAlign: 'center',
              background: dragActive ? 'rgba(16, 185, 129, 0.08)' : 'rgba(0, 0, 0, 0.2)',
              transition: 'all 0.2s ease-in-out',
              cursor: 'pointer',
            }}
          >
            <input
              type="file"
              accept="image/*,.pdf"
              multiple
              id="multi-image-upload-input"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files && handleFilesSelect(e.target.files)}
            />
            <label htmlFor="multi-image-upload-input" style={{ cursor: 'pointer', width: '100%', display: 'block' }}>
              <Box sx={{ p: 2, borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)', width: 'fit-content', mx: 'auto', mb: 2 }}>
                <UploadCloud size={40} color="#10b981" />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                Drag & Drop Files Here, or Click to Select Multiple Documents
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                Supports PNG, JPG, JPEG, WEBP, and PDF files. Select multiple files at once.
              </Typography>
            </label>
          </Box>

          {/* Multi-Document Queue Manager */}
          <MultiDocumentQueue
            files={selectedFiles}
            onClearFiles={handleClearAll}
            onRemoveFile={handleRemoveFile}
          />
        </CardContent>
      </Card>

      {/* Terminal Step Logs */}
      <TerminalLogs logs={terminalLogs} />
    </Box>
  );
};
