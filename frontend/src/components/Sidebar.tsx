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
      { label: 'Settings & Engine', icon: Settings, path: '/settings' },
    ]
  }
];

const DRAWER_WIDTH = 265;

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
          background: mode === 'dark' ? 'rgba(18, 30, 21, 0.92)' : 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(20px)',
          borderRight: mode === 'dark' ? '1px solid rgba(246, 255, 220, 0.15)' : '1px solid rgba(0, 0, 0, 0.08)',
          pt: 2,
          pb: 4
        },
      }}
    >
      {NAV_GROUPS.map((group) => (
        <Box key={group.groupName} sx={{ mb: 2.5, px: 2 }}>
          <Typography 
            variant="overline" 
            sx={{ 
              color: mode === 'dark' ? '#F6FFDC' : 'text.secondary', 
              fontWeight: 800, 
              letterSpacing: '0.12em',
              fontSize: '0.65rem',
              px: 1.5,
              mb: 1,
              display: 'block',
              opacity: 0.7
            }}
          >
            {group.groupName}
          </Typography>

          <List disablePadding>
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <ListItem key={item.path} disablePadding sx={{ mb: 0.8 }} className="parent-hover">
                  <ListItemButton
                    onClick={() => handleNavClick(item.path)}
                    onMouseEnter={handleNavHover}
                    sx={{
                      borderRadius: '12px',
                      py: 1,
                      px: 1.5,
                      background: isActive 
                        ? (mode === 'dark' 
                            ? 'linear-gradient(135deg, rgba(246, 255, 220, 0.22) 0%, rgba(167, 139, 250, 0.18) 100%)' 
                            : 'linear-gradient(135deg, rgba(20, 184, 166, 0.25) 0%, rgba(139, 92, 246, 0.2) 100%)')
                        : 'transparent',
                      border: isActive ? (mode === 'dark' ? '1px solid rgba(246, 255, 220, 0.4)' : '1px solid rgba(20, 184, 166, 0.4)') : '1px solid transparent',
                      color: isActive ? (mode === 'dark' ? '#F6FFDC' : '#0F766E') : 'text.secondary',
                      boxShadow: isActive ? (mode === 'dark' ? '0 4px 15px rgba(246, 255, 220, 0.2)' : '0 4px 15px rgba(20, 184, 166, 0.2)') : 'none',
                      transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
                      '&:hover': {
                        background: isActive 
                          ? (mode === 'dark'
                              ? 'linear-gradient(135deg, rgba(246, 255, 220, 0.3) 0%, rgba(167, 139, 250, 0.25) 100%)'
                              : 'linear-gradient(135deg, rgba(20, 184, 166, 0.3) 0%, rgba(139, 92, 246, 0.25) 100%)')
                          : mode === 'dark' ? 'rgba(246, 255, 220, 0.08)' : 'rgba(0, 0, 0, 0.04)',
                        color: mode === 'dark' ? '#F6FFDC' : '#0F1D21',
                        transform: 'translateX(4px)',
                      },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 34, color: isActive ? (mode === 'dark' ? '#F6FFDC' : '#0F766E') : 'inherit' }}>
                      <Icon size={18} className="icon-rotate-hover" />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        fontSize: '0.85rem',
                        fontWeight: isActive ? 700 : 500,
                        fontFamily: "'Inter', sans-serif"
                      }}
                    />
                    {item.badge && (
                      <Box 
                        sx={{ 
                          fontSize: '0.6rem', 
                          fontWeight: 700, 
                          px: 0.8, 
                          py: 0.2, 
                          borderRadius: '6px', 
                          background: isActive ? 'rgba(20, 184, 166, 0.25)' : (mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)'),
                          color: isActive ? '#2DD4BF' : 'text.secondary',
                          border: isActive ? '1px solid rgba(20, 184, 166, 0.4)' : '1px solid transparent'
                        }}
                      >
                        {item.badge}
                      </Box>
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
