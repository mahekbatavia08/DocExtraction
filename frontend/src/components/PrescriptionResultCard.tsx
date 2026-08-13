import React, { useRef } from 'react';
import { Box, Card, CardContent, Typography, Button, Grid, Paper } from '@mui/material';
import { Download } from 'lucide-react';

export interface MedicineItem {
  name: string;
  dosage?: string;
  strength?: string;
  frequency?: string;
  duration?: string;
  instructions?: string;
}

export interface PrescriptionResultCardProps {
  patientName?: string;
  doctorName?: string;
  date?: string;
  medicines?: MedicineItem[];
  diagnosis?: string;
  notes?: string;
  rawText?: string;
  onExportPdf?: () => void;
}

export const PrescriptionResultCard: React.FC<PrescriptionResultCardProps> = ({
  patientName = 'Not specified',
  doctorName = 'Not specified',
  date = 'Not specified',
  medicines = [],
  diagnosis,
  notes,
  rawText,
  onExportPdf
}) => {
  const cardRef = useRef<HTMLDivElement>(null);

  const handlePrintPdf = () => {
    if (onExportPdf) {
      onExportPdf();
      return;
    }

    const printContent = cardRef.current;
    if (!printContent) return;

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Prescription Result - ${patientName}</title>
          <style>
            body { font-family: 'Inter', system-ui, -apple-system, sans-serif; padding: 40px; background: #ffffff; color: #0f172a; }
            .header-title { font-size: 24px; font-weight: 800; margin-bottom: 24px; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }
            .summary-row { display: flex; justify-content: space-between; margin-bottom: 32px; background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; }
            .summary-col { flex: 1; }
            .label { font-size: 13px; font-weight: 600; color: #64748b; margin-bottom: 4px; }
            .val { font-size: 18px; font-weight: 800; color: #0f172a; }
            .section-title { font-size: 20px; font-weight: 800; margin-top: 24px; margin-bottom: 16px; color: #0f172a; }
            .med-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 16px; }
            .med-name { font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 12px; }
            .grid-row { display: flex; flex-wrap: wrap; gap: 24px; margin-bottom: 8px; }
            .field-pair { font-size: 14px; }
            .field-label { color: #64748b; font-weight: 600; }
            .field-val { font-weight: 800; color: #0f172a; }
            .notes-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; font-size: 15px; font-weight: 600; color: #334155; line-height: 1.6; }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
          <script>
            window.onload = function() { window.print(); window.close(); };
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  const additionalNotesText = [
    diagnosis ? `Diagnosis: ${diagnosis}` : null,
    notes ? `Notes: ${notes}` : null,
    (!diagnosis && !notes && rawText) ? `Summary: ${rawText.slice(0, 300)}...` : null
  ].filter(Boolean).join('. ');

  return (
    <Card
      sx={{
        borderRadius: '16px',
        border: '1px solid rgba(226, 232, 240, 0.8)',
        background: '#ffffff',
        boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
        color: '#0f172a',
        overflow: 'hidden',
        mt: 3
      }}
    >
      <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
        <Box ref={cardRef}>
          {/* Header Row */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3.5 }}>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em', fontSize: '1.45rem' }}>
              Your Extracted Prescription Result
            </Typography>
            <Button
              variant="outlined"
              onClick={handlePrintPdf}
              startIcon={<Download size={16} />}
              sx={{
                borderRadius: '8px',
                borderColor: '#cbd5e1',
                color: '#0f172a',
                fontWeight: 700,
                textTransform: 'none',
                px: 2.5,
                py: 0.8,
                '&:hover': {
                  borderColor: '#94a3b8',
                  background: '#f8fafc'
                }
              }}
            >
              Export PDF
            </Button>
          </Box>

          {/* Patient / Doctor / Date Summary Row */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={4}>
              <Box>
                <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600, fontSize: '0.85rem', display: 'block', mb: 0.5 }}>
                  Patient Name
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 800, color: '#0f172a', fontSize: '1.25rem' }}>
                  {patientName && patientName !== 'Not Found' ? patientName : 'Not specified'}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Box>
                <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600, fontSize: '0.85rem', display: 'block', mb: 0.5 }}>
                  Doctor Name
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 800, color: '#0f172a', fontSize: '1.25rem' }}>
                  {doctorName && doctorName !== 'Not Found' ? doctorName : 'Not specified'}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Box>
                <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600, fontSize: '0.85rem', display: 'block', mb: 0.5 }}>
                  Date
                </Typography>
                <Typography variant="h6" sx={{ fontWeight: 800, color: '#0f172a', fontSize: '1.25rem' }}>
                  {date && date !== 'Not Found' ? date : 'Not specified'}
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* Prescribed Medications Section */}
          <Typography variant="h6" sx={{ fontWeight: 800, color: '#0f172a', mb: 2, fontSize: '1.25rem' }}>
            Prescribed Medications
          </Typography>

          {medicines && medicines.length > 0 ? (
            medicines.map((med, idx) => (
              <Paper
                key={idx}
                elevation={0}
                sx={{
                  p: 3,
                  mb: 2,
                  borderRadius: '12px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0'
                }}
              >
                <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0f172a', fontSize: '1.15rem', mb: 1.5 }}>
                  {med.name || 'Prescribed Medicine'}
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 600 }}>
                      Dosage: <Typography component="span" sx={{ fontWeight: 800, color: '#0f172a' }}>{med.dosage || med.strength || 'As prescribed'}</Typography>
                    </Typography>
                  </Grid>

                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 600 }}>
                      Frequency: <Typography component="span" sx={{ fontWeight: 800, color: '#0f172a' }}>{med.frequency || 'Once daily'}</Typography>
                    </Typography>
                  </Grid>

                  {med.duration && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 600 }}>
                        Duration: <Typography component="span" sx={{ fontWeight: 800, color: '#0f172a' }}>{med.duration}</Typography>
                      </Typography>
                    </Grid>
                  )}

                  {med.instructions && (
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 600 }}>
                        Instructions: <Typography component="span" sx={{ fontWeight: 800, color: '#0f172a' }}>{med.instructions}</Typography>
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </Paper>
            ))
          ) : (
            <Paper
              elevation={0}
              sx={{ p: 3, mb: 2, borderRadius: '12px', background: '#f8fafc', border: '1px solid #e2e8f0' }}
            >
              <Typography variant="body2" sx={{ color: '#64748b', fontWeight: 600 }}>
                No explicit medication list extracted.
              </Typography>
            </Paper>
          )}

          {/* Additional Notes Section */}
          <Typography variant="h6" sx={{ fontWeight: 800, color: '#0f172a', mt: 3, mb: 1.5, fontSize: '1.25rem' }}>
            Additional Notes
          </Typography>

          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              borderRadius: '12px',
              background: '#f8fafc',
              border: '1px solid #e2e8f0'
            }}
          >
            <Typography variant="body2" sx={{ color: '#334155', fontWeight: 600, lineHeight: 1.6, fontSize: '0.95rem' }}>
              {additionalNotesText || 'No additional clinical diagnosis notes extracted.'}
            </Typography>
          </Paper>
        </Box>
      </CardContent>
    </Card>
  );
};
