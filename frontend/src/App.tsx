import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CustomThemeProvider } from './context/ThemeContext';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import { LiveCamera } from './pages/LiveCamera';
import { UploadImage } from './pages/UploadImage';
import { UploadPdf } from './pages/UploadPdf';
import { Results } from './pages/Results';
import { Settings } from './pages/Settings';
import { AnimatedBackground } from './components/AnimatedBackground';

import { PanCardPage } from './pages/PanCardPage';
import { AadhaarCardPage } from './pages/AadhaarCardPage';
import { IdCardPage } from './pages/IdCardPage';
import { BusinessCardPage } from './pages/BusinessCardPage';
import { MedicalPrescriptionPage } from './pages/MedicalPrescriptionPage';
import { PaymentCardPage } from './pages/PaymentCardPage';
import { InvoicePage } from './pages/InvoicePage';
import { DatabaseHistory } from './pages/DatabaseHistory';

export const App: React.FC = () => {
  return (
    <CustomThemeProvider>
      <AnimatedBackground />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/pan" element={<PanCardPage />} />
            <Route path="/aadhaar" element={<AadhaarCardPage />} />
            <Route path="/id-card" element={<IdCardPage />} />
            <Route path="/business-card" element={<BusinessCardPage />} />
            <Route path="/medical-prescription" element={<MedicalPrescriptionPage />} />
            <Route path="/payment-card" element={<PaymentCardPage />} />
            <Route path="/invoice" element={<InvoicePage />} />
            <Route path="/database" element={<DatabaseHistory />} />
            <Route path="/live-camera" element={<LiveCamera />} />
            <Route path="/upload-image" element={<UploadImage />} />
            <Route path="/upload-pdf" element={<UploadPdf />} />
            <Route path="/results" element={<Results />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Router>
    </CustomThemeProvider>
  );
};
