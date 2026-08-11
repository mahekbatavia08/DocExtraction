import React from 'react';
import { Card, CardContent, Typography, Box, Grid, Chip, Divider } from '@mui/material';
import { CreditCard, CheckCircle2, User, Calendar, ShieldCheck } from 'lucide-react';
import { PANDetails } from '../types';

interface PANDetailsCardProps {
  panDetails?: PANDetails;
}

export const PANDetailsCard: React.FC<PANDetailsCardProps> = ({ panDetails }) => {
  if (!panDetails || !panDetails.is_pan_card) {
    return null;
  }

  return (
    <Card 
      sx={{ 
        mb: 3, 
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(15, 23, 42, 0.85) 100%)',
        border: '1px solid rgba(16, 185, 129, 0.4)',
        borderRadius: '16px',
        boxShadow: '0 8px 32px 0 rgba(16, 185, 129, 0.15)',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box sx={{ p: 1, borderRadius: '10px', background: 'rgba(16, 185, 129, 0.2)', display: 'flex' }}>
              <CreditCard size={22} color="#10b981" />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ color: '#10b981', fontWeight: 700 }}>
                PAN Card Auto-Identified
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                Indian Income Tax Department Document Structure
              </Typography>
            </Box>
          </Box>

          <Chip 
            icon={<CheckCircle2 size={16} color="#10b981" />} 
            label={`Match Confidence: ${(panDetails.confidence * 100).toFixed(0)}%`}
            variant="outlined" 
            sx={{ color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.5)', background: 'rgba(16, 185, 129, 0.1)' }} 
          />
        </Box>

        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)', mb: 2.5 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Box sx={{ p: 1.5, borderRadius: '12px', background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8 }}>
                <ShieldCheck size={14} color="#10b981" /> PAN NUMBER
              </Typography>
              <Typography variant="body1" sx={{ color: '#00ff66', fontFamily: 'monospace', fontWeight: 800, fontSize: '1.15rem', mt: 0.5 }}>
                {panDetails.pan_number || 'N/A'}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box sx={{ p: 1.5, borderRadius: '12px', background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8 }}>
                <User size={14} color="#6366f1" /> CARD HOLDER NAME
              </Typography>
              <Typography variant="body1" sx={{ color: '#f8fafc', fontWeight: 700, mt: 0.5 }}>
                {panDetails.name || 'N/A'}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box sx={{ p: 1.5, borderRadius: '12px', background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8 }}>
                <User size={14} color="#a855f7" /> FATHER'S NAME
              </Typography>
              <Typography variant="body1" sx={{ color: '#f8fafc', fontWeight: 700, mt: 0.5 }}>
                {panDetails.father_name || 'N/A'}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box sx={{ p: 1.5, borderRadius: '12px', background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8 }}>
                <Calendar size={14} color="#f59e0b" /> DATE OF BIRTH
              </Typography>
              <Typography variant="body1" sx={{ color: '#f8fafc', fontWeight: 700, mt: 0.5 }}>
                {panDetails.dob || 'N/A'}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
