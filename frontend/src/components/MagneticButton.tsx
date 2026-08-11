import React, { useRef, useState, useEffect } from 'react';
import { Box } from '@mui/material';

interface MagneticButtonProps {
  children: React.ReactElement;
  strength?: number;
}

export const MagneticButton: React.FC<MagneticButtonProps> = ({ children, strength = 15 }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const handleMouseMove = (e: MouseEvent) => {
      const { clientX, clientY } = e;
      const { left, top, width, height } = el.getBoundingClientRect();
      
      const x = clientX - (left + width / 2);
      const y = clientY - (top + height / 2);

      // Pull if mouse is near
      const dist = Math.sqrt(x * x + y * y);
      if (dist < width * 0.8) {
        setPosition({ x: (x / width) * strength, y: (y / height) * strength });
      } else {
        setPosition({ x: 0, y: 0 });
      }
    };

    const handleMouseLeave = () => {
      setPosition({ x: 0, y: 0 });
    };

    window.addEventListener('mousemove', handleMouseMove);
    el.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      el.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [strength]);

  return (
    <Box
      ref={ref}
      sx={{
        display: 'inline-flex',
        transform: `translate(${position.x}px, ${position.y}px)`,
        transition: position.x === 0 && position.y === 0 ? 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)' : 'transform 0.1s linear',
        width: '100%',
        justifyContent: 'inherit',
      }}
    >
      {children}
    </Box>
  );
};
