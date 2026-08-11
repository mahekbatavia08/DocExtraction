import React, { useState } from 'react';
import { Box, Card, CardContent, Typography, Alert } from '@mui/material';
import { FileText, UploadCloud } from 'lucide-react';
import { MultiDocumentQueue } from '../components/MultiDocumentQueue';
import { TerminalLogs } from '../components/TerminalLogs';

export const UploadPdf: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] PDF Multi-Document Engine Ready`
  ]);

  const handleFilesSelect = (fileList: FileList | File[]) => {
    const validFiles: File[] = [];
    Array.from(fileList).forEach(file => {
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf') || file.type.startsWith('image/')) {
        validFiles.push(file);
      }
    });

    if (validFiles.length === 0) {
      setErrorMsg('Please select valid PDF document files.');
      return;
    }

    setErrorMsg(null);
    setSelectedFiles(prev => [...prev, ...validFiles]);
    setTerminalLogs(prev => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] Added ${validFiles.length} PDF file(s) to queue. Total: ${selectedFiles.length + validFiles.length}`
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
          Upload PDF & Multi-Document OCR
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Process single or multiple PDF documents with batch queue control.
        </Typography>
      </Box>

      {errorMsg && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: '12px' }} onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      <Card sx={{ borderRadius: '20px', mb: 3 }}>
        <CardContent sx={{ p: 4 }}>
          <Box
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            sx={{
              border: '2px dashed',
              borderColor: dragActive ? '#a855f7' : 'rgba(255, 255, 255, 0.15)',
              borderRadius: '16px',
              p: 5,
              textAlign: 'center',
              background: dragActive ? 'rgba(168, 85, 247, 0.08)' : 'rgba(0, 0, 0, 0.2)',
              transition: 'all 0.2s ease-in-out',
              cursor: 'pointer',
            }}
          >
            <input
              type="file"
              accept=".pdf,application/pdf,image/*"
              multiple
              id="multi-pdf-upload-input"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files && handleFilesSelect(e.target.files)}
            />
            <label htmlFor="multi-pdf-upload-input" style={{ cursor: 'pointer', width: '100%', display: 'block' }}>
              <Box sx={{ p: 2, borderRadius: '50%', background: 'rgba(168, 85, 247, 0.15)', width: 'fit-content', mx: 'auto', mb: 2 }}>
                <FileText size={40} color="#a855f7" />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                Drag & Drop PDF Documents Here, or Click to Select Multiple PDFs
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                Supports scanned & digital PDF files and document images.
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

      <TerminalLogs logs={terminalLogs} />
    </Box>
  );
};
