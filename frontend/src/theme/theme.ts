import { createTheme, ThemeOptions } from '@mui/material/styles';

const getThemeOptions = (mode: 'dark' | 'light'): ThemeOptions => ({
  palette: {
    mode,
    primary: {
      main: '#2563EB', // Enterprise Royal Blue
      light: '#3B82F6',
      dark: '#1D4ED8',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#6366F1', // Indigo Accent
      light: '#818CF8',
      dark: '#4F46E5',
      contrastText: '#FFFFFF',
    },
    success: {
      main: '#10B981', // Clean Emerald
      light: '#34D399',
      dark: '#059669',
    },
    warning: {
      main: '#F59E0B', // Warm Amber
      light: '#FBBF24',
      dark: '#D97706',
    },
    error: {
      main: '#EF4444', // Clean Rose Red
      light: '#F87171',
      dark: '#DC2626',
    },
    background: {
      default: mode === 'dark' ? '#090D16' : '#F8FAFC', // Deep Charcoal / Pristine Canvas
      paper: mode === 'dark' ? '#1E293B' : '#FFFFFF',   // Slate Paper / Pure White Card
    },
    text: {
      primary: mode === 'dark' ? '#F8FAFC' : '#0F172A',
      secondary: mode === 'dark' ? '#94A3B8' : '#64748B',
    },
    divider: mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : '#E2E8F0',
  },
  typography: {
    fontFamily: '"Inter", "Outfit", system-ui, -apple-system, sans-serif',
    h1: { fontFamily: '"Outfit", sans-serif', fontWeight: 700, color: mode === 'dark' ? '#F8FAFC' : '#0F172A' },
    h2: { fontFamily: '"Outfit", sans-serif', fontWeight: 700, color: mode === 'dark' ? '#F8FAFC' : '#0F172A' },
    h3: { fontFamily: '"Outfit", sans-serif', fontWeight: 700, color: mode === 'dark' ? '#F8FAFC' : '#0F172A' },
    h4: { fontFamily: '"Outfit", sans-serif', fontWeight: 700, color: mode === 'dark' ? '#F8FAFC' : '#0F172A' },
    h5: { fontFamily: '"Outfit", sans-serif', fontWeight: 600, color: mode === 'dark' ? '#F8FAFC' : '#0F172A' },
    h6: { fontFamily: '"Outfit", sans-serif', fontWeight: 600, color: mode === 'dark' ? '#F8FAFC' : '#0F172A' },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
    button: { fontFamily: '"Inter", sans-serif', fontWeight: 600, textTransform: 'none' },
  },
  shape: {
    borderRadius: 14,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: mode === 'dark' ? '#090D16' : '#F8FAFC',
          color: mode === 'dark' ? '#F8FAFC' : '#0F172A',
          minHeight: '100vh',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: mode === 'dark' ? '#1E293B' : '#FFFFFF',
          border: mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #E2E8F0',
          boxShadow: mode === 'dark' 
            ? '0 4px 12px rgba(0, 0, 0, 0.25)'
            : '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.06)',
          transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
            borderColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.18)' : '#CBD5E1',
            boxShadow: mode === 'dark' 
              ? '0 8px 20px rgba(0, 0, 0, 0.35)'
              : '0 4px 12px rgba(0, 0, 0, 0.08)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '8px 18px',
          fontWeight: 600,
          transition: 'all 0.2s ease',
          '&:active': {
            transform: 'scale(0.98)',
          },
        },
        containedPrimary: {
          background: '#2563EB',
          color: '#FFFFFF',
          boxShadow: '0 1px 2px rgba(37, 99, 235, 0.2)',
          '&:hover': {
            background: '#1D4ED8',
            boxShadow: '0 4px 10px rgba(37, 99, 235, 0.3)',
          },
        },
        containedSecondary: {
          background: '#4F46E5',
          color: '#FFFFFF',
          boxShadow: '0 1px 2px rgba(79, 70, 229, 0.2)',
          '&:hover': {
            background: '#4338CA',
            boxShadow: '0 4px 10px rgba(79, 70, 229, 0.3)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 600,
        },
      },
    },
  },
});

export const theme = createTheme(getThemeOptions('dark'));
export const lightTheme = createTheme(getThemeOptions('light'));
