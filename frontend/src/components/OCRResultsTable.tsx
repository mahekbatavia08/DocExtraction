import React, { useState, useMemo } from 'react';
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TablePagination, TableSortLabel, TextField, InputAdornment, Chip, Tooltip,
  IconButton, Typography, Paper, Alert, TextFieldProps, Button
} from '@mui/material';
import { Search, AlertTriangle, Copy, Edit2, Check, ArrowUpDown, RefreshCw } from 'lucide-react';
import { OCRResultItem } from '../types';
import { MagneticButton } from './MagneticButton';

interface OCRResultsTableProps {
  results: OCRResultItem[];
  fullText?: string;
  onUpdateResultItem?: (id: number, newText: string) => void;
}

type SortField = 'id' | 'text' | 'confidence';
type SortOrder = 'asc' | 'desc';

export const OCRResultsTable: React.FC<OCRResultsTableProps> = ({
  results: initialResults,
  fullText,
  onUpdateResultItem
}) => {
  const [resultsList, setResultsList] = useState<OCRResultItem[]>(initialResults);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortField, setSortField] = useState<SortField>('id');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [page, setPage] = useState<number>(0);
  const [rowsPerPage, setRowsPerPage] = useState<number>(10);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState<string>('');
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [tableCopied, setTableCopied] = useState<boolean>(false);

  // Sync when initialResults change
  React.useEffect(() => {
    setResultsList(initialResults);
  }, [initialResults]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortOrder(field === 'confidence' ? 'desc' : 'asc');
    }
  };

  const handleCopyRow = (id: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleCopyFullText = () => {
    const textToCopy = fullText || resultsList.map(r => r.text).join('\n');
    navigator.clipboard.writeText(textToCopy);
    setTableCopied(true);
    setTimeout(() => setTableCopied(false), 2000);
  };

  const startEdit = (item: OCRResultItem) => {
    setEditingId(item.id);
    setEditText(item.text);
  };

  const saveEdit = (id: number) => {
    setResultsList(prev => prev.map(item => item.id === id ? { ...item, text: editText, corrected_text: editText } : item));
    if (onUpdateResultItem) {
      onUpdateResultItem(id, editText);
    }
    setEditingId(null);
  };

  // Filter and sort items
  const filteredAndSortedResults = useMemo(() => {
    let filtered = resultsList.filter(item =>
      item.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.raw_text && item.raw_text.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    filtered.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = (bVal as string).toLowerCase();
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [resultsList, searchTerm, sortField, sortOrder]);

  const paginatedResults = useMemo(() => {
    const start = page * rowsPerPage;
    return filteredAndSortedResults.slice(start, start + rowsPerPage);
  }, [filteredAndSortedResults, page, rowsPerPage]);

  const lowConfidenceCount = useMemo(() => {
    return resultsList.filter(r => r.confidence < 0.95 || r.is_low_confidence).length;
  }, [resultsList]);

  return (
    <Box sx={{ width: '100%' }}>
      {/* Top Search & Action Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, gap: 2, flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search extracted text..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setPage(0);
          }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search size={16} style={{ color: '#94a3b8' }} />
              </InputAdornment>
            )
          }}
          sx={{
            width: { xs: '100%', sm: 260 },
            '& .MuiOutlinedInput-root': {
              borderRadius: '8px',
              backgroundColor: 'rgba(15, 23, 42, 0.6)'
            }
          }}
        />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {lowConfidenceCount > 0 && (
            <Chip
              icon={<AlertTriangle size={14} color="#f59e0b" />}
              label={`${lowConfidenceCount} Low Confidence (<95%)`}
              color="warning"
              variant="outlined"
              size="small"
              sx={{ fontWeight: 600 }}
            />
          )}

          <MagneticButton>
            <Button
              size="small"
              variant="outlined"
              startIcon={tableCopied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
              onClick={handleCopyFullText}
              sx={{ borderRadius: '8px', textTransform: 'none', fontWeight: 600 }}
            >
              {tableCopied ? 'Copied Full Table' : 'Copy Extracted Text'}
            </Button>
          </MagneticButton>
        </Box>
      </Box>

      {/* Main Responsive Table Container with Sticky Header */}
      <Paper
        elevation={0}
        sx={{
          width: '100%',
          overflow: 'hidden',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          background: '#020617'
        }}
      >
        <TableContainer sx={{ maxHeight: 440 }}>
          <Table stickyHeader size="small" aria-label="OCR Results Table">
            <TableHead>
              <TableRow>
                <TableCell
                  sx={{
                    width: '12%',
                    fontWeight: 700,
                    backgroundColor: '#0f172a !important',
                    color: '#94a3b8',
                    borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
                    py: 1.5
                  }}
                >
                  <TableSortLabel
                    active={sortField === 'id'}
                    direction={sortField === 'id' ? sortOrder : 'asc'}
                    onClick={() => handleSort('id')}
                    sx={{ '&.Mui-active': { color: '#10b981' } }}
                  >
                    Sr. No
                  </TableSortLabel>
                </TableCell>

                <TableCell
                  sx={{
                    width: '63%',
                    fontWeight: 700,
                    backgroundColor: '#0f172a !important',
                    color: '#94a3b8',
                    borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
                    py: 1.5
                  }}
                >
                  <TableSortLabel
                    active={sortField === 'text'}
                    direction={sortField === 'text' ? sortOrder : 'asc'}
                    onClick={() => handleSort('text')}
                    sx={{ '&.Mui-active': { color: '#10b981' } }}
                  >
                    Extracted Text
                  </TableSortLabel>
                </TableCell>

                <TableCell
                  align="right"
                  sx={{
                    width: '25%',
                    fontWeight: 700,
                    backgroundColor: '#0f172a !important',
                    color: '#94a3b8',
                    borderBottom: '2px solid rgba(255, 255, 255, 0.1)',
                    py: 1.5
                  }}
                >
                  <TableSortLabel
                    active={sortField === 'confidence'}
                    direction={sortField === 'confidence' ? sortOrder : 'asc'}
                    onClick={() => handleSort('confidence')}
                    sx={{ '&.Mui-active': { color: '#10b981' } }}
                  >
                    Confidence Score
                  </TableSortLabel>
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {paginatedResults.length > 0 ? (
                paginatedResults.map((row, index) => {
                  const confPercent = (row.confidence * 100).toFixed(1);
                  const isLowConf = row.confidence < 0.95 || row.is_low_confidence;
                  const isEditing = editingId === row.id;

                  return (
                    <TableRow
                      key={row.id}
                      hover
                      className={`animate-fade-in-up stagger-${(index % 8) + 1}`}
                      sx={{
                        backgroundColor: isLowConf
                          ? 'rgba(245, 158, 11, 0.08)'
                          : row.id % 2 === 0
                          ? 'rgba(255, 255, 255, 0.02)'
                          : 'transparent',
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                        '&:hover': {
                          transform: 'translateX(6px)',
                          backgroundColor: isLowConf
                            ? 'rgba(245, 158, 11, 0.15) !important'
                            : 'rgba(16, 185, 129, 0.08) !important'
                        }
                      }}
                    >
                      {/* Sr. No */}
                      <TableCell sx={{ fontWeight: 700, color: isLowConf ? '#f59e0b' : '#94a3b8' }}>
                        {row.id}
                      </TableCell>

                      {/* Extracted Text */}
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
                          {isEditing ? (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                              <TextField
                                size="small"
                                fullWidth
                                value={editText}
                                onChange={(e) => setEditText(e.target.value)}
                                autoFocus
                                sx={{
                                  '& .MuiOutlinedInput-root': {
                                    fontSize: '0.875rem',
                                    borderRadius: '6px',
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)'
                                  }
                                }}
                              />
                              <IconButton className="button-spring" size="small" color="success" onClick={() => saveEdit(row.id)}>
                                <Check size={16} />
                              </IconButton>
                            </Box>
                          ) : (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.2 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600, color: '#f8fafc', wordBreak: 'break-word' }}>
                                {row.text}
                              </Typography>

                              {row.raw_text && row.raw_text !== row.text && (
                                <Typography variant="caption" sx={{ color: '#64748b', fontStyle: 'italic' }}>
                                  Raw: {row.raw_text}
                                </Typography>
                              )}
                            </Box>
                          )}

                          {!isEditing && (
                            <Box sx={{ display: 'flex', opacity: 0.6, '&:hover': { opacity: 1 }, transition: 'opacity 0.2s' }}>
                              <Tooltip title="Edit Text">
                                <IconButton size="small" onClick={() => startEdit(row)}>
                                  <Edit2 size={14} color="#94a3b8" />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title={copiedId === row.id ? 'Copied!' : 'Copy Line'}>
                                <IconButton size="small" onClick={() => handleCopyRow(row.id, row.text)}>
                                  {copiedId === row.id ? <Check size={14} color="#10b981" /> : <Copy size={14} color="#94a3b8" />}
                                </IconButton>
                              </Tooltip>
                            </Box>
                          )}
                        </Box>
                      </TableCell>

                      {/* Confidence Score */}
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                          {isLowConf && (
                            <Tooltip title="Confidence below 95% - Manual review recommended">
                              <AlertTriangle size={15} color="#f59e0b" style={{ cursor: 'pointer' }} />
                            </Tooltip>
                          )}
                          <Chip
                            label={`${confPercent}%`}
                            size="small"
                            className={row.confidence >= 0.95 ? 'animate-pulse-glow' : row.confidence >= 0.8 ? 'animate-breathing' : ''}
                            color={row.confidence >= 0.95 ? 'success' : row.confidence >= 0.8 ? 'warning' : 'error'}
                            variant={row.confidence >= 0.95 ? 'filled' : 'outlined'}
                            sx={{ fontWeight: 700, borderRadius: '6px', minWidth: 60 }}
                          />
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={3} align="center" sx={{ py: 6, color: '#64748b' }}>
                    <Typography variant="body2">
                      {searchTerm ? `No lines matching "${searchTerm}"` : 'No OCR text detected'}
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination Controls */}
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredAndSortedResults.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          sx={{
            color: '#94a3b8',
            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            '.MuiTablePagination-selectIcon': { color: '#94a3b8' }
          }}
        />
      </Paper>
    </Box>
  );
};
