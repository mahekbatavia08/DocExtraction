import React, { useRef, useState, useEffect } from 'react';
import { Box, Typography, Tooltip, IconButton, Switch, FormControlLabel } from '@mui/material';
import { ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff } from 'lucide-react';
import { OCRResultItem } from '../types';

interface BoundingBoxOverlayProps {
  imageSrc: string;
  imageSize: number[]; // [width, height]
  results: OCRResultItem[];
  selectedId?: number | null;
  onSelectBox?: (id: number) => void;
}

export const BoundingBoxOverlay: React.FC<BoundingBoxOverlayProps> = ({
  imageSrc,
  imageSize,
  results,
  selectedId,
  onSelectBox,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showBoxes, setShowBoxes] = useState(true);

  const containerRef = useRef<HTMLDivElement>(null);

  const imgWidth = imageSize[0] || 800;
  const imgHeight = imageSize[1] || 600;

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 4));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.25));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUpOrLeave = () => {
    setIsDragging(false);
  };

  return (
    <Box sx={{ position: 'relative', width: '100%', overflow: 'hidden', borderRadius: '16px', background: '#020617', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
      {/* Zoom Controls */}
      <Box 
        sx={{ 
          position: 'absolute', 
          top: 16, 
          right: 16, 
          zIndex: 10, 
          display: 'flex', 
          alignItems: 'center',
          gap: 1, 
          background: 'rgba(15, 23, 42, 0.85)', 
          backdropFilter: 'blur(10px)', 
          p: 0.5, 
          px: 1.5,
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <FormControlLabel
          control={
            <Switch 
              checked={showBoxes} 
              onChange={(e) => setShowBoxes(e.target.checked)} 
              size="small" 
              color="success" 
            />
          }
          label={<Typography variant="caption" sx={{ color: 'white', fontWeight: 600 }}>Boxes</Typography>}
          sx={{ m: 0, mr: 1 }}
        />
        <Tooltip title="Zoom In">
          <IconButton className="button-spring" size="small" onClick={handleZoomIn} sx={{ color: 'white' }}>
            <ZoomIn size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out">
          <IconButton className="button-spring" size="small" onClick={handleZoomOut} sx={{ color: 'white' }}>
            <ZoomOut size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Reset View">
          <IconButton className="button-spring" size="small" onClick={handleResetZoom} sx={{ color: 'white' }}>
            <RotateCcw size={18} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Main Image Container */}
      <Box 
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUpOrLeave}
        onMouseLeave={handleMouseUpOrLeave}
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          overflow: 'hidden', 
          height: '500px',
          p: 2,
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
      >
        <Box 
          sx={{ 
            position: 'relative', 
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, 
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
            display: 'inline-block',
          }}
        >
          {/* Base Image */}
          <img
            src={imageSrc.startsWith('data:') || imageSrc.startsWith('blob:') || imageSrc.startsWith('http') ? imageSrc : `data:image/jpeg;base64,${imageSrc}`}
            alt="OCR Target Preview"
            style={{
              maxWidth: '100%',
              height: 'auto',
              display: 'block',
              borderRadius: '8px',
            }}
          />

          {/* SVG Overlay for Bounding Boxes */}
          <svg
            viewBox={`0 0 ${imgWidth} ${imgHeight}`}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
              opacity: showBoxes ? 1 : 0,
              transition: 'opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            {results.map((res, index) => {
              const pointsStr = res.bbox.map((pt) => `${pt[0]},${pt[1]}`).join(' ');
              const isSelected = selectedId === res.id;

              return (
                <g key={res.id} style={{ pointerEvents: 'auto', cursor: 'pointer' }} onClick={() => onSelectBox?.(res.id)}>
                  {/* Bounding Box Polygon */}
                  <polygon
                    className="animate-svg-draw"
                    points={pointsStr}
                    fill={isSelected ? 'rgba(16, 185, 129, 0.35)' : 'rgba(16, 185, 129, 0.12)'}
                    stroke={isSelected ? '#00ff66' : '#10b981'}
                    strokeWidth={isSelected ? 4 : 2}
                    style={{ transition: 'all 0.2s ease-in-out', animationDelay: `${index * 50}ms` }}
                  />

                  {/* Top Corner Label */}
                  {res.bbox[0] && (
                    <g transform={`translate(${res.bbox[0][0]}, ${Math.max(20, res.bbox[0][1] - 8)})`} className="animate-fade-in-up" style={{ animationDelay: `${index * 50}ms`, opacity: 0 }}>
                      <rect
                        x="-4"
                        y="-14"
                        width={Math.max(60, res.text.length * 9)}
                        height="18"
                        rx="4"
                        fill="rgba(15, 23, 42, 0.9)"
                        stroke={isSelected ? '#00ff66' : '#10b981'}
                        strokeWidth="1"
                      />
                      <text
                        x="0"
                        y="-1"
                        fill="#00ff66"
                        fontSize="12"
                        fontWeight="bold"
                        fontFamily="sans-serif"
                      >
                        #{res.id} {res.text.slice(0, 10)} ({(res.confidence * 100).toFixed(0)}%)
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </svg>
        </Box>
      </Box>
    </Box>
  );
};
