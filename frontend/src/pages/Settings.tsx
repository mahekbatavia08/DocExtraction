import React, { useEffect, useState } from 'react';
import { Box, Card, CardContent, Typography, Grid, Switch, FormControlLabel, Slider, Select, MenuItem, FormControl, InputLabel, Button, Alert, Chip, Divider } from '@mui/material';
import { Cpu, Settings as SettingsIcon, ShieldCheck, RefreshCw } from 'lucide-react';
import { getHealth } from '../services/api';
import { HealthResponse } from '../types';

export const Settings: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [language, setLanguage] = useState('en');
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0.5);
  const [useAngleCls, setUseAngleCls] = useState(true);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  const fetchHealthStatus = async () => {
    try {
      const data = await getHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    }
  };

  useEffect(() => {
    fetchHealthStatus();
  }, []);

  const handleSaveSettings = () => {
    setSavedMsg('Settings saved successfully!');
    setTimeout(() => setSavedMsg(null), 3000);
  };

  return (
    <Box sx={{ pb: 6, maxWidth: '900px', mx: 'auto' }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, mb: 0.5 }}>
          OCR Model Engine Settings
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Configure PaddleOCR model parameters, languages, and hardware runtime.
        </Typography>
      </Box>

      {savedMsg && (
        <Alert severity="success" sx={{ mb: 3, borderRadius: '12px' }}>
          {savedMsg}
        </Alert>
      )}

      {/* Engine Status Summary */}
      <Card sx={{ mb: 3, borderRadius: '16px' }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box sx={{ p: 1, borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)' }}>
                <Cpu size={22} color="#10b981" />
              </Box>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Active Engine: {health ? health.engine_type : 'Connecting...'}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Model Loaded Once on Startup (Singleton LifeCycle)
                </Typography>
              </Box>
            </Box>

            <Chip
              label={health?.ocr_engine_loaded ? 'Engine Loaded' : 'Offline'}
              color={health?.ocr_engine_loaded ? 'success' : 'error'}
              variant="outlined"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Settings Form */}
      <Card sx={{ borderRadius: '16px' }}>
        <CardContent sx={{ p: 4 }}>
          <Grid container spacing={4}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel id="lang-select-label" sx={{ color: 'text.secondary' }}>OCR Recognition Language</InputLabel>
                <Select
                  labelId="lang-select-label"
                  value={language}
                  label="OCR Recognition Language"
                  onChange={(e) => setLanguage(e.target.value)}
                  sx={{ borderRadius: '12px' }}
                >
                  <MenuItem value="en">English (PP-OCRv4)</MenuItem>
                  <MenuItem value="ch">Chinese & English (ch_PP-OCRv4)</MenuItem>
                  <MenuItem value="latin">Latin Multilingual</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                Confidence Score Threshold ({Math.round(confidenceThreshold * 100)}%)
              </Typography>
              <Slider
                value={confidenceThreshold}
                min={0.1}
                max={0.95}
                step={0.05}
                onChange={(_, val) => setConfidenceThreshold(val as number)}
                valueLabelDisplay="auto"
                color="primary"
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.08)' }} />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={useAngleCls}
                    onChange={(e) => setUseAngleCls(e.target.checked)}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Enable Text Orientation Classifier</Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>Auto-rotates sideways or upside-down text blocks.</Typography>
                  </Box>
                }
              />
            </Grid>

            <Grid item xs={12} sx={{ textAlign: 'right', mt: 2 }}>
              <Button variant="contained" color="primary" onClick={handleSaveSettings} size="large">
                Save Configuration
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};
