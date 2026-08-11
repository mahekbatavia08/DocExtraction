import React, { useState } from 'react';
import {
  Menu, MenuItem, ListItemIcon, ListItemText, Snackbar, Alert, Button, CircularProgress
} from '@mui/material';
import { Download, FileText, FileSpreadsheet, FileJson, FileCode, Check, AlertTriangle } from 'lucide-react';
import { OCRResponse } from '../types';
import { exportOCRData, ExportFormat } from '../utils/exportUtils';

interface ExportModalProps {
  ocrResult: OCRResponse;
  documentTitle?: string;
}

export const ExportModal: React.FC<ExportModalProps> = ({ ocrResult, documentTitle = 'Document' }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(null);
  const [toastInfo, setToastInfo] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleExport = async (format: ExportFormat) => {
    handleClose();
    setExportingFormat(format);

    const result = await exportOCRData({
      ocrResult,
      documentTitle,
      format
    });

    setExportingFormat(null);
    setToastInfo({
      open: true,
      message: result.success ? `✓ ${result.message}` : `✗ ${result.message}`,
      severity: result.success ? 'success' : 'error'
    });
  };

  return (
    <>
      <Button
        variant="contained"
        color="success"
        size="small"
        startIcon={exportingFormat ? <CircularProgress size={16} color="inherit" /> : <Download size={16} />}
        onClick={handleClick}
        disabled={!ocrResult || !ocrResult.results || ocrResult.results.length === 0}
        sx={{ fontWeight: 700, borderRadius: '8px' }}
      >
        {exportingFormat ? `Exporting ${exportingFormat.toUpperCase()}...` : 'Export Document'}
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          elevation: 4,
          sx: {
            mt: 1,
            borderRadius: '12px',
            minWidth: 200,
            background: '#0f172a',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#f8fafc'
          }
        }}
      >
        <MenuItem onClick={() => handleExport('csv')} sx={{ py: 1, '&:hover': { background: 'rgba(16, 185, 129, 0.15)' } }}>
          <ListItemIcon sx={{ color: '#10b981' }}>
            <FileSpreadsheet size={18} />
          </ListItemIcon>
          <ListItemText primary="Export as CSV (.csv)" primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: 600 }} />
        </MenuItem>

        <MenuItem onClick={() => handleExport('xlsx')} sx={{ py: 1, '&:hover': { background: 'rgba(16, 185, 129, 0.15)' } }}>
          <ListItemIcon sx={{ color: '#38bdf8' }}>
            <FileSpreadsheet size={18} />
          </ListItemIcon>
          <ListItemText primary="Export as Excel (.xlsx)" primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: 600 }} />
        </MenuItem>

        <MenuItem onClick={() => handleExport('pdf')} sx={{ py: 1, '&:hover': { background: 'rgba(16, 185, 129, 0.15)' } }}>
          <ListItemIcon sx={{ color: '#f43f5e' }}>
            <FileText size={18} />
          </ListItemIcon>
          <ListItemText primary="Export as PDF (.pdf)" primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: 600 }} />
        </MenuItem>

        <MenuItem onClick={() => handleExport('txt')} sx={{ py: 1, '&:hover': { background: 'rgba(16, 185, 129, 0.15)' } }}>
          <ListItemIcon sx={{ color: '#a855f7' }}>
            <FileCode size={18} />
          </ListItemIcon>
          <ListItemText primary="Export as Plain Text (.txt)" primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: 600 }} />
        </MenuItem>

        <MenuItem onClick={() => handleExport('json')} sx={{ py: 1, '&:hover': { background: 'rgba(16, 185, 129, 0.15)' } }}>
          <ListItemIcon sx={{ color: '#f59e0b' }}>
            <FileJson size={18} />
          </ListItemIcon>
          <ListItemText primary="Export as JSON (.json)" primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: 600 }} />
        </MenuItem>
      </Menu>

      <Snackbar
        open={toastInfo.open}
        autoHideDuration={4000}
        onClose={() => setToastInfo(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          severity={toastInfo.severity}
          onClose={() => setToastInfo(prev => ({ ...prev, open: false }))}
          sx={{ borderRadius: '10px', fontWeight: 600 }}
        >
          {toastInfo.message}
        </Alert>
      </Snackbar>
    </>
  );
};
