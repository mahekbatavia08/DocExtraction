import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Box, Typography,
  Button, Chip, Grid, Table, TableBody, TableCell, TableHead, TableRow,
  IconButton, Tabs, Tab, Alert, Divider, Card, CardContent
} from '@mui/material';
import {
  X, Download, Trash2, Clock, CheckCircle2, ShieldCheck, FileText,
  Copy, FileJson, FileSpreadsheet, User, Building, Mail, Phone, Globe, MapPin, Calendar, CreditCard
} from 'lucide-react';
import { DBDocument } from '../types';

interface DocumentDetailModalProps {
  document: DBDocument | null;
  open: boolean;
  onClose: () => void;
  onDelete?: (id: number) => void;
}

export const DocumentDetailModal: React.FC<DocumentDetailModalProps> = ({
  document,
  open,
  onClose,
  onDelete
}) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  if (!document) return null;

  const handleCopyRawText = () => {
    if (document.raw_ocr_text) {
      navigator.clipboard.writeText(document.raw_ocr_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(document, null, 2));
    const downloadAnchor = window.document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `${document.original_filename}_db_record.json`);
    window.document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleExportCSV = () => {
    const fields = document.fields || [];
    let csvContent = "Field Name,Field Value,Confidence\n";
    fields.forEach(f => {
      csvContent += `"${f.field_name}","${f.field_value.replace(/"/g, '""')}",${f.confidence}\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${document.original_filename}_fields.csv`);
    window.document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: '20px',
          background: 'rgba(15, 29, 33, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(20, 184, 166, 0.2)',
          color: '#F8FAFC',
          maxHeight: '90vh'
        }
      }}
    >
      <DialogTitle sx={{ m: 0, p: 2.5, borderBottom: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ p: 1, borderRadius: '10px', background: 'rgba(20, 184, 166, 0.2)', color: '#2DD4BF', border: '1px solid rgba(20, 184, 166, 0.4)' }}>
            <FileText size={22} />
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.1rem' }}>
              {document.original_filename}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', gap: 1.5, alignItems: 'center' }}>
              <span>DB ID: #{document.id}</span>
              <span>•</span>
              <span>{document.upload_timestamp}</span>
            </Typography>
          </Box>
        </Box>
        <IconButton onClick={onClose} sx={{ color: 'text.secondary', '&:hover': { color: '#F8FAFC' } }}>
          <X size={20} />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 3, borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
        {/* Top Badges */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={3}>
            <Box sx={{ p: 1.5, borderRadius: '12px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>Document Type</Typography>
              <Chip label={document.document_type} size="small" color="primary" sx={{ fontWeight: 700, fontSize: '0.75rem' }} />
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box sx={{ p: 1.5, borderRadius: '12px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>OCR Confidence</Typography>
              <Typography variant="body2" sx={{ fontWeight: 800, color: document.overall_confidence > 0.8 ? '#10B981' : '#F59E0B' }}>
                {Math.round(document.overall_confidence * 100)}%
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box sx={{ p: 1.5, borderRadius: '12px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>Processing Time</Typography>
              <Typography variant="body2" sx={{ fontWeight: 700, color: '#60A5FA', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Clock size={14} /> {document.processing_time}s
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Box sx={{ p: 1.5, borderRadius: '12px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>Masking Security</Typography>
              <Chip label="Masked & Compliant" size="small" color="success" icon={<ShieldCheck size={14} />} sx={{ fontWeight: 700, fontSize: '0.7rem' }} />
            </Box>
          </Grid>
        </Grid>

        {/* Original Document Preview if available */}
        {document.image_data && (
          <Box sx={{ mb: 3, textAlign: 'center', p: 2, background: 'rgba(0, 0, 0, 0.3)', borderRadius: '14px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 1, fontWeight: 700 }}>ORIGINAL DOCUMENT PREVIEW</Typography>
            <Box component="img" src={document.image_data} alt="Document Preview" sx={{ maxHeight: 220, maxWidth: '100%', borderRadius: '10px', objectFit: 'contain' }} />
          </Box>
        )}

        {/* Navigation Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'rgba(255, 255, 255, 0.1)', mb: 2 }}>
          <Tabs value={tabIndex} onChange={(_, val) => setTabIndex(val)} textColor="inherit" indicatorColor="primary">
            <Tab label={`Extracted Fields (${document.fields?.length || 0})`} sx={{ fontWeight: 700, fontSize: '0.85rem' }} />
            <Tab label="Raw OCR Text" sx={{ fontWeight: 700, fontSize: '0.85rem' }} />
            <Tab label={`Audit Logs (${document.logs?.length || 0})`} sx={{ fontWeight: 700, fontSize: '0.85rem' }} />
          </Tabs>
        </Box>

        {/* Tab 0: Extracted Fields & Contact Card */}
        {tabIndex === 0 && (
          <Box>
            {document.contact && (
              <Card sx={{ mb: 2.5, background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(124, 58, 237, 0.1) 100%)', border: '1px solid rgba(37, 99, 235, 0.3)', borderRadius: '14px' }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="subtitle2" sx={{ color: '#60A5FA', fontWeight: 800, mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <User size={16} /> Extracted Contact Information
                  </Typography>
                  <Grid container spacing={1.5}>
                    {document.contact.name && <Grid item xs={6} sm={4}><Typography variant="caption" sx={{ color: 'text.secondary' }}>Name</Typography><Typography variant="body2" sx={{ fontWeight: 700 }}>{document.contact.name}</Typography></Grid>}
                    {document.contact.company && <Grid item xs={6} sm={4}><Typography variant="caption" sx={{ color: 'text.secondary' }}>Company</Typography><Typography variant="body2" sx={{ fontWeight: 700 }}>{document.contact.company}</Typography></Grid>}
                    {document.contact.designation && <Grid item xs={6} sm={4}><Typography variant="caption" sx={{ color: 'text.secondary' }}>Designation</Typography><Typography variant="body2" sx={{ fontWeight: 700 }}>{document.contact.designation}</Typography></Grid>}
                    {document.contact.email && <Grid item xs={6} sm={4}><Typography variant="caption" sx={{ color: 'text.secondary' }}>Email</Typography><Typography variant="body2" sx={{ fontWeight: 700, color: '#38BDF8' }}>{document.contact.email}</Typography></Grid>}
                    {document.contact.phone && <Grid item xs={6} sm={4}><Typography variant="caption" sx={{ color: 'text.secondary' }}>Phone</Typography><Typography variant="body2" sx={{ fontWeight: 700 }}>{document.contact.phone}</Typography></Grid>}
                    {document.contact.address && <Grid item xs={12}><Typography variant="caption" sx={{ color: 'text.secondary' }}>Address</Typography><Typography variant="body2" sx={{ fontWeight: 600 }}>{document.contact.address}</Typography></Grid>}
                  </Grid>
                </CardContent>
              </Card>
            )}

            {document.fields && document.fields.length > 0 ? (
              <Table size="small" sx={{ '& .MuiTableCell-root': { borderColor: 'rgba(255, 255, 255, 0.08)', color: '#F8FAFC' } }}>
                <TableHead>
                  <TableRow sx={{ background: 'rgba(255, 255, 255, 0.04)' }}>
                    <TableCell sx={{ fontWeight: 700 }}>Field Name</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Extracted Value</TableCell>
                    <TableCell sx={{ fontWeight: 700, textAlign: 'right' }}>Confidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {document.fields.map((field, idx) => (
                    <TableRow key={idx} sx={{ '&:hover': { background: 'rgba(255, 255, 255, 0.03)' } }}>
                      <TableCell sx={{ fontWeight: 600, color: '#94A3B8' }}>{field.field_name}</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontFamily: 'monospace', color: field.field_name.toLowerCase().includes('mask') ? '#F59E0B' : '#F8FAFC' }}>
                        {field.field_value}
                      </TableCell>
                      <TableCell sx={{ textAlign: 'right' }}>
                        <Chip label={`${Math.round(field.confidence * 100)}%`} size="small" sx={{ height: 20, fontSize: '0.65rem', fontWeight: 800, background: 'rgba(16, 185, 129, 0.15)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.3)' }} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <Alert severity="info" sx={{ background: 'rgba(59, 130, 246, 0.1)', color: '#93C5FD', borderRadius: '12px' }}>
                No structured fields extracted for this document.
              </Alert>
            )}
          </Box>
        )}

        {/* Tab 1: Raw OCR Text */}
        {tabIndex === 1 && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700 }}>RAW RECOGNIZED OCR TEXT (SANITIZED)</Typography>
              <Button size="small" startIcon={<Copy size={14} />} onClick={handleCopyRawText} sx={{ color: copied ? '#10B981' : '#60A5FA' }}>
                {copied ? 'Copied to Clipboard!' : 'Copy Text'}
              </Button>
            </Box>
            <Box
              component="pre"
              sx={{
                p: 2,
                borderRadius: '12px',
                background: '#090D16',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: '#38BDF8',
                fontFamily: 'Consolas, Monaco, monospace',
                fontSize: '0.82rem',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                maxHeight: 300,
                overflowY: 'auto'
              }}
            >
              {document.raw_ocr_text || "No OCR text captured."}
            </Box>
          </Box>
        )}

        {/* Tab 2: Processing Logs */}
        {tabIndex === 2 && (
          <Box>
            {document.logs && document.logs.length > 0 ? (
              <Table size="small" sx={{ '& .MuiTableCell-root': { borderColor: 'rgba(255, 255, 255, 0.08)', color: '#F8FAFC' } }}>
                <TableHead>
                  <TableRow sx={{ background: 'rgba(255, 255, 255, 0.04)' }}>
                    <TableCell sx={{ fontWeight: 700 }}>Stage</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Message</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Timestamp</TableCell>
                    <TableCell sx={{ fontWeight: 700, textAlign: 'right' }}>Duration</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {document.logs.map((log, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Chip label={log.stage} size="small" color="primary" sx={{ height: 22, fontSize: '0.68rem', fontWeight: 700 }} />
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.82rem', color: '#E2E8F0' }}>{log.message}</TableCell>
                      <TableCell sx={{ fontSize: '0.75rem', color: 'text.secondary' }}>{log.timestamp}</TableCell>
                      <TableCell sx={{ textAlign: 'right', fontSize: '0.78rem', fontWeight: 700, color: '#60A5FA' }}>{log.duration}s</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <Alert severity="info" sx={{ background: 'rgba(59, 130, 246, 0.1)', color: '#93C5FD' }}>
                No processing audit logs logged.
              </Alert>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2.5, justifyContent: 'space-between' }}>
        {onDelete ? (
          <Button
            variant="outlined"
            color="error"
            startIcon={<Trash2 size={16} />}
            onClick={() => { onDelete(document.id); onClose(); }}
            sx={{ borderRadius: '10px', fontWeight: 700 }}
          >
            Delete Record
          </Button>
        ) : <Box />}

        <Box sx={{ display: 'flex', gap: 1.5 }}>
          <Button
            variant="outlined"
            startIcon={<FileSpreadsheet size={16} />}
            onClick={handleExportCSV}
            sx={{ borderRadius: '10px', fontWeight: 700, color: '#10B981', borderColor: 'rgba(16, 185, 129, 0.4)', '&:hover': { borderColor: '#10B981', background: 'rgba(16, 185, 129, 0.1)' } }}
          >
            Export CSV
          </Button>
          <Button
            variant="outlined"
            startIcon={<FileJson size={16} />}
            onClick={handleExportJSON}
            sx={{ borderRadius: '10px', fontWeight: 700, color: '#F59E0B', borderColor: 'rgba(245, 158, 11, 0.4)', '&:hover': { borderColor: '#F59E0B', background: 'rgba(245, 158, 11, 0.1)' } }}
          >
            Export JSON
          </Button>
          <Button
            variant="contained"
            onClick={onClose}
            sx={{ borderRadius: '10px', fontWeight: 700, background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)' }}
          >
            Close
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
};
