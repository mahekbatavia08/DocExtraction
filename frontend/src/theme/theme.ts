import { createTheme, ThemeOptions } from '@mui/material/styles';

const getThemeOptions = (mode: 'dark' | 'light'): ThemeOptions => ({
  palette: {
    mode,
    primary: {
      main: '#14B8A6', // Cyber Emerald Teal
      light: '#2DD4BF',
      dark: '#0F766E',
      contrastText: '#F8FAFC',
    },
    secondary: {
      main: '#8B5CF6', // Vibrant Violet
      light: '#A78BFA',
      dark: '#6D28D9',
      contrastText: '#F8FAFC',
    },
    success: {
      main: '#10B981', // Emerald Green
      light: '#34D399',
      dark: '#059669',
    },
    warning: {
      main: '#F59E0B', // Amber
      light: '#FBBF24',
      dark: '#D97706',
    },
    error: {
      main: '#EF4444', // Rose Red
      light: '#F87171',
      dark: '#DC2626',
    },
    background: {
      default: mode === 'dark' ? '#0F1D21' : '#F8FAFC', // Deep Teal-Slate
      paper: mode === 'dark' ? '#14252B' : '#FFFFFF',   // Dark Cyan Card
    },
    text: {
      primary: mode === 'dark' ? '#F8FAFC' : '#0F1D21',
      secondary: mode === 'dark' ? '#94A3B8' : '#475569',
    },
    divider: mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
  },
  typography: {
    fontFamily: '"Inter", "Outfit", system-ui, sans-serif',
    h1: { fontFamily: '"Outfit", sans-serif', fontWeight: 800 },
    h2: { fontFamily: '"Outfit", sans-serif', fontWeight: 800 },
    h3: { fontFamily: '"Outfit", sans-serif', fontWeight: 800 },
    h4: { fontFamily: '"Outfit", sans-serif', fontWeight: 800 },
    h5: { fontFamily: '"Outfit", sans-serif', fontWeight: 700 },
    h6: { fontFamily: '"Outfit", sans-serif', fontWeight: 700 },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
    button: { fontFamily: '"Inter", sans-serif', fontWeight: 700, textTransform: 'none' },
  },
  shape: {
    borderRadius: 16,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: mode === 'dark' ? '#0F1D21' : '#F8FAFC',
          color: mode === 'dark' ? '#F8FAFC' : '#0F1D21',
          minHeight: '100vh',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: mode === 'dark' ? 'rgba(20, 37, 43, 0.85)' : 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(20px) saturate(160%)',
          WebkitBackdropFilter: 'blur(20px) saturate(160%)',
          border: mode === 'dark' ? '1px solid rgba(20, 184, 166, 0.15)' : '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: mode === 'dark' 
            ? '0 10px 30px -5px rgba(0, 0, 0, 0.4), inset 0 1px 0 0 rgba(255, 255, 255, 0.08)'
            : '0 10px 30px -5px rgba(0, 0, 0, 0.05), inset 0 1px 0 0 rgba(255, 255, 255, 0.8)',
          transition: 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
          '&:hover': {
            transform: 'translateY(-4px)',
            borderColor: mode === 'dark' ? 'rgba(20, 184, 166, 0.5)' : 'rgba(20, 184, 166, 0.3)',
            boxShadow: mode === 'dark' 
              ? '0 20px 40px -10px rgba(20, 184, 166, 0.3), 0 0 25px rgba(139, 92, 246, 0.2)'
              : '0 20px 40px -10px rgba(20, 184, 166, 0.15)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '8px 20px',
          fontWeight: 700,
          transition: 'all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
          '&:active': {
            transform: 'scale(0.96)',
          },
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #14B8A6 0%, #0F766E 100%)',
          color: '#F8FAFC',
          boxShadow: '0 4px 14px rgba(20, 184, 166, 0.35)',
          '&:hover': {
            background: 'linear-gradient(135deg, #2DD4BF 0%, #14B8A6 100%)',
            boxShadow: '0 8px 25px rgba(20, 184, 166, 0.5)',
          },
        },
        containedSecondary: {
          background: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
          boxShadow: '0 4px 14px rgba(139, 92, 246, 0.35)',
          '&:hover': {
            background: 'linear-gradient(135deg, #A78BFA 0%, #8B5CF6 100%)',
            boxShadow: '0 8px 25px rgba(139, 92, 246, 0.5)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 700,
        },
      },
    },
  },
});

export const theme = createTheme(getThemeOptions('dark'));
export const lightTheme = createTheme(getThemeOptions('light'));
