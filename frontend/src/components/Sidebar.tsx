import React, { useState, useEffect } from 'react';
import { 
  Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Box, 
  Typography, Collapse, Tooltip, IconButton, Badge 
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, Contact, CreditCard, BriefcaseBusiness, ChevronDown, ChevronRight,
  ShieldCheck, UserCheck, Building, FileText, Camera, Upload, Layers, 
  Database, BarChart3, Settings, PanelLeftClose, PanelLeftOpen, FolderOpen, CheckCircle2
} from 'lucide-react';
import { soundFx } from '../utils/soundEffects';
import { useThemeMode } from '../context/ThemeContext';
import { getDBDocuments } from '../services/api';

const DRAWER_WIDTH_EXPANDED = 265;
const DRAWER_WIDTH_COLLAPSED = 68;

interface FolderItem {
  id: string;
  label: string;
  icon: any;
  items: { label: string; icon: any; path: string; countKey?: string }[];
}

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { mode } = useThemeMode();

  // 1. Sidebar Collapse Preference (Saved in localStorage)
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved ? JSON.parse(saved) : false;
  });

  // 2. Folder Expansion Preference (Saved in localStorage key: documentSidebarState)
  const [folderStates, setFolderStates] = useState<Record<string, boolean>>(() => {
    const saved = localStorage.getItem('documentSidebarState');
    return saved ? JSON.parse(saved) : { identity: true, financial: true, business: true };
  });

  // Document Counts from Backend DB
  const [docCounts, setDocCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(isCollapsed));
  }, [isCollapsed]);

  useEffect(() => {
    localStorage.setItem('documentSidebarState', JSON.stringify(folderStates));
  }, [folderStates]);

  // Fetch document counts on mount
  useEffect(() => {
    getDBDocuments().then(res => {
      if (res && res.documents) {
        const counts: Record<string, number> = {};
        res.documents.forEach(doc => {
          counts[doc.document_type] = (counts[doc.document_type] || 0) + 1;
        });
        setDocCounts(counts);
      }
    }).catch(() => {});
  }, [location.pathname]);

  // Auto-expand folder matching current active route
  useEffect(() => {
    const p = location.pathname;
    if (['/pan', '/aadhaar', '/id-card'].includes(p)) {
      setFolderStates(prev => ({ ...prev, identity: true }));
    } else if (['/payment-card', '/invoice'].includes(p)) {
      setFolderStates(prev => ({ ...prev, financial: true }));
    } else if (['/business-card'].includes(p)) {
      setFolderStates(prev => ({ ...prev, business: true }));
    }
  }, [location.pathname]);

  const toggleFolder = (folderId: string) => {
    soundFx.playClick();
    setFolderStates(prev => ({ ...prev, [folderId]: !prev[folderId] }));
  };

  const handleNavClick = (path: string) => {
    soundFx.playClick();
    navigate(path);
  };

  const handleNavHover = () => {
    soundFx.playHover();
  };

  // Structured Categories Specification
  const folders: FolderItem[] = [
    {
      id: 'identity',
      label: 'Identity Documents',
      icon: Contact,
      items: [
        { label: 'PAN Card', icon: CreditCard, path: '/pan', countKey: 'PAN Card' },
        { label: 'Aadhaar Card', icon: ShieldCheck, path: '/aadhaar', countKey: 'Aadhaar Card' },
        { label: 'ID Card', icon: UserCheck, path: '/id-card', countKey: 'ID Card' },
      ]
    },
    {
      id: 'financial',
      label: 'Financial Documents',
      icon: CreditCard,
      items: [
        { label: 'Debit / Credit Card', icon: CreditCard, path: '/payment-card', countKey: 'Payment Card' },
        { label: 'Invoice & Receipts', icon: FileText, path: '/invoice', countKey: 'Invoice' },
      ]
    },
    {
      id: 'business',
      label: 'Business & Medical Documents',
      icon: BriefcaseBusiness,
      items: [
        { label: 'Business Cards', icon: Building, path: '/business-card', countKey: 'Business Card' },
        { label: 'Medical Prescriptions', icon: FileText, path: '/medical-prescription', countKey: 'Medical Prescription' },
      ]
    }
  ];

  const currentWidth = isCollapsed ? DRAWER_WIDTH_COLLAPSED : DRAWER_WIDTH_EXPANDED;

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: currentWidth,
        flexShrink: 0,
        transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        [`& .MuiDrawer-paper`]: {
          width: currentWidth,
          boxSizing: 'border-box',
          background: mode === 'dark' ? '#0F172A' : '#FFFFFF',
          borderRight: mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #E2E8F0',
          pt: 2,
          pb: 3,
          overflowX: 'hidden',
          transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        },
      }}
    >
      {/* ── 1. OVERVIEW SECTION ────────────────────────────────────────── */}
      <Box sx={{ px: isCollapsed ? 1 : 2, mb: 2 }}>
        {!isCollapsed && (
          <Typography 
            variant="overline" 
            sx={{ 
              color: mode === 'dark' ? '#64748B' : '#94A3B8', 
              fontWeight: 700, 
              letterSpacing: '0.08em',
              fontSize: '0.65rem',
              px: 1.5,
              mb: 0.8,
              display: 'block',
            }}
          >
            OVERVIEW
          </Typography>
        )}

        <Tooltip title={isCollapsed ? "Dashboard Overview" : ""} placement="right">
          <ListItemButton
            onClick={() => handleNavClick('/')}
            onMouseEnter={handleNavHover}
            sx={{
              borderRadius: '8px',
              py: 1,
              px: isCollapsed ? 1.5 : 1.5,
              justifyContent: isCollapsed ? 'center' : 'flex-start',
              background: location.pathname === '/' 
                ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.16)' : '#EFF6FF')
                : 'transparent',
              borderLeft: location.pathname === '/' ? '3px solid #2563EB' : '3px solid transparent',
              color: location.pathname === '/' 
                ? (mode === 'dark' ? '#60A5FA' : '#1D4ED8') 
                : (mode === 'dark' ? '#94A3B8' : '#475569'),
              '&:hover': {
                background: mode === 'dark' ? 'rgba(255, 255, 255, 0.04)' : '#F8FAFC',
                color: mode === 'dark' ? '#F8FAFC' : '#0F172A',
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: isCollapsed ? 0 : 32, color: location.pathname === '/' ? '#2563EB' : 'inherit' }}>
              <LayoutDashboard size={18} />
            </ListItemIcon>
            {!isCollapsed && (
              <ListItemText
                primary="Dashboard"
                primaryTypographyProps={{
                  fontSize: '0.85rem',
                  fontWeight: location.pathname === '/' ? 700 : 500,
                  fontFamily: "'Inter', sans-serif"
                }}
              />
            )}
          </ListItemButton>
        </Tooltip>
      </Box>

      {/* ── 2. DOCUMENT INTELLIGENCE (Collapsible Folders) ─────────────── */}
      <Box sx={{ px: isCollapsed ? 1 : 2, mb: 2 }}>
        {!isCollapsed && (
          <Typography 
            variant="overline" 
            sx={{ 
              color: mode === 'dark' ? '#64748B' : '#94A3B8', 
              fontWeight: 700, 
              letterSpacing: '0.08em',
              fontSize: '0.65rem',
              px: 1.5,
              mb: 0.8,
              display: 'block',
            }}
          >
            DOCUMENT INTELLIGENCE
          </Typography>
        )}

        {folders.map((folder) => {
          const FolderIcon = folder.icon;
          const isOpen = folderStates[folder.id] ?? true;

          // Calculate total documents count in folder
          const totalFolderDocs = folder.items.reduce((acc, item) => acc + (docCounts[item.countKey || ''] || 0), 0);

          if (isCollapsed) {
            return (
              <Box key={folder.id} sx={{ mb: 1 }}>
                {folder.items.map((subItem) => {
                  const SubIcon = subItem.icon;
                  const isActive = location.pathname === subItem.path;

                  return (
                    <Tooltip key={subItem.path} title={`${folder.label} - ${subItem.label}`} placement="right">
                      <ListItemButton
                        onClick={() => handleNavClick(subItem.path)}
                        sx={{
                          justifyContent: 'center',
                          py: 1,
                          my: 0.3,
                          borderRadius: '8px',
                          background: isActive ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.16)' : '#EFF6FF') : 'transparent',
                          color: isActive ? '#2563EB' : (mode === 'dark' ? '#94A3B8' : '#475569')
                        }}
                      >
                        <SubIcon size={18} />
                      </ListItemButton>
                    </Tooltip>
                  );
                })}
              </Box>
            );
          }

          return (
            <Box key={folder.id} sx={{ mb: 0.8 }}>
              {/* Level 2 Folder Header */}
              <ListItemButton
                onClick={() => toggleFolder(folder.id)}
                sx={{
                  py: 0.75,
                  px: 1.5,
                  borderRadius: '8px',
                  color: mode === 'dark' ? '#CBD5E1' : '#334155',
                  '&:hover': {
                    background: mode === 'dark' ? 'rgba(255, 255, 255, 0.03)' : '#F1F5F9'
                  }
                }}
              >
                <ListItemIcon sx={{ minWidth: 28, color: '#2563EB' }}>
                  <FolderIcon size={16} />
                </ListItemIcon>
                <ListItemText
                  primary={folder.label}
                  primaryTypographyProps={{
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    color: mode === 'dark' ? '#E2E8F0' : '#1E293B'
                  }}
                />
                {totalFolderDocs > 0 && (
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      fontSize: '0.65rem', 
                      fontWeight: 700, 
                      px: 0.8, py: 0.1, 
                      borderRadius: '10px', 
                      background: mode === 'dark' ? 'rgba(255, 255, 255, 0.06)' : '#E2E8F0',
                      color: mode === 'dark' ? '#94A3B8' : '#64748B',
                      mr: 1
                    }}
                  >
                    {totalFolderDocs}
                  </Typography>
                )}
                {isOpen ? <ChevronDown size={15} color="#94A3B8" /> : <ChevronRight size={15} color="#94A3B8" />}
              </ListItemButton>

              {/* Level 3 Document Items (Collapsible) */}
              <Collapse in={isOpen} timeout="auto" unmountOnExit>
                <List disablePadding sx={{ pl: 2, pt: 0.3 }}>
                  {folder.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    const count = docCounts[item.countKey || ''] || 0;

                    return (
                      <ListItem key={item.path} disablePadding sx={{ mb: 0.3 }}>
                        <ListItemButton
                          onClick={() => handleNavClick(item.path)}
                          onMouseEnter={handleNavHover}
                          sx={{
                            borderRadius: '6px',
                            py: 0.65,
                            px: 1.5,
                            background: isActive 
                              ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.16)' : '#EFF6FF')
                              : 'transparent',
                            borderLeft: isActive ? '3px solid #2563EB' : '3px solid transparent',
                            color: isActive 
                              ? (mode === 'dark' ? '#60A5FA' : '#1D4ED8') 
                              : (mode === 'dark' ? '#94A3B8' : '#475569'),
                            transition: 'all 0.15s ease',
                            '&:hover': {
                              background: isActive 
                                ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.22)' : '#DBEAFE')
                                : (mode === 'dark' ? 'rgba(255, 255, 255, 0.04)' : '#F8FAFC'),
                              color: mode === 'dark' ? '#F8FAFC' : '#0F172A',
                            },
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 26, color: isActive ? '#2563EB' : 'inherit' }}>
                            <Icon size={15} />
                          </ListItemIcon>
                          <ListItemText
                            primary={item.label}
                            primaryTypographyProps={{
                              fontSize: '0.78rem',
                              fontWeight: isActive ? 600 : 500,
                              fontFamily: "'Inter', sans-serif"
                            }}
                          />
                          {count > 0 && (
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                fontSize: '0.62rem', 
                                fontWeight: 700,
                                px: 0.7,
                                py: 0.1,
                                borderRadius: '4px',
                                background: isActive ? '#2563EB' : (mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : '#F1F5F9'),
                                color: isActive ? '#FFFFFF' : (mode === 'dark' ? '#94A3B8' : '#64748B')
                              }}
                            >
                              {count}
                            </Typography>
                          )}
                        </ListItemButton>
                      </ListItem>
                    );
                  })}
                </List>
              </Collapse>
            </Box>
          );
        })}
      </Box>

      {/* ── 3. DOCUMENT PROCESSING GROUP ───────────────────────────────── */}
      <Box sx={{ px: isCollapsed ? 1 : 2, mb: 2 }}>
        {!isCollapsed && (
          <Typography 
            variant="overline" 
            sx={{ 
              color: mode === 'dark' ? '#64748B' : '#94A3B8', 
              fontWeight: 700, 
              letterSpacing: '0.08em',
              fontSize: '0.65rem',
              px: 1.5,
              mb: 0.8,
              display: 'block',
            }}
          >
            DOCUMENT PROCESSING
          </Typography>
        )}

        {[
          { label: 'Upload Document', icon: Upload, path: '/upload-image' },
          { label: 'Multi-Document Queue', icon: Layers, path: '/upload-image' },
          { label: 'Live Camera OCR', icon: Camera, path: '/live-camera' },
          { label: 'Uploaded Documents', icon: FolderOpen, path: '/upload-pdf' },
          { label: 'OCR Results', icon: CheckCircle2, path: '/results' },
          { label: 'Database History', icon: Database, path: '/database' }
        ].map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          if (isCollapsed) {
            return (
              <Tooltip key={item.label} title={item.label} placement="right">
                <ListItemButton
                  onClick={() => handleNavClick(item.path)}
                  sx={{
                    justifyContent: 'center',
                    py: 1,
                    my: 0.3,
                    borderRadius: '8px',
                    background: isActive ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.16)' : '#EFF6FF') : 'transparent',
                    color: isActive ? '#2563EB' : (mode === 'dark' ? '#94A3B8' : '#475569')
                  }}
                >
                  <Icon size={18} />
                </ListItemButton>
              </Tooltip>
            );
          }

          return (
            <ListItem key={item.label} disablePadding sx={{ mb: 0.3 }}>
              <ListItemButton
                onClick={() => handleNavClick(item.path)}
                onMouseEnter={handleNavHover}
                sx={{
                  borderRadius: '8px',
                  py: 0.75,
                  px: 1.5,
                  background: isActive 
                    ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.16)' : '#EFF6FF')
                    : 'transparent',
                  borderLeft: isActive ? '3px solid #2563EB' : '3px solid transparent',
                  color: isActive 
                    ? (mode === 'dark' ? '#60A5FA' : '#1D4ED8') 
                    : (mode === 'dark' ? '#94A3B8' : '#475569'),
                  transition: 'all 0.15s ease',
                  '&:hover': {
                    background: mode === 'dark' ? 'rgba(255, 255, 255, 0.04)' : '#F8FAFC',
                    color: mode === 'dark' ? '#F8FAFC' : '#0F172A',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 30, color: isActive ? '#2563EB' : 'inherit' }}>
                  <Icon size={16} />
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.81rem',
                    fontWeight: isActive ? 600 : 500,
                    fontFamily: "'Inter', sans-serif"
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </Box>

      {/* ── 4. SYSTEM SECTION ──────────────────────────────────────────── */}
      <Box sx={{ px: isCollapsed ? 1 : 2, mt: 'auto' }}>
        {!isCollapsed && (
          <Typography 
            variant="overline" 
            sx={{ 
              color: mode === 'dark' ? '#64748B' : '#94A3B8', 
              fontWeight: 700, 
              letterSpacing: '0.08em',
              fontSize: '0.65rem',
              px: 1.5,
              mb: 0.8,
              display: 'block',
            }}
          >
            SYSTEM
          </Typography>
        )}

        <Tooltip title={isCollapsed ? "Settings & Engine" : ""} placement="right">
          <ListItemButton
            onClick={() => handleNavClick('/settings')}
            onMouseEnter={handleNavHover}
            sx={{
              borderRadius: '8px',
              py: 0.75,
              px: 1.5,
              justifyContent: isCollapsed ? 'center' : 'flex-start',
              background: location.pathname === '/settings' 
                ? (mode === 'dark' ? 'rgba(37, 99, 235, 0.16)' : '#EFF6FF')
                : 'transparent',
              borderLeft: location.pathname === '/settings' ? '3px solid #2563EB' : '3px solid transparent',
              color: location.pathname === '/settings' 
                ? (mode === 'dark' ? '#60A5FA' : '#1D4ED8') 
                : (mode === 'dark' ? '#94A3B8' : '#475569'),
              '&:hover': {
                background: mode === 'dark' ? 'rgba(255, 255, 255, 0.04)' : '#F8FAFC',
                color: mode === 'dark' ? '#F8FAFC' : '#0F172A',
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: isCollapsed ? 0 : 30, color: location.pathname === '/settings' ? '#2563EB' : 'inherit' }}>
              <Settings size={16} />
            </ListItemIcon>
            {!isCollapsed && (
              <ListItemText
                primary="Settings & Engine"
                primaryTypographyProps={{
                  fontSize: '0.81rem',
                  fontWeight: location.pathname === '/settings' ? 600 : 500,
                  fontFamily: "'Inter', sans-serif"
                }}
              />
            )}
          </ListItemButton>
        </Tooltip>

        {/* Collapse Sidebar Toggle Button */}
        <Box sx={{ mt: 2, pt: 1.5, borderTop: mode === 'dark' ? '1px solid rgba(255,255,255,0.06)' : '1px solid #F1F5F9', display: 'flex', justifyContent: isCollapsed ? 'center' : 'space-between', alignItems: 'center' }}>
          {!isCollapsed && (
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem', fontWeight: 600, px: 1 }}>
              Collapse Sidebar
            </Typography>
          )}
          <Tooltip title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}>
            <IconButton 
              size="small" 
              onClick={() => setIsCollapsed(!isCollapsed)}
              sx={{ color: mode === 'dark' ? '#94A3B8' : '#64748B' }}
            >
              {isCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
    </Drawer>
  );
};
