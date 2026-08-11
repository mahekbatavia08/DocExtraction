import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, TextField, MenuItem,
  Table, TableBody, TableCell, TableHead, TableRow, Paper, Chip,
  InputAdornment, IconButton, Tooltip, CircularProgress, Alert, Button, Pagination
} from '@mui/material';
import {
  Database, Search, Filter, ArrowUpDown, FileText, Clock, BarChart3,
  CheckCircle2, RefreshCw, Trash2, Eye, ShieldCheck, Layers, ExternalLink
} from 'lucide-react';
import { getDBDocuments, getDBStats, deleteDBDocument, getDBDocumentById } from '../services/api';
import { DBDocument, DBStats } from '../types';
import { DocumentDetailModal } from '../components/DocumentDetailModal';
import { soundFx } from '../utils/soundEffects';

const DOC_TYPES = [
  'All',
  'PAN Card',
  'Aadhaar Card',
  'Business Card',
  'Payment Card',
  'Invoice',
  'ID Card',
  'Excel Spreadsheet',
  'Document Image',
  'PDF Document',
  'Webcam Capture',
  'Unknown'
];

export const DatabaseHistory: React.FC = () => {
  const [documents, setDocuments] = useState<DBDocument[]>([]);
  const [stats, setStats] = useState<DBStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Sorting
  const [search, setSearch] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [sortBy, setSortBy] = useState<string>('date');
  const [sortOrder, setSortOrder] = useState<string>('desc');

  // Modal State
  const [selectedDoc, setSelectedDoc] = useState<DBDocument | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  const fetchDatabaseData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [docsRes, statsRes] = await Promise.all([
        getDBDocuments({
          search: search || undefined,
          document_type: selectedType === 'All' ? undefined : selectedType,
          sort_by: sortBy,
          order: sortOrder
        }),
        getDBStats()
      ]);
      setDocuments(docsRes.documents);
      setStats(statsRes);
    } catch (err: any) {
      console.error('Failed to load database records:', err);
      setError(err.message || 'Failed to fetch database history.');
    } finally {
      setLoading(false);
    }
  }, [search, selectedType, sortBy, sortOrder]);

  useEffect(() => {
    fetchDatabaseData();
  }, [fetchDatabaseData]);

  const handleRowClick = async (doc: DBDocument) => {
    soundFx.playClick();
    try {
      // Fetch fresh full record including fields, logs, and contact
      const fullDoc = await getDBDocumentById(doc.id);
      setSelectedDoc(fullDoc);
      setIsModalOpen(true);
    } catch (e) {
      setSelectedDoc(doc);
      setIsModalOpen(true);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this document from SQLite database?')) {
      try {
        await deleteDBDocument(id);
        fetchDatabaseData();
      } catch (err) {
        alert('Failed to delete document');
      }
    }
  };

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <Box sx={{ p: 1.2, borderRadius: '14px', background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.25) 0%, rgba(139, 92, 246, 0.2) 100%)', border: '1px solid rgba(20, 184, 166, 0.4)', color: '#2DD4BF' }}>
              <Database size={26} />
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 900, background: 'linear-gradient(135deg, #F8FAFC 0%, #94A3B8 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Database History & Records
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 500 }}>
            Local SQLite Persistent Storage • Masked PCI/Aadhaar Compliance • Stage Audit Logs
          </Typography>
        </Box>

        <Button
          variant="outlined"
          startIcon={<RefreshCw size={16} />}
          onClick={() => { soundFx.playClick(); fetchDatabaseData(); }}
          sx={{ borderRadius: '12px', px: 2.5, py: 1, fontWeight: 700, borderColor: 'rgba(255, 255, 255, 0.15)', color: '#F8FAFC', '&:hover': { background: 'rgba(255, 255, 255, 0.05)' } }}
        >
          Refresh DB
        </Button>
      </Box>

      {/* Metric Stats Cards */}
      <Grid container spacing={2.5} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'rgba(20, 37, 43, 0.85)', backdropFilter: 'blur(20px)', border: '1px solid rgba(20, 184, 166, 0.3)', borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 800, letterSpacing: '0.08em' }}>
                  TOTAL DOCUMENTS
                </Typography>
                <Box sx={{ p: 0.8, borderRadius: '10px', background: 'rgba(20, 184, 166, 0.15)', color: '#2DD4BF' }}>
                  <Layers size={18} />
                </Box>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 900, color: '#F8FAFC' }}>
                {stats?.total_documents || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 800, letterSpacing: '0.08em' }}>
                  AVG OCR CONFIDENCE
                </Typography>
                <Box sx={{ p: 0.8, borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                  <BarChart3 size={18} />
                </Box>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 900, color: '#10B981' }}>
                {stats ? `${Math.round(stats.average_confidence * 100)}%` : '0%'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 800, letterSpacing: '0.08em' }}>
                  AVG PROCESSING TIME
                </Typography>
                <Box sx={{ p: 0.8, borderRadius: '10px', background: 'rgba(245, 158, 11, 0.15)', color: '#F59E0B' }}>
                  <Clock size={18} />
                </Box>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 900, color: '#F59E0B' }}>
                {stats ? `${stats.average_processing_time}s` : '0s'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(168, 85, 247, 0.3)', borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 800, letterSpacing: '0.08em' }}>
                  DOCUMENT TYPES
                </Typography>
                <Box sx={{ p: 0.8, borderRadius: '10px', background: 'rgba(168, 85, 247, 0.15)', color: '#A855F7' }}>
                  <ShieldCheck size={18} />
                </Box>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 900, color: '#A855F7' }}>
                {stats ? Object.keys(stats.document_type_counts || {}).length : 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filter and Search Controls Bar */}
      <Paper sx={{ p: 2.5, mb: 3, background: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '18px' }}>
        <Grid container spacing={2} alignItems="center">
          {/* Search */}
          <Grid item xs={12} sm={5} md={4}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search filename, type, or extracted text..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search size={18} style={{ color: '#94A3B8' }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  color: '#F8FAFC',
                }
              }}
            />
          </Grid>

          {/* Filter Document Type */}
          <Grid item xs={6} sm={3.5} md={3}>
            <TextField
              select
              fullWidth
              size="small"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              label="Filter Type"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  color: '#F8FAFC',
                }
              }}
            >
              {DOC_TYPES.map((type) => (
                <MenuItem key={type} value={type}>{type}</MenuItem>
              ))}
            </TextField>
          </Grid>

          {/* Sort By */}
          <Grid item xs={6} sm={3.5} md={3}>
            <TextField
              select
              fullWidth
              size="small"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              label="Sort By"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  color: '#F8FAFC',
                }
              }}
            >
              <MenuItem value="date">Date (Newest First)</MenuItem>
              <MenuItem value="confidence">Confidence (Highest First)</MenuItem>
              <MenuItem value="filename">File Name</MenuItem>
              <MenuItem value="type">Document Type</MenuItem>
            </TextField>
          </Grid>

          {/* Order Toggle */}
          <Grid item xs={12} sm={12} md={2} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<ArrowUpDown size={16} />}
              onClick={() => setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc')}
              sx={{ borderRadius: '12px', py: 1, px: 2, fontWeight: 700, textTransform: 'uppercase', fontSize: '0.75rem' }}
            >
              {sortOrder === 'desc' ? 'DESC' : 'ASC'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Document Records Data Table (NO STATUS COLUMN per requirements) */}
      <Paper sx={{ background: 'rgba(15, 23, 42, 0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '18px', overflow: 'hidden' }}>
        {loading ? (
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <CircularProgress size={36} color="primary" />
            <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary', fontWeight: 600 }}>
              Loading database records...
            </Typography>
          </Box>
        ) : error ? (
          <Box sx={{ p: 4 }}>
            <Alert severity="error" sx={{ borderRadius: '12px' }}>{error}</Alert>
          </Box>
        ) : documents.length === 0 ? (
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <FileText size={48} style={{ color: '#475569', marginBottom: 12 }} />
            <Typography variant="h6" sx={{ color: 'text.secondary', fontWeight: 700 }}>
              No database records found
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 0.5 }}>
              Upload documents via any module to persist OCR results into SQLite.
            </Typography>
          </Box>
        ) : (
          <Table sx={{ minWidth: 650, '& .MuiTableCell-root': { borderColor: 'rgba(255, 255, 255, 0.08)', color: '#F8FAFC' } }}>
            <TableHead>
              <TableRow sx={{ background: 'rgba(255, 255, 255, 0.04)' }}>
                <TableCell sx={{ fontWeight: 800, fontSize: '0.82rem', py: 2 }}>File Name</TableCell>
                <TableCell sx={{ fontWeight: 800, fontSize: '0.82rem', py: 2 }}>Document Type</TableCell>
                <TableCell sx={{ fontWeight: 800, fontSize: '0.82rem', py: 2 }}>Extracted Name</TableCell>
                <TableCell sx={{ fontWeight: 800, fontSize: '0.82rem', py: 2 }}>Processing Date</TableCell>
                <TableCell sx={{ fontWeight: 800, fontSize: '0.82rem', py: 2, textAlign: 'right' }}>Confidence</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((doc) => (
                <TableRow
                  key={doc.id}
                  hover
                  onClick={() => handleRowClick(doc)}
                  sx={{
                    cursor: 'pointer',
                    transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                    '&:hover': {
                      background: 'rgba(37, 99, 235, 0.1) !important',
                      transform: 'scale(1.002)',
                    }
                  }}
                >
                  {/* Column 1: File Name */}
                  <TableCell sx={{ fontWeight: 700 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box sx={{ p: 0.8, borderRadius: '8px', background: 'rgba(20, 184, 166, 0.15)', color: '#2DD4BF' }}>
                        <FileText size={18} />
                      </Box>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 700, color: '#F8FAFC' }}>
                          {doc.original_filename}
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                          ID: #{doc.id} • {doc.file_type || 'image'}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>

                  {/* Column 2: Document Type */}
                  <TableCell>
                    <Chip
                      label={doc.document_type || 'Unknown'}
                      size="small"
                      sx={{
                        fontWeight: 700,
                        fontSize: '0.72rem',
                        borderRadius: '8px',
                        background: doc.document_type === 'PAN Card' ? 'rgba(59, 130, 246, 0.2)' :
                          doc.document_type === 'Aadhaar Card' ? 'rgba(16, 185, 129, 0.2)' :
                          doc.document_type === 'Business Card' ? 'rgba(168, 85, 247, 0.2)' :
                          doc.document_type === 'Invoice' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                        color: doc.document_type === 'PAN Card' ? '#60A5FA' :
                          doc.document_type === 'Aadhaar Card' ? '#10B981' :
                          doc.document_type === 'Business Card' ? '#C084FC' :
                          doc.document_type === 'Invoice' ? '#FBBF24' : '#F8FAFC',
                        border: '1px solid rgba(255, 255, 255, 0.1)'
                      }}
                    />
                  </TableCell>

                  {/* Column 3: Extracted Name */}
                  <TableCell sx={{ fontWeight: 600, color: doc.extracted_name && doc.extracted_name !== 'N/A' ? '#38BDF8' : 'text.secondary' }}>
                    {doc.extracted_name || 'N/A'}
                  </TableCell>

                  {/* Column 4: Processing Date */}
                  <TableCell sx={{ fontSize: '0.82rem', color: 'text.secondary' }}>
                    {doc.upload_timestamp}
                  </TableCell>

                  {/* Column 5: Confidence */}
                  <TableCell sx={{ textAlign: 'right' }}>
                    <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={`${Math.round(doc.overall_confidence * 100)}%`}
                        size="small"
                        sx={{
                          fontWeight: 800,
                          fontSize: '0.72rem',
                          background: doc.overall_confidence > 0.85 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                          color: doc.overall_confidence > 0.85 ? '#10B981' : '#F59E0B',
                          border: doc.overall_confidence > 0.85 ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)'
                        }}
                      />
                      <IconButton
                        size="small"
                        onClick={(e) => { e.stopPropagation(); handleDelete(doc.id); }}
                        sx={{ color: '#EF4444', opacity: 0.6, '&:hover': { opacity: 1, background: 'rgba(239, 68, 68, 0.15)' } }}
                      >
                        <Trash2 size={16} />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      {/* Complete Document Detail Modal */}
      <DocumentDetailModal
        document={selectedDoc}
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onDelete={(id) => { handleDelete(id); setIsModalOpen(false); }}
      />
    </Box>
  );
};
