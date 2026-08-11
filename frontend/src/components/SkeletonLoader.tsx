import React from 'react';
import { Box, Card, CardContent, Skeleton, Grid, Paper } from '@mui/material';

interface SkeletonLoaderProps {
  type?: 'card' | 'table' | 'full';
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ type = 'card' }) => {
  if (type === 'table') {
    return (
      <Box sx={{ width: '100%', py: 1 }}>
        <Skeleton variant="rounded" height={40} sx={{ mb: 1, borderRadius: '8px', background: 'rgba(255, 255, 255, 0.05)' }} />
        {[1, 2, 3, 4, 5].map((idx) => (
          <Skeleton
            key={idx}
            variant="rounded"
            height={36}
            sx={{ mb: 0.8, borderRadius: '6px', background: 'rgba(255, 255, 255, 0.03)' }}
          />
        ))}
      </Box>
    );
  }

  if (type === 'full') {
    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: '16px', background: '#020617', border: '1px solid rgba(255,255,255,0.08)' }}>
            <CardContent sx={{ p: 3 }}>
              <Skeleton variant="text" width="60%" height={32} sx={{ mb: 2 }} />
              <Skeleton variant="rounded" height={260} sx={{ borderRadius: '12px', mb: 2 }} />
              <Skeleton variant="rounded" height={40} sx={{ borderRadius: '8px' }} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ borderRadius: '16px', background: '#020617', border: '1px solid rgba(255,255,255,0.08)' }}>
            <CardContent sx={{ p: 3 }}>
              <Skeleton variant="text" width="50%" height={32} sx={{ mb: 2 }} />
              <Skeleton variant="rounded" height={40} sx={{ mb: 1.5, borderRadius: '8px' }} />
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} variant="rounded" height={32} sx={{ mb: 1, borderRadius: '6px' }} />
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  }

  return (
    <Paper sx={{ p: 2.5, borderRadius: '14px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
        <Skeleton variant="circular" width={36} height={36} />
        <Box sx={{ flex: 1 }}>
          <Skeleton variant="text" width="40%" height={24} />
          <Skeleton variant="text" width="25%" height={18} />
        </Box>
        <Skeleton variant="rounded" width={90} height={28} sx={{ borderRadius: '6px' }} />
      </Box>
      <Skeleton variant="rounded" height={6} sx={{ borderRadius: 3, mb: 1 }} />
    </Paper>
  );
};
