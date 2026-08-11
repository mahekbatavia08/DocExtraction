import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Card, CardContent, Typography, Button, LinearProgress, Chip, Alert,
  Table, TableBody, TableCell, TableHead, TableRow, IconButton, Tooltip
} from '@mui/material';
import { Play, Trash2, Layers, Download, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { processUniversal } from '../services/api';
import { CardDetailModal } from './CardDetailModal';

export interface CardQueueItem {
  id: string;
  file: File;
  previewUrl: string | null;
  status: 'waiting' | 'processing' | 'complete' | 'error';
  result: any | null; // Universal API response
  errorMsg: string | null;
}

interface MultiCardQueueProps {
  files: File[];
  onClearFiles: () => void;
  onRemoveFile: (index: number) => void;
}

export const MultiCardQueue: React.FC<MultiCardQueueProps> = ({
  files,
  onClearFiles,
  onRemoveFile
}) => {
  const [queue, setQueue] = useState<CardQueueItem[]>([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState<boolean>(false);
  const [selectedCard, setSelectedCard] = useState<CardQueueItem | null>(null);

  const queueRef = useRef<CardQueueItem[]>(queue);
  useEffect(() => {
    queueRef.current = queue;
  }, [queue]);

  const isProcessingQueueRef = useRef(false);

  useEffect(() => {
    setQueue(prev => {
      const existingMap = new Map(prev.map(item => [item.file.name + item.file.size, item]));
      return files.map((file, idx) => {
        const key = file.name + file.size;
        if (existingMap.has(key)) return existingMap.get(key)!;
        return {
          id: `card_${idx}_${Date.now()}`,
          file,
          previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
          status: 'waiting',
          result: null,
          errorMsg: null
        };
      });
    });
  }, [files]);

  const startProcessingQueue = async () => {
    if (isProcessingQueueRef.current) return;
    isProcessingQueueRef.current = true;
    setIsProcessingQueue(true);

    while (true) {
      const targetItem = queueRef.current.find(item => item.status === 'waiting');
      if (!targetItem) break;

      const itemId = targetItem.id;
      setQueue(q => q.map(item => item.id === itemId ? { ...item, status: 'processing' } : item));

      try {
        const res = await processUniversal(targetItem.file);
        setQueue(q => q.map(item => item.id === itemId ? {
          ...item,
          status: 'complete',
          result: res
        } : item));
      } catch (err: any) {
        setQueue(q => q.map(item => item.id === itemId ? {
          ...item,
          status: 'error',
          errorMsg: err.response?.data?.detail || err.message || 'Failed to process card.'
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

  const handleExportAll = () => {
    const completed = queue.filter(q => q.status === 'complete' && q.result);
    if (completed.length === 0) return;
    
    const exportData = completed.map(c => c.result);
    const dataStr = JSON.stringify(exportData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `multi_card_export_${new Date().getTime()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const extractNameAndCardNumber = (fields: any = {}) => {
    let name = fields['Name'] || fields['Candidate Name'] || fields['Party A'] || '';
    let cardNumber = fields['PAN Number'] || fields['Aadhaar Number'] || fields['License Number'] || fields['Passport Number'] || fields['Validated Aadhaar'] || fields['Masked Aadhaar'] || '';
    
    // Attempting some basic heuristics for other cards if specific fields are absent
    if (!name && Object.keys(fields).length > 0) {
       const possibleNames = ['First Name', 'Given Name', 'Full Name'];
       for (const n of possibleNames) {
           if (fields[n]) name = fields[n];
       }
    }
    
    return { name, cardNumber };
  };

  if (queue.length === 0) return null;

  return (
    <Box sx={{ width: '100%', mt: 3 }}>
      <Card sx={{ borderRadius: '16px', mb: 3, background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(2, 6, 23, 0.95) 100%)', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Layers size={22} color="#10b981" />
              <Typography variant="h6" sx={{ fontWeight: 800 }}>
                Multi-Card Batch Queue ({queue.length} Cards)
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
                {isProcessingQueue ? 'Processing Queue...' : `Process ${waitingCount} Cards`}
              </Button>
              
              <Button
                variant="outlined"
                color="primary"
                disabled={completedCount === 0}
                onClick={handleExportAll}
                startIcon={<Download size={16} />}
                sx={{ borderRadius: '8px', fontWeight: 600 }}
              >
                Export All
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

      <Card sx={{ borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <CardContent sx={{ p: 0 }}>
          <Table>
            <TableHead>
              <TableRow sx={{ background: 'rgba(255, 255, 255, 0.03)' }}>
                <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Sr No</TableCell>
                <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>File Name</TableCell>
                <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Card Type</TableCell>
                <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Name</TableCell>
                <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Card Number</TableCell>
                <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }}>Confidence</TableCell>
                <TableCell sx={{ color: 'text.secondary', fontWeight: 600 }} align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {queue.map((item, index) => {
                let cardType = '-';
                let name = '-';
                let cardNumber = '-';
                let confidenceStr = '-';
                
                if (item.status === 'processing') {
                   cardType = 'Processing...';
                } else if (item.status === 'error') {
                   cardType = 'Error';
                } else if (item.status === 'complete' && item.result) {
                   cardType = item.result.metadata?.document_type || 'Unknown';
                   const extracted = extractNameAndCardNumber(item.result.fields);
                   name = extracted.name || '-';
                   cardNumber = extracted.cardNumber || '-';
                   const conf = item.result.confidence || item.result.metadata?.confidence_score || 0;
                   confidenceStr = `${(conf * 100).toFixed(1)}%`;
                }

                return (
                  <TableRow 
                    key={item.id} 
                    hover 
                    onClick={() => item.status === 'complete' && setSelectedCard(item)}
                    sx={{ cursor: item.status === 'complete' ? 'pointer' : 'default' }}
                  >
                    <TableCell>{index + 1}</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                         {item.status === 'waiting' && <Clock size={16} color="#94a3b8" />}
                         {item.status === 'processing' && <Layers size={16} color="#3b82f6" className="animate-pulse" />}
                         {item.status === 'complete' && <CheckCircle2 size={16} color="#10b981" />}
                         {item.status === 'error' && <AlertCircle size={16} color="#ef4444" />}
                         {item.file.name}
                      </Box>
                    </TableCell>
                    <TableCell>{cardType}</TableCell>
                    <TableCell>{name}</TableCell>
                    <TableCell>{cardNumber}</TableCell>
                    <TableCell>
                       {item.status === 'complete' && (
                         <Chip label={confidenceStr} size="small" color={parseFloat(confidenceStr) > 90 ? 'success' : 'warning'} variant="outlined" />
                       )}
                       {item.status === 'processing' && <LinearProgress sx={{ width: '50px' }} />}
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Remove">
                        <IconButton size="small" onClick={(e) => { e.stopPropagation(); onRemoveFile(index); }}>
                          <Trash2 size={16} color="#ef4444" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      
      {selectedCard && (
        <CardDetailModal 
          open={!!selectedCard} 
          onClose={() => setSelectedCard(null)} 
          cardResult={selectedCard.result} 
          fileName={selectedCard.file.name} 
        />
      )}
    </Box>
  );
};
