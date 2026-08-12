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
        background: mode === 'dark' ? '#0F172A' : '#FFFFFF',
        borderBottom: mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #E2E8F0',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, md: 3 }, minHeight: 64 }}>
        {/* Left Branding Logo */}
        <Logo size="medium" showText={true} />

        {/* Right Status Controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2 }}>
          {/* Local AI Status Indicator */}
          <Tooltip title={aiStatus?.is_available ? `Local Ollama AI Connected (${aiStatus.configured_model})` : "Local Ollama AI Offline — OCR Fallback Active"}>
            <Chip
              icon={<Cpu size={14} color={aiStatus?.is_available ? '#2563EB' : '#94A3B8'} />}
              label={aiStatus?.is_available ? "Local AI: Connected" : "Local AI: Offline"}
              variant="outlined"
              sx={{
                fontWeight: 600,
                fontSize: '0.72rem',
                borderRadius: '8px',
                background: aiStatus?.is_available 
                  ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.15)' : '#EFF6FF')
                  : (mode === 'dark' ? 'rgba(148, 163, 184, 0.1)' : '#F1F5F9'),
                borderColor: aiStatus?.is_available 
                  ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.3)' : '#BFDBFE')
                  : (mode === 'dark' ? 'rgba(148, 163, 184, 0.2)' : '#E2E8F0'),
                color: aiStatus?.is_available ? '#2563EB' : 'text.secondary'
              }}
            />
          </Tooltip>

          {/* Engine Status Chip */}
          <Chip
            icon={<Activity size={14} color={health ? '#10B981' : '#EF4444'} />}
            label={health ? `FastAPI Engine (${health.engine_type})` : 'Engine Offline'}
            variant="outlined"
            sx={{ 
              fontWeight: 600, 
              fontSize: '0.72rem',
              borderRadius: '8px',
              background: health 
                ? (mode === 'dark' ? 'rgba(16, 185, 129, 0.12)' : '#ECFDF5')
                : (mode === 'dark' ? 'rgba(239, 68, 68, 0.12)' : '#FEF2F2'),
              borderColor: health 
                ? (mode === 'dark' ? 'rgba(16, 185, 129, 0.3)' : '#A7F3D0')
                : (mode === 'dark' ? 'rgba(239, 68, 68, 0.3)' : '#FECACA'),
              color: health ? '#10B981' : '#EF4444'
            }}
          />

          {/* Light / Dark Mode Switcher */}
          <Tooltip title={mode === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}>
            <IconButton 
              onClick={() => { soundFx.playClick(); toggleTheme(); }} 
              size="small" 
              sx={{ 
                p: 1,
                borderRadius: '8px',
                color: mode === 'dark' ? '#F59E0B' : '#6366F1',
                background: mode === 'dark' ? 'rgba(245, 158, 11, 0.1)' : '#F1F5F9',
                border: mode === 'dark' ? '1px solid rgba(245, 158, 11, 0.2)' : '1px solid #E2E8F0',
                '&:hover': { background: mode === 'dark' ? 'rgba(245, 158, 11, 0.2)' : '#E2E8F0' }
              }}
            >
              {mode === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </IconButton>
          </Tooltip>

          {/* Sound Synthesizer Toggle */}
          <Tooltip title={isMuted ? "Unmute Spatial Web Audio" : "Mute Spatial Web Audio"}>
            <IconButton 
              onClick={handleToggleSound} 
              size="small" 
              sx={{ 
                p: 1,
                borderRadius: '8px',
                color: isMuted ? 'text.secondary' : '#2563EB',
                background: isMuted ? 'transparent' : (mode === 'dark' ? 'rgba(37, 99, 235, 0.15)' : '#EFF6FF'),
                border: mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #E2E8F0',
                '&:hover': { background: mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : '#F1F5F9' }
              }}
            >
              {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </IconButton>
          </Tooltip>

          {/* Refresh Diagnostics */}
          <Tooltip title="Refresh Diagnostics">
            <IconButton 
              onClick={() => { soundFx.playClick(); fetchStatus(); }} 
              size="small" 
              sx={{ 
                color: 'text.secondary', 
                borderRadius: '8px',
                p: 1,
                border: mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #E2E8F0',
                '&:hover': { color: '#2563EB', background: mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : '#F1F5F9' } 
              }}
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};
