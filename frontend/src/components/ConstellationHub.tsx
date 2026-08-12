import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Card, Chip, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { 
  CreditCard, ShieldCheck, UserCheck, Building, FileText, 
  Camera, Layers, ArrowUpRight, Zap, Sparkles, Compass, Grid, Activity
} from 'lucide-react';
import { soundFx } from '../utils/soundEffects';
import { useThemeMode } from '../context/ThemeContext';

interface ConstellationNode {
  id: string;
  title: string;
  subtitle: string;
  category: string;
  path: string;
  icon: React.ReactNode;
  color: string;
  angle: number;
  distance: number;
  badge: string;
  accuracy: string;
  description: string;
}

const NODES: ConstellationNode[] = [
  {
    id: 'pan',
    title: 'PAN Card OCR',
    subtitle: 'Tax Identity Verification',
    category: 'Government ID',
    path: '/pan',
    icon: <CreditCard size={22} color="#2563EB" />,
    color: '#2563EB',
    angle: 0,
    distance: 36,
    badge: 'Regex Validated',
    accuracy: '99.8%',
    description: 'Extract PAN number, cardholder name, father name, and DOB with strict regex rules.'
  },
  {
    id: 'aadhaar',
    title: 'Aadhaar Card OCR',
    subtitle: 'National Biometric ID',
    category: 'Government ID',
    path: '/aadhaar',
    icon: <ShieldCheck size={22} color="#38BDF8" />,
    color: '#38BDF8',
    angle: 45,
    distance: 38,
    badge: 'Verhoeff Checksum',
    accuracy: '99.9%',
    description: 'Extract Aadhaar UID, City, State, and Address with Verhoeff checksum validation.'
  },
  {
    id: 'id-card',
    title: 'ID Card OCR',
    subtitle: 'Employee & Student Cards',
    category: 'Identity',
    path: '/id-card',
    icon: <UserCheck size={22} color="#7C3AED" />,
    color: '#7C3AED',
    angle: 90,
    distance: 36,
    badge: 'Multi-Format',
    accuracy: '98.5%',
    description: 'Structure school, university, and enterprise identity badge metadata.'
  },
  {
    id: 'business-card',
    title: 'Business Cards',
    subtitle: 'Contact Manager & Duplicates',
    category: 'Enterprise',
    path: '/business-card',
    icon: <Building size={22} color="#F59E0B" />,
    color: '#F59E0B',
    angle: 135,
    distance: 38,
    badge: 'Duplicate Alert',
    accuracy: '99.2%',
    description: 'Batch process visiting cards, extract vCards, and auto-detect duplicate contacts.'
  },
  {
    id: 'invoice',
    title: 'Invoice & Receipts',
    subtitle: 'Financial Math Verification',
    category: 'Finance',
    path: '/invoice',
    icon: <FileText size={22} color="#EC4899" />,
    color: '#EC4899',
    angle: 180,
    distance: 36,
    badge: 'Arithmetic Audit',
    accuracy: '99.5%',
    description: 'Audit subtotal, GST/VAT tax math, vendor name, and line items with error audit.'
  },
  {
    id: 'payment-card',
    title: 'Payment Cards',
    subtitle: 'Credit & Debit PCI Masking',
    category: 'Banking',
    path: '/payment-card',
    icon: <CreditCard size={22} color="#10B981" />,
    color: '#10B981',
    angle: 225,
    distance: 38,
    badge: 'PCI-DSS Masking',
    accuracy: '99.7%',
    description: 'Recognize card network, expiry date, masked PAN, and BIN code.'
  },
  {
    id: 'camera',
    title: 'Live Camera OCR',
    subtitle: 'Real-time Video Quality Gate',
    category: 'Stream',
    path: '/camera',
    icon: <Camera size={22} color="#EF4444" />,
    color: '#EF4444',
    angle: 270,
    distance: 36,
    badge: 'Realtime Feed',
    accuracy: '97.8%',
    description: 'Live document alignment, blur detector, and frame auto-capture.'
  },
  {
    id: 'queue',
    title: 'Multi-Doc Queue',
    subtitle: 'Batch PDF & Image Engine',
    category: 'Queue',
    path: '/queue',
    icon: <Layers size={22} color="#6366F1" />,
    color: '#6366F1',
    angle: 315,
    distance: 38,
    badge: 'Parallel Worker',
    accuracy: '99.4%',
    description: 'Upload zip/pdf documents for parallel multi-model extraction.'
  }
];

export const ConstellationHub: React.FC = () => {
  const { mode } = useThemeMode();
  const navigate = useNavigate();
  const [activeNode, setActiveNode] = useState<ConstellationNode | null>(null);
  const [viewMode, setViewMode] = useState<'spatial' | 'grid'>('spatial');
  const [pulseCore, setPulseCore] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulseCore((prev) => !prev);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleNodeHover = (node: ConstellationNode | null) => {
    if (node) soundFx.playHover();
    setActiveNode(node);
  };

  const handleNodeClick = (node: ConstellationNode) => {
    soundFx.playChime();
    navigate(node.path);
  };

  return (
    <Box sx={{ width: '100%', position: 'relative', my: 2 }}>
      {/* Header with Mode Switcher */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 4, 
        px: 2,
        flexWrap: 'wrap',
        gap: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ 
            p: 1, 
            borderRadius: '12px', 
            background: mode === 'dark' 
              ? 'linear-gradient(135deg, rgba(20, 184, 166, 0.2), rgba(139, 92, 246, 0.2))'
              : 'linear-gradient(135deg, rgba(20, 184, 166, 0.15), rgba(139, 92, 246, 0.15))',
            border: '1px solid rgba(20, 184, 166, 0.3)',
            display: 'flex',
            alignItems: 'center'
          }}>
            <Sparkles size={20} color="#14B8A6" />
          </Box>
          <Box>
            <Typography variant="h5" sx={{ 
              fontWeight: 800, 
              fontFamily: "'Outfit', sans-serif", 
              letterSpacing: '-0.02em', 
              color: mode === 'dark' ? '#F8FAFC' : '#0F1D21'
            }}>
              Spatial Document Galaxy
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8, fontWeight: 600 }}>
              <Activity size={12} color="#14B8A6" /> Interactive Point-Line-Plane Neural Matrix • Select any node to activate OCR
            </Typography>
          </Box>
        </Box>

        <Box sx={{ 
          display: 'flex', 
          gap: 1, 
          background: mode === 'dark' ? 'rgba(15, 29, 33, 0.8)' : 'rgba(255, 255, 255, 0.95)', 
          p: 0.6, 
          borderRadius: '12px', 
          border: mode === 'dark' ? '1px solid rgba(20, 184, 166, 0.2)' : '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: mode === 'dark' ? 'none' : '0 2px 10px rgba(0,0,0,0.06)'
        }}>
          <Button
            size="small"
            onClick={() => { soundFx.playClick(); setViewMode('spatial'); }}
            startIcon={<Compass size={16} />}
            sx={{
              borderRadius: '8px',
              textTransform: 'none',
              fontWeight: 700,
              px: 2,
              color: viewMode === 'spatial' 
                ? (mode === 'dark' ? '#14B8A6' : '#0F1D21')
                : 'text.secondary',
              background: viewMode === 'spatial' 
                ? (mode === 'dark' ? 'rgba(20, 184, 166, 0.2)' : '#FFFFFF')
                : 'transparent',
              border: viewMode === 'spatial' 
                ? (mode === 'dark' ? '1px solid rgba(20, 184, 166, 0.4)' : '1px solid rgba(20, 184, 166, 0.3)')
                : '1px solid transparent',
              boxShadow: (viewMode === 'spatial' && mode === 'light') ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
              '&:hover': { background: mode === 'dark' ? 'rgba(20, 184, 166, 0.25)' : '#FFFFFF' }
            }}
          >
            Spatial Galaxy
          </Button>
          <Button
            size="small"
            onClick={() => { soundFx.playClick(); setViewMode('grid'); }}
            startIcon={<Grid size={16} />}
            sx={{
              borderRadius: '8px',
              textTransform: 'none',
              fontWeight: 700,
              px: 2,
              color: viewMode === 'grid' 
                ? (mode === 'dark' ? '#14B8A6' : '#0F1D21')
                : 'text.secondary',
              background: viewMode === 'grid' 
                ? (mode === 'dark' ? 'rgba(20, 184, 166, 0.2)' : '#FFFFFF')
                : 'transparent',
              border: viewMode === 'grid' 
                ? (mode === 'dark' ? '1px solid rgba(20, 184, 166, 0.4)' : '1px solid rgba(20, 184, 166, 0.3)')
                : '1px solid transparent',
              boxShadow: (viewMode === 'grid' && mode === 'light') ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
              '&:hover': { background: mode === 'dark' ? 'rgba(20, 184, 166, 0.25)' : '#FFFFFF' }
            }}
          >
            Matrix Grid
          </Button>
        </Box>
      </Box>

      {/* SPATIAL GALAXY VIEW MODE */}
      {viewMode === 'spatial' ? (
        <Box 
          ref={containerRef}
          sx={{ 
            position: 'relative', 
            width: '100%', 
            minHeight: '620px', 
            borderRadius: '24px', 
            background: mode === 'dark' 
              ? 'radial-gradient(circle at 50% 50%, rgba(15, 29, 33, 0.98) 0%, rgba(10, 18, 21, 0.99) 100%)'
              : 'radial-gradient(circle at 50% 50%, #FFFFFF 0%, #F8FAFC 100%)',
            border: mode === 'dark' ? '1px solid rgba(20, 184, 166, 0.15)' : '1px solid rgba(20, 184, 166, 0.25)',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: mode === 'dark' ? '0 20px 50px rgba(0,0,0,0.5)' : '0 10px 30px rgba(20, 184, 166, 0.1)',
            p: 2
          }}
        >
          {/* Subtle Orbital Circles background */}
          <Box sx={{
            position: 'absolute',
            width: '420px', height: '420px',
            borderRadius: '50%',
            border: mode === 'dark' ? '1px dashed rgba(255, 255, 255, 0.08)' : '1px dashed rgba(20, 184, 166, 0.2)',
            pointerEvents: 'none',
            animation: 'spinSmooth 60s linear infinite'
          }} />
          <Box sx={{
            position: 'absolute',
            width: '560px', height: '560px',
            borderRadius: '50%',
            border: mode === 'dark' ? '1px dashed rgba(20, 184, 166, 0.15)' : '1px dashed rgba(20, 184, 166, 0.25)',
            pointerEvents: 'none',
            animation: 'spinSmooth 90s linear infinite reverse'
          }} />

          {/* SVG Connecting Rays */}
          <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
            {NODES.map((node) => {
              const rad = (node.angle * Math.PI) / 180;
              const isActive = activeNode?.id === node.id;
              const rx = 50 + Math.cos(rad) * node.distance;
              const ry = 50 + Math.sin(rad) * (node.distance * 0.85);

              return (
                <g key={node.id}>
                  <line 
                    x1="50%" 
                    y1="50%" 
                    x2={`${rx}%`} 
                    y2={`${ry}%`} 
                    stroke={isActive ? node.color : (mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : 'rgba(20, 184, 166, 0.25)')} 
                    strokeWidth={isActive ? '2.5' : '1.2'}
                    strokeDasharray={isActive ? 'none' : '4 4'}
                    style={{ transition: 'all 0.3s ease' }}
                  />
                  {isActive && (
                    <circle cx={`${rx}%`} cy={`${ry}%`} r="6" fill={node.color}>
                      <animate attributeName="r" values="4;10;4" dur="1.2s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite" />
                    </circle>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Central Core Hub */}
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 10,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              cursor: 'pointer',
              transition: 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)'
            }}
            onClick={() => soundFx.playChime()}
          >
            <Box
              sx={{
                width: 110,
                height: 110,
                borderRadius: '50%',
                background: mode === 'dark'
                  ? 'radial-gradient(circle, rgba(20, 184, 166, 0.3) 0%, rgba(15, 29, 33, 0.95) 70%)'
                  : 'radial-gradient(circle, rgba(20, 184, 166, 0.2) 0%, #FFFFFF 70%)',
                border: pulseCore ? '2px solid #14B8A6' : '2px solid rgba(20, 184, 166, 0.5)',
                boxShadow: pulseCore ? '0 0 35px rgba(20, 184, 166, 0.6)' : '0 0 15px rgba(20, 184, 166, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                transition: 'all 0.5s ease',
                '&:hover': {
                  transform: 'scale(1.1)',
                  boxShadow: '0 0 45px rgba(20, 184, 166, 0.8)'
                }
              }}
            >
              <Box sx={{
                position: 'absolute',
                inset: -8,
                borderRadius: '50%',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                animation: 'spinSmooth 12s linear infinite'
              }} />
              <Zap size={44} color="#14B8A6" />
            </Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 800, mt: 1.5, fontFamily: "'Outfit', sans-serif", color: mode === 'dark' ? '#F8FAFC' : '#0F1D21', letterSpacing: '0.05em' }}>
              PADDLE OCR CORE
            </Typography>
            <Chip 
              label="v2.8 ENGINE ONLINE" 
              size="small" 
              sx={{ 
                height: 20, 
                fontSize: '0.65rem', 
                background: 'rgba(20, 184, 166, 0.15)', 
                color: '#14B8A6', 
                border: '1px solid rgba(20, 184, 166, 0.4)',
                fontWeight: 700,
                mt: 0.5
              }} 
            />
          </Box>

          {/* Orbital Nodes */}
          {NODES.map((node) => {
            const rad = (node.angle * Math.PI) / 180;
            const rx = 50 + Math.cos(rad) * node.distance;
            const ry = 50 + Math.sin(rad) * (node.distance * 0.85);
            const isActive = activeNode?.id === node.id;

            return (
              <Box
                key={node.id}
                onMouseEnter={() => handleNodeHover(node)}
                onMouseLeave={() => handleNodeHover(null)}
                onClick={() => handleNodeClick(node)}
                sx={{
                  position: 'absolute',
                  top: `${ry}%`,
                  left: `${rx}%`,
                  transform: 'translate(-50%, -50%)',
                  zIndex: isActive ? 30 : 20,
                  cursor: 'pointer',
                  transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                  '&:hover': {
                    transform: 'translate(-50%, -50%) scale(1.15)',
                  }
                }}
              >
                <Card
                  sx={{
                    borderRadius: '16px',
                    background: mode === 'dark'
                      ? (isActive ? 'rgba(15, 29, 33, 0.95)' : 'rgba(15, 29, 33, 0.85)')
                      : (isActive ? '#FFFFFF' : 'rgba(255, 255, 255, 0.95)'),
                    backdropFilter: 'blur(12px)',
                    border: isActive ? `2px solid ${node.color}` : (mode === 'dark' ? '1px solid rgba(20, 184, 166, 0.2)' : '1px solid rgba(0, 0, 0, 0.08)'),
                    boxShadow: isActive ? `0 10px 30px ${node.color}40` : (mode === 'dark' ? '0 4px 15px rgba(0,0,0,0.3)' : '0 4px 15px rgba(0,0,0,0.05)'),
                    p: 1.8,
                    minWidth: 160,
                    maxWidth: 190,
                    textAlign: 'center',
                    transition: 'all 0.3s ease'
                  }}
                >
                  <Box sx={{ 
                    width: 44, 
                    height: 44, 
                    borderRadius: '12px', 
                    background: `${node.color}20`, 
                    border: `1px solid ${node.color}40`,
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    mx: 'auto',
                    mb: 1,
                    boxShadow: isActive ? `0 0 15px ${node.color}60` : 'none'
                  }}>
                    {node.icon}
                  </Box>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: mode === 'dark' ? '#F8FAFC' : '#0F1D21', fontSize: '0.85rem' }}>
                    {node.title}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', fontSize: '0.7rem', mt: 0.2 }}>
                    {node.subtitle}
                  </Typography>
                  {isActive && (
                    <Chip 
                      label={node.badge} 
                      size="small"
                      sx={{ 
                        mt: 1, 
                        height: 18, 
                        fontSize: '0.62rem', 
                        background: `${node.color}25`, 
                        color: node.color,
                        border: `1px solid ${node.color}60`,
                        fontWeight: 700
                      }} 
                    />
                  )}
                </Card>
              </Box>
            );
          })}

          {/* Active Node Detail Hover Floating Drawer */}
          {activeNode && (
            <Card
              className="animate-fade-in-up"
              sx={{
                position: 'absolute',
                bottom: 20,
                left: 20,
                zIndex: 40,
                maxWidth: 340,
                borderRadius: '16px',
                background: mode === 'dark' ? 'rgba(15, 29, 33, 0.95)' : '#FFFFFF',
                backdropFilter: 'blur(16px)',
                border: `1px solid ${activeNode.color}`,
                boxShadow: `0 15px 35px ${activeNode.color}30`,
                p: 2.5
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Chip label={activeNode.category} size="small" sx={{ background: `${activeNode.color}20`, color: activeNode.color, fontWeight: 700, fontSize: '0.65rem' }} />
                <Typography variant="caption" sx={{ color: '#22C55E', fontWeight: 700 }}>Accuracy: {activeNode.accuracy}</Typography>
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 800, color: mode === 'dark' ? '#F8FAFC' : '#0F1D21', mb: 0.5, fontSize: '1rem' }}>
                {activeNode.title}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.8rem', mb: 2 }}>
                {activeNode.description}
              </Typography>
              <Button
                fullWidth
                variant="contained"
                onClick={() => handleNodeClick(activeNode)}
                endIcon={<ArrowUpRight size={16} />}
                sx={{
                  borderRadius: '10px',
                  textTransform: 'none',
                  fontWeight: 700,
                  background: `linear-gradient(135deg, ${activeNode.color}, ${activeNode.color}cc)`,
                  boxShadow: `0 4px 15px ${activeNode.color}40`,
                  '&:hover': { background: activeNode.color }
                }}
              >
                Launch {activeNode.title}
              </Button>
            </Card>
          )}
        </Box>
      ) : (
        /* MATRIX GRID VIEW MODE */
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, gap: 2.5 }}>
          {NODES.map((node, idx) => (
            <Card
              key={node.id}
              className={`animate-fade-in-up stagger-${idx + 1}`}
              onClick={() => handleNodeClick(node)}
              onMouseEnter={() => soundFx.playHover()}
              sx={{
                borderRadius: '16px',
                background: 'rgba(17, 24, 39, 0.75)',
                backdropFilter: 'blur(12px)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                p: 2.5,
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                '&:hover': {
                  transform: 'translateY(-6px)',
                  borderColor: node.color,
                  boxShadow: `0 15px 30px ${node.color}25`
                }
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ p: 1.5, borderRadius: '12px', background: `${node.color}20`, border: `1px solid ${node.color}40` }}>
                  {node.icon}
                </Box>
                <Chip label={node.badge} size="small" sx={{ background: 'rgba(255,255,255,0.06)', color: 'text.secondary', fontSize: '0.65rem' }} />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 800, color: '#F8FAFC', mb: 0.5, fontSize: '0.95rem' }}>
                {node.title}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.78rem', mb: 2 }}>
                {node.subtitle}
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pt: 1, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <Typography variant="caption" sx={{ color: '#22C55E', fontWeight: 600 }}>{node.accuracy}</Typography>
                <ArrowUpRight size={16} color={node.color} />
              </Box>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
};
