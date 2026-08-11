import React from 'react';
import { Box, Typography } from '@mui/material';
import { soundFx } from '../utils/soundEffects';

interface LogoProps {
  size?: 'small' | 'medium' | 'large';
  showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ size = 'medium', showText = true }) => {
  const iconSize = size === 'small' ? 28 : size === 'medium' ? 36 : 48;
  const fontSize = size === 'small' ? '1rem' : size === 'medium' ? '1.25rem' : '1.75rem';

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1.5,
        cursor: 'pointer',
        userSelect: 'none'
      }}
      onClick={() => soundFx.playChime()}
    >
      <Box
        sx={{
          width: iconSize,
          height: iconSize,
          borderRadius: size === 'small' ? '8px' : '12px',
          background: 'linear-gradient(135deg, #2563EB 0%, #7C3AED 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 14px rgba(37, 99, 235, 0.35)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
          '&:hover': {
            transform: 'scale(1.08) rotate(3deg)',
            boxShadow: '0 8px 24px rgba(124, 58, 237, 0.5)',
          }
        }}
      >
        <svg width={iconSize * 0.65} height={iconSize * 0.65} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 7V5C3 3.89543 3.89543 3 5 3H7" stroke="#F8FAFC" strokeWidth="2" strokeLinecap="round"/>
          <path d="M17 3H19C20.1046 3 21 3.89543 21 5V7" stroke="#F8FAFC" strokeWidth="2" strokeLinecap="round"/>
          <path d="M21 17V19C21 20.1046 20.1046 21 19 21H17" stroke="#F8FAFC" strokeWidth="2" strokeLinecap="round"/>
          <path d="M7 21H5C3.89543 21 3 20.1046 3 19V17" stroke="#F8FAFC" strokeWidth="2" strokeLinecap="round"/>
          <line x1="7" y1="9" x2="17" y2="9" stroke="#60A5FA" strokeWidth="2" strokeLinecap="round"/>
          <line x1="7" y1="13" x2="14" y2="13" stroke="#A78BFA" strokeWidth="2" strokeLinecap="round"/>
          <line x1="7" y1="17" x2="17" y2="17" stroke="#F8FAFC" strokeWidth="2" strokeLinecap="round"/>
          <circle cx="17" cy="13" r="1.5" fill="#22C55E"/>
        </svg>
      </Box>

      {showText && (
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Typography
            variant="h6"
            sx={{
              fontFamily: "'Outfit', sans-serif",
              fontWeight: 800,
              fontSize: fontSize,
              lineHeight: 1.1,
              letterSpacing: '-0.02em',
              background: 'linear-gradient(90deg, #F8FAFC 0%, #60A5FA 50%, #A78BFA 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            PaddleOCR AI
          </Typography>
          <Typography
            variant="caption"
            sx={{
              fontSize: '0.68rem',
              fontWeight: 700,
              color: '#94A3B8',
              letterSpacing: '0.08em',
              textTransform: 'uppercase'
            }}
          >
            Vision Matrix Dashboard
          </Typography>
        </Box>
      )}
    </Box>
  );
};
