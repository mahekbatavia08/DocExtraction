import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Card, Chip, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { 
  CreditCard, ShieldCheck, UserCheck, Building, FileText, 
  Camera, Layers, ArrowUpRight, Zap, Sparkles, Compass, Grid, Activity
} from 'lucide-react';
import { soundFx } from '../utils/soundEffects';

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
    icon: <CreditCard size={22} color="#EF4444" />,
    color: '#EF4444',
    angle: 225,
    distance: 38,
    badge: 'PCI Compliance',
    accuracy: '99.9%',
    description: 'Safely extract cardholder name, expiry date, and masked 16-digit card number.'
  },
  {
    id: 'live-camera',
    title: 'Live Camera OCR',
    subtitle: 'Real-time Video Quality Gate',
    category: 'Realtime',
    path: '/live-camera',
    icon: <Camera size={22} color="#6366F1" />,
    color: '#6366F1',
    angle: 270,
    distance: 36,
    badge: 'Blur Quality Gate',
    accuracy: '60 FPS Live',
    description: 'Continuous quality scoring for webcam feed with laplacian blur & brightness detection.'
  },
  {
    id: 'upload-image',
    title: 'Multi-Doc Queue',
    subtitle: 'Batch PDF & Image Engine',
    category: 'Batch System',
    path: '/upload-image',
    icon: <Layers size={22} color="#22C55E" />,
    color: '#22C55E',
    angle: 315,
    distance: 38,
    badge: 'Parallel Queue',
    accuracy: 'Batch Queue',
    description: 'Drag & drop multiple files or multi-page PDFs with real-time process pipeline logs.'
  }
];

export const ConstellationHub: React.FC = () => {
  const navigate = useNavigate();
  const [activeNode, setActiveNode] = useState<ConstellationNode | null>(null);
  const [viewMode, setViewMode] = useState<'spatial' | 'grid'>('spatial');
  const [pulseCore, setPulseCore] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setPulseCore(prev => !prev);
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const handleNodeClick = (node: ConstellationNode) => {
    soundFx.playChime();
    navigate(node.path);
  };

  const handleNodeHover = (node: ConstellationNode | null) => {
    if (node) {
      soundFx.playHover();
    }
    setActiveNode(node);
  };

  return (
    <Box sx={{ position: 'relative', width: '100%', py: 3 }}>
      {/* Top Switcher Bar */}
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
            background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(124, 58, 237, 0.2))',
            border: '1px solid rgba(37, 99, 235, 0.3)',
            display: 'flex',
            alignItems: 'center'
          }}>
            <Sparkles size={20} color="#2563EB" />
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif", letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #F8FAFC, #94A3B8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Spatial Document Galaxy
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', display: 'flex', alignItems: 'center', gap: 0.8 }}>
              <Activity size={12} color="#2563EB" /> Interactive Point-Line-Plane Neural Matrix • Select any node to activate OCR
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, background: 'rgba(17, 24, 39, 0.7)', p: 0.6, borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <Button
            size="small"
            onClick={() => { soundFx.playClick(); setViewMode('spatial'); }}
            startIcon={<Compass size={16} />}
            sx={{
              borderRadius: '8px',
              textTransform: 'none',
              fontWeight: 600,
              px: 2,
              color: viewMode === 'spatial' ? '#2563EB' : 'text.secondary',
              background: viewMode === 'spatial' ? 'rgba(37, 99, 235, 0.15)' : 'transparent',
              border: viewMode === 'spatial' ? '1px solid rgba(37, 99, 235, 0.3)' : '1px solid transparent',
              '&:hover': { background: 'rgba(37, 99, 235, 0.2)' }
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
              fontWeight: 600,
              px: 2,
              color: viewMode === 'grid' ? '#2563EB' : 'text.secondary',
              background: viewMode === 'grid' ? 'rgba(37, 99, 235, 0.15)' : 'transparent',
              border: viewMode === 'grid' ? '1px solid rgba(37, 99, 235, 0.3)' : '1px solid transparent',
              '&:hover': { background: 'rgba(37, 99, 235, 0.2)' }
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
            background: 'radial-gradient(circle at 50% 50%, rgba(17, 24, 39, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
            p: 2
          }}
        >
          {/* Subtle Orbital Circles background */}
          <Box sx={{
            position: 'absolute',
            width: '420px', height: '420px',
            borderRadius: '50%',
            border: '1px dashed rgba(255, 255, 255, 0.08)',
            pointerEvents: 'none',
            animation: 'spinSmooth 60s linear infinite'
          }} />
          <Box sx={{
            position: 'absolute',
            width: '560px', height: '560px',
            borderRadius: '50%',
            border: '1px dashed rgba(37, 99, 235, 0.12)',
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
                    stroke={isActive ? node.color : 'rgba(255, 255, 255, 0.12)'} 
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
                background: 'radial-gradient(circle, rgba(37, 99, 235, 0.3) 0%, rgba(17, 24, 39, 0.95) 70%)',
                border: pulseCore ? '2px solid #2563EB' : '2px solid rgba(37, 99, 235, 0.5)',
                boxShadow: pulseCore ? '0 0 35px rgba(37, 99, 235, 0.6)' : '0 0 15px rgba(37, 99, 235, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                transition: 'all 0.5s ease',
                '&:hover': {
                  transform: 'scale(1.1)',
                  boxShadow: '0 0 45px rgba(37, 99, 235, 0.8)'
                }
              }}
            >
              <Box sx={{
                position: 'absolute',
                inset: -8,
                borderRadius: '50%',
                border: '1px solid rgba(124, 58, 237, 0.3)',
                animation: 'spinSmooth 12s linear infinite'
              }} />
              <Zap size={44} color="#2563EB" />
            </Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 800, mt: 1.5, fontFamily: "'Outfit', sans-serif", color: '#F8FAFC', letterSpacing: '0.05em' }}>
              PADDLE OCR CORE
            </Typography>
            <Chip 
              label="v2.8 ENGINE ONLINE" 
              size="small" 
              sx={{ 
                height: 20, 
                fontSize: '0.65rem', 
                background: 'rgba(37, 99, 235, 0.15)', 
                color: '#2563EB', 
                border: '1px solid rgba(37, 99, 235, 0.4)',
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
                    background: isActive ? 'rgba(17, 24, 39, 0.95)' : 'rgba(17, 24, 39, 0.8)',
                    backdropFilter: 'blur(12px)',
                    border: isActive ? `2px solid ${node.color}` : '1px solid rgba(255, 255, 255, 0.08)',
                    boxShadow: isActive ? `0 10px 30px ${node.color}40` : '0 4px 15px rgba(0,0,0,0.3)',
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
                  <Typography variant="body2" sx={{ fontWeight: 700, color: '#F8FAFC', fontSize: '0.85rem' }}>
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
                background: 'rgba(17, 24, 39, 0.95)',
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
              <Typography variant="h6" sx={{ fontWeight: 800, color: '#F8FAFC', mb: 0.5, fontSize: '1rem' }}>
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
