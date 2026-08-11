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
            width: 'calc(100% - 260px)',
            maxWidth: '1600px',
            margin: '0 auto',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

