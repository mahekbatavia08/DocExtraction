import React from 'react';
import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Box, Typography } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Camera, FileText, BarChart3, Settings, 
  CreditCard, ShieldCheck, UserCheck, Building, Globe, Layers, Database
} from 'lucide-react';
import { soundFx } from '../utils/soundEffects';
import { useThemeMode } from '../context/ThemeContext';

interface NavGroup {
  groupName: string;
  items: { label: string; icon: any; path: string; badge?: string }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    groupName: 'AI VISION MATRIX',
    items: [
      { label: 'Universal Galaxy', icon: Globe, path: '/' },
    ]
  },
  {
    groupName: 'DOCUMENT MODULES',
    items: [
      { label: 'PAN Card OCR', icon: CreditCard, path: '/pan', badge: 'Regex' },
      { label: 'Aadhaar Card OCR', icon: ShieldCheck, path: '/aadhaar', badge: 'UID' },
      { label: 'ID Card OCR', icon: UserCheck, path: '/id-card' },
      { label: 'Business Cards', icon: Building, path: '/business-card', badge: 'Duplicates' },
      { label: 'Debit / Credit Card', icon: CreditCard, path: '/payment-card', badge: 'PCI' },
      { label: 'Invoice & Receipts', icon: FileText, path: '/invoice', badge: 'Audit Math' },
    ]
  },
  {
    groupName: 'PIPELINES & QUEUES',
    items: [
      { label: 'Database History', icon: Database, path: '/database', badge: 'SQLite' },
      { label: 'Live Camera OCR', icon: Camera, path: '/live-camera', badge: 'Realtime' },
      { label: 'Multi-Doc Queue', icon: Layers, path: '/upload-image', badge: 'Batch' },
      { label: 'Upload PDF', icon: FileText, path: '/upload-pdf' },
      { label: 'OCR Results Output', icon: BarChart3, path: '/results' },
    ]
  },
  {
    groupName: 'SYSTEM',
    items: [
      { label: 'Settings & Engine', icon: Settings, path: '/settings' },
    ]
  }
];

const DRAWER_WIDTH = 260;

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { mode } = useThemeMode();

  const handleNavClick = (path: string) => {
    soundFx.playClick();
    navigate(path);
  };

  const handleNavHover = () => {
    soundFx.playHover();
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          background: mode === 'dark' ? '#0F172A' : '#FFFFFF',
          borderRight: mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #E2E8F0',
          pt: 2.5,
          pb: 4
        },
      }}
    >
      {NAV_GROUPS.map((group) => (
        <Box key={group.groupName} sx={{ mb: 2, px: 2 }}>
          <Typography 
            variant="overline" 
            sx={{ 
              color: mode === 'dark' ? '#94A3B8' : '#64748B', 
              fontWeight: 700, 
              letterSpacing: '0.08em',
              fontSize: '0.65rem',
              px: 1.5,
              mb: 0.8,
              display: 'block',
            }}
          >
            {group.groupName}
          </Typography>

          <List disablePadding>
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <ListItem key={item.path} disablePadding sx={{ mb: 0.4 }}>
                  <ListItemButton
                    onClick={() => handleNavClick(item.path)}
                    onMouseEnter={handleNavHover}
                    sx={{
                      borderRadius: '8px',
                      py: 0.85,
                      px: 1.5,
                      background: isActive 
                        ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.16)' : '#EFF6FF')
                        : 'transparent',
                      borderLeft: isActive ? '3px solid #2563EB' : '3px solid transparent',
                      color: isActive 
                        ? (mode === 'dark' ? '#60A5FA' : '#1D4ED8') 
                        : (mode === 'dark' ? '#94A3B8' : '#475569'),
                      transition: 'all 0.18s ease',
                      '&:hover': {
                        background: isActive 
                          ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.22)' : '#DBEAFE')
                          : (mode === 'dark' ? 'rgba(255, 255, 255, 0.04)' : '#F8FAFC'),
                        color: mode === 'dark' ? '#F8FAFC' : '#0F172A',
                      },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 32, color: isActive ? '#2563EB' : 'inherit' }}>
                      <Icon size={17} />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        fontSize: '0.82rem',
                        fontWeight: isActive ? 600 : 500,
                        fontFamily: "'Inter', sans-serif"
                      }}
                    />
                    {item.badge && (
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          fontSize: '0.62rem', 
                          fontWeight: 600,
                          px: 0.8,
                          py: 0.2,
                          borderRadius: '4px',
                          background: mode === 'dark' ? 'rgba(255, 255, 255, 0.06)' : '#F1F5F9',
                          color: mode === 'dark' ? '#94A3B8' : '#64748B'
                        }}
                      >
                        {item.badge}
                      </Typography>
                    )}
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
        </Box>
      ))}

      {/* Footer System Badge */}
      <Box sx={{ mt: 'auto', px: 3, pt: 2 }}>
        <Box sx={{ p: 2, borderRadius: '14px', background: mode === 'dark' ? 'rgba(20, 184, 166, 0.1)' : 'rgba(20, 184, 166, 0.05)', border: '1px solid rgba(20, 184, 166, 0.25)', textAlign: 'center' }}>
          <Typography variant="caption" sx={{ color: '#14B8A6', fontWeight: 700, display: 'block', mb: 0.5 }}>
            PADDLE OCR AI SAAS
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.68rem', display: 'block' }}>
            Multi-Engine Vision Pipeline
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
};
