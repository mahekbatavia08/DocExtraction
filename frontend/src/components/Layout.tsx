import React from 'react';
import { Box } from '@mui/material';
import { useLocation } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        <Sidebar />
        <Box 
          component="main" 
          key={location.pathname}
          className="animate-page-enter"
          sx={{ 
            flexGrow: 1, 
            p: 4, 
            width: '100%',
            maxWidth: '1600px',
            margin: '0 auto',
            transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1)'
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

