import React, { useEffect, useState } from 'react';
import { Box, Grid, Card, CardContent, Typography, Button, Chip, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { Cpu, Clock, CheckCircle2, Zap, RefreshCw, Layers, Sparkles } from 'lucide-react';
import { getStats } from '../services/api';
import { StatsResponse } from '../types';
import { ConstellationHub } from '../components/ConstellationHub';
import { soundFx } from '../utils/soundEffects';
import { useThemeMode } from '../context/ThemeContext';

const useCountUp = (end: number | string, duration: number = 2000) => {
  const [count, setCount] = useState(0);
  const numericEnd = typeof end === 'string' ? parseFloat(end) : end;

  useEffect(() => {
    if (isNaN(numericEnd)) return;
    let startTimestamp: number | null = null;
    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      setCount(easeProgress * numericEnd);
      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };
    window.requestAnimationFrame(step);
  }, [numericEnd, duration]);

  return Number.isInteger(numericEnd) ? Math.floor(count) : count.toFixed(2);
};

const AnimatedNumber = ({ value, suffix = '' }: { value: number | string, suffix?: string }) => {
  const count = useCountUp(value);
  return <>{isNaN(Number(value)) ? value : count}{suffix}</>;
};

export const Home: React.FC = () => {
  const { mode } = useThemeMode();
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchDashboardStats = async () => {
    setLoading(true);
    try {
      const data = await getStats();
      setStats(data);
    } catch {
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  return (
    <Box sx={{ pb: 6, maxWidth: '1450px', mx: 'auto' }}>
      {/* Header Banner */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ maxWidth: '800px' }}>
          <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1, px: 1.2, py: 0.4, borderRadius: '6px', background: mode === 'dark' ? 'rgba(37, 99, 235, 0.15)' : '#EFF6FF', border: mode === 'dark' ? '1px solid rgba(37, 99, 235, 0.3)' : '1px solid #BFDBFE', mb: 1.5 }}>
            <Sparkles size={13} color="#2563EB" />
            <Typography variant="caption" sx={{ color: '#2563EB', fontWeight: 700, letterSpacing: '0.05em' }}>
              AI DOCUMENT VISION MATRIX • MULTI-ENGINE OCR
            </Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 700, fontFamily: "'Outfit', sans-serif", letterSpacing: '-0.02em', mb: 0.8, color: mode === 'dark' ? '#F8FAFC' : '#0F172A' }}>
            Autonomous Document Vision Engine
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary', fontSize: '0.98rem', lineHeight: 1.5 }}>
            High-precision document extraction powered by PaddleOCR and FastAPI.
          </Typography>
        </Box>

        <Button
          variant="outlined"
          startIcon={<RefreshCw size={15} className={loading ? 'animate-spin' : ''} />}
          onClick={() => { soundFx.playClick(); fetchDashboardStats(); }}
          sx={{ 
            borderRadius: '10px', 
            borderColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.15)' : '#E2E8F0', 
            color: mode === 'dark' ? '#F8FAFC' : '#0F172A', 
            fontWeight: 600, 
            px: 2.2, 
            py: 0.9, 
            '&:hover': { borderColor: '#2563EB', background: mode === 'dark' ? 'rgba(37, 99, 235, 0.1)' : '#F1F5F9' } 
          }}
        >
          Refresh Live Metrics
        </Button>
      </Box>

      {/* Metric Cards Row */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ borderRadius: '14px' }}>
            <CardContent sx={{ p: 2.2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, letterSpacing: '0.04em' }}>TOTAL PROCESSED</Typography>
                <Zap size={16} color="#2563EB" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, fontFamily: "'Outfit', sans-serif" }}>
                {stats ? <AnimatedNumber value={stats.total_images_processed} /> : 0}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5, display: 'block', fontSize: '0.75rem' }}>
                Images & PDF Pages
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ borderRadius: '14px' }}>
            <CardContent sx={{ p: 2.2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, letterSpacing: '0.04em' }}>AVG LATENCY</Typography>
                <Clock size={16} color="#6366F1" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, fontFamily: "'Outfit', sans-serif" }}>
                {stats ? <AnimatedNumber value={stats.avg_processing_time} suffix="s" /> : '0.00s'}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5, display: 'block', fontSize: '0.75rem' }}>
                Per Inference Cycle
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ borderRadius: '14px' }}>
            <CardContent sx={{ p: 2.2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, letterSpacing: '0.04em' }}>ENGINE STATUS</Typography>
                <CheckCircle2 size={16} color="#10B981" />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 700, color: '#10B981', fontFamily: "'Outfit', sans-serif" }}>
                {stats ? stats.ocr_status : 'Online'}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5, display: 'block', fontSize: '0.75rem' }}>
                Memory Active (0.2s Warm)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ borderRadius: '14px' }}>
            <CardContent sx={{ p: 2.2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, letterSpacing: '0.04em' }}>OCR MODEL</Typography>
                <Cpu size={16} color="#6366F1" />
              </Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontFamily: "'Outfit', sans-serif" }}>
                {stats ? stats.current_model : 'PaddleOCR PP-OCRv4'}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5, display: 'block', fontSize: '0.75rem' }}>
                Detector + Recognizer
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ borderRadius: '14px' }}>
            <CardContent sx={{ p: 2.2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, letterSpacing: '0.04em' }}>RECENT LOGS</Typography>
                <Layers size={16} color="#2563EB" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, fontFamily: "'Outfit', sans-serif" }}>
                {stats?.recent_activity ? stats.recent_activity.length : 0}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5, display: 'block', fontSize: '0.75rem' }}>
                In-Memory History
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* SEUNGHYUK SPATIAL CONSTELLATION GALAXY HUB */}
      <ConstellationHub />

      {/* Recent Activity Table */}
      {stats?.recent_activity && stats.recent_activity.length > 0 && (
        <Card sx={{ borderRadius: '20px', mt: 4 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 800, mb: 2, fontFamily: "'Outfit', sans-serif" }}>
              Recent Processed Documents Log
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ '& th': { borderColor: 'divider', color: 'text.secondary', fontWeight: 700 } }}>
                  <TableCell>Document Name</TableCell>
                  <TableCell>Blocks Detected</TableCell>
                  <TableCell>Process Time</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Timestamp</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {stats.recent_activity.map((act) => (
                  <TableRow key={act.id} sx={{ '& td': { borderColor: 'divider' }, '&:hover': { background: mode === 'dark' ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' } }}>
                    <TableCell sx={{ fontWeight: 600 }}>{act.image_name}</TableCell>
                    <TableCell>{act.text_blocks}</TableCell>
                    <TableCell>{act.processing_time.toFixed(2)}s</TableCell>
                    <TableCell><Chip label={`${act.confidence}%`} size="small" sx={{ background: 'rgba(34,197,94,0.15)', color: '#22C55E', fontSize: '0.7rem', fontWeight: 700 }} /></TableCell>
                    <TableCell sx={{ color: 'text.secondary', fontSize: '0.8rem' }}>{act.timestamp}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};
