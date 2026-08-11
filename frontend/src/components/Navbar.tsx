import React, { useEffect, useState } from 'react';
import { AppBar, Toolbar, Typography, Box, Chip, IconButton, Tooltip } from '@mui/material';
import { Activity, RefreshCw, Volume2, VolumeX, Sun, Moon, Cpu } from 'lucide-react';
import { getHealth, getAIStatus } from '../services/api';
import { HealthResponse, AIStatusResponse } from '../types';
import { soundFx } from '../utils/soundEffects';
import { useThemeMode } from '../context/ThemeContext';
import { Logo } from './Logo';

export const Navbar: React.FC = () => {
  const { mode, toggleTheme } = useThemeMode();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [aiStatus, setAiStatus] = useState<AIStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [isMuted, setIsMuted] = useState(soundFx.getMuted());

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const [hData, aiData] = await Promise.allSettled([getHealth(), getAIStatus()]);
      setHealth(hData.status === 'fulfilled' ? hData.value : null);
      setAiStatus(aiData.status === 'fulfilled' ? aiData.value : null);
    } catch {
      setHealth(null);
      setAiStatus(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleSound = () => {
    const muted = soundFx.toggleMute();
    setIsMuted(muted);
  };

  return (
    <AppBar 
      position="sticky" 
      elevation={0}
      sx={{ 
        background: mode === 'dark' ? 'rgba(18, 30, 21, 0.88)' : 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: mode === 'dark' ? '1px solid rgba(246, 255, 220, 0.15)' : '1px solid rgba(0, 0, 0, 0.08)',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, md: 4 } }}>
        {/* Left Branding Logo */}
        <Logo size="medium" showText={true} />

        {/* Right Status Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {/* Local AI Status Indicator */}
          <Tooltip title={aiStatus?.is_available ? `Local Ollama AI Connected (${aiStatus.configured_model})` : "Local Ollama AI Offline — OCR Fallback Active"}>
            <Chip
              icon={<Cpu size={15} color={aiStatus?.is_available ? '#38BDF8' : '#94A3B8'} />}
              label={aiStatus?.is_available ? "Local AI: Connected" : "Local AI: Offline"}
              variant="outlined"
              sx={{
                fontWeight: 700,
                fontSize: '0.72rem',
                borderRadius: '10px',
                background: aiStatus?.is_available ? 'rgba(56, 189, 248, 0.12)' : 'rgba(148, 163, 184, 0.1)',
                borderColor: aiStatus?.is_available ? 'rgba(56, 189, 248, 0.4)' : 'rgba(148, 163, 184, 0.3)',
                color: aiStatus?.is_available ? '#38BDF8' : '#94A3B8'
              }}
            />
          </Tooltip>

          {/* Light / Dark Mode Switcher */}
          <Tooltip title={mode === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}>
            <IconButton 
              onClick={() => { soundFx.playClick(); toggleTheme(); }} 
              size="small" 
              sx={{ 
                p: 1,
                borderRadius: '10px',
                color: mode === 'dark' ? '#F59E0B' : '#7C3AED',
                background: mode === 'dark' ? 'rgba(245, 158, 11, 0.12)' : 'rgba(124, 58, 237, 0.1)',
                border: mode === 'dark' ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid rgba(124, 58, 237, 0.3)',
                '&:hover': { transform: 'scale(1.05)' }
              }}
            >
              {mode === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </IconButton>
          </Tooltip>

          {/* Sound Synthesizer Toggle */}
          <Tooltip title={isMuted ? "Unmute Spatial Web Audio" : "Mute Spatial Web Audio"}>
            <IconButton 
              onClick={handleToggleSound} 
              size="small" 
              sx={{ 
                p: 1,
                borderRadius: '10px',
                color: isMuted ? 'text.secondary' : '#2563EB',
                background: isMuted ? 'rgba(255, 255, 255, 0.05)' : 'rgba(37, 99, 235, 0.12)',
                border: isMuted ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(37, 99, 235, 0.3)',
                '&:hover': { background: 'rgba(37, 99, 235, 0.2)' }
              }}
            >
              {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
            </IconButton>
          </Tooltip>

          {/* Engine Status Chip */}
          <Chip
            icon={<Activity size={16} color={health ? '#22C55E' : '#EF4444'} />}
            label={health ? `FastAPI Engine (${health.engine_type})` : 'Engine Offline'}
            color={health ? 'success' : 'error'}
            variant="outlined"
            sx={{ 
              fontWeight: 700, 
              fontSize: '0.75rem',
              borderRadius: '10px',
              background: health ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              borderColor: health ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)',
              color: health ? '#22C55E' : '#EF4444'
            }}
          />

          {/* Refresh Status */}
          <Tooltip title="Refresh Diagnostics">
            <IconButton 
              onClick={() => { soundFx.playClick(); fetchStatus(); }} 
              size="small" 
              sx={{ 
                color: 'text.secondary', 
                borderRadius: '10px',
                p: 1,
                border: mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(0, 0, 0, 0.08)',
                '&:hover': { color: '#2563EB', borderColor: 'rgba(37, 99, 235, 0.3)' } 
              }}
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};
