import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { Terminal as TerminalIcon } from 'lucide-react';

interface TerminalLogsProps {
  logs: string[];
}

export const TerminalLogs: React.FC<TerminalLogsProps> = ({ logs }) => {
  if (!logs || logs.length === 0) return null;

  return (
    <Card 
      sx={{ 
        mt: 3, 
        background: '#020617', 
        border: '1px solid rgba(255, 255, 255, 0.1)', 
        borderRadius: '16px',
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
          <TerminalIcon size={18} color="#10b981" />
          <Typography variant="subtitle2" sx={{ color: '#10b981', fontFamily: 'monospace', fontWeight: 700 }}>
            TERMINAL PROCESSING LOGS
          </Typography>
        </Box>

        <Box 
          sx={{ 
            p: 2, 
            borderRadius: '10px', 
            background: '#000000', 
            fontFamily: 'monospace', 
            fontSize: '0.85rem', 
            color: '#34d399', 
            maxHeight: '200px', 
            overflowY: 'auto',
            border: '1px solid rgba(16, 185, 129, 0.2)'
          }}
        >
          {logs.map((log, index) => (
            <div key={index} style={{ marginBottom: '4px', whiteSpace: 'pre-wrap' }}>
              {log}
            </div>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};
