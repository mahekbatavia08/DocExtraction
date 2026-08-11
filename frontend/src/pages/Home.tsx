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
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ maxWidth: '800px' }}>
          <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1, px: 1.5, py: 0.5, borderRadius: '20px', background: 'rgba(20, 184, 166, 0.12)', border: '1px solid rgba(20, 184, 166, 0.35)', mb: 1.5 }}>
            <Sparkles size={14} color="#14B8A6" />
            <Typography variant="caption" sx={{ color: '#14B8A6', fontWeight: 700, letterSpacing: '0.05em' }}>
              AI DOCUMENT VISION MATRIX • MULTI-ENGINE OCR
            </Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif", letterSpacing: '-0.03em', mb: 1, background: 'linear-gradient(90deg, #F8FAFC 0%, #2DD4BF 50%, #A78BFA 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: mode === 'dark' ? 'transparent' : 'inherit' }}>
            Autonomous Document Vision Engine
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary', fontSize: '1.05rem', lineHeight: 1.6 }}>
            High-precision text extraction, regex parsing, Verhoeff checksum validation, and real-time video stream OCR powered by PaddleOCR & FastAPI.
          </Typography>
        </Box>

        <Button
          variant="outlined"
          startIcon={<RefreshCw size={16} className={loading ? 'animate-spin' : ''} />}
          onClick={() => { soundFx.playClick(); fetchDashboardStats(); }}
          sx={{ borderRadius: '12px', borderColor: mode === 'dark' ? 'rgba(20, 184, 166, 0.3)' : 'rgba(0, 0, 0, 0.12)', color: 'text.primary', fontWeight: 600, px: 2.5, py: 1, '&:hover': { borderColor: '#14B8A6', background: 'rgba(20, 184, 166, 0.1)' } }}
        >
          Refresh Live Metrics
        </Button>
      </Box>

      {/* Metric Cards Row */}
      <Grid container spacing={2.5} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4} className="animate-fade-in-up stagger-1">
          <Card className="card-hover-premium" sx={{ borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: '0.05em' }}>TOTAL PROCESSED</Typography>
                <Zap size={18} color="#14B8A6" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
                {stats ? <AnimatedNumber value={stats.total_images_processed} /> : 0}
              </Typography>
              <Typography variant="caption" sx={{ color: '#14B8A6', mt: 0.5, display: 'block', fontWeight: 600 }}>
                Images & PDF Pages
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4} className="animate-fade-in-up stagger-2">
          <Card className="card-hover-premium" sx={{ borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: '0.05em' }}>AVG LATENCY</Typography>
                <Clock size={18} color="#8B5CF6" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
                {stats ? <AnimatedNumber value={stats.avg_processing_time} suffix="s" /> : '0.00s'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#8B5CF6', mt: 0.5, display: 'block', fontWeight: 600 }}>
                Per Inference Cycle
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4} className="animate-fade-in-up stagger-3">
          <Card className="card-hover-premium" sx={{ borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: '0.05em' }}>ENGINE STATUS</Typography>
                <CheckCircle2 size={18} color="#10B981" />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 800, color: '#10B981', fontFamily: "'Outfit', sans-serif" }}>
                {stats ? stats.ocr_status : 'Online'}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', mt: 0.5, display: 'block', fontWeight: 600 }}>
                Memory Active (0.2s Warm)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4} className="animate-fade-in-up stagger-4">
          <Card className="card-hover-premium" sx={{ borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: '0.05em' }}>OCR MODEL</Typography>
                <Cpu size={18} color="#8B5CF6" />
              </Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 800, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontFamily: "'Outfit', sans-serif" }}>
                {stats ? stats.current_model : 'PaddleOCR PP-OCRv4'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#8B5CF6', mt: 0.5, display: 'block', fontWeight: 600 }}>
                Detector + Recognizer
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={2.4} className="animate-fade-in-up stagger-5">
          <Card className="card-hover-premium" sx={{ borderRadius: '18px' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: '0.05em' }}>RECENT LOGS</Typography>
                <Layers size={18} color="#2DD4BF" />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
                {stats?.recent_activity ? stats.recent_activity.length : 0}
              </Typography>
              <Typography variant="caption" sx={{ color: '#2DD4BF', mt: 0.5, display: 'block', fontWeight: 600 }}>
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
