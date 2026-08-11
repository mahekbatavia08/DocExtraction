import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { DocumentOCRModule } from '../components/DocumentOCRModule';
import { parseAadhaarCard } from '../utils/documentExtractors';

export const AadhaarCardPage: React.FC = () => {
  return (
    <DocumentOCRModule
      title="Aadhaar Card OCR"
      description="Extract Aadhaar UID (Masked), Name, DOB, Gender, and Address with Verhoeff validation."
      badgeLabel="UID Masked"
      badgeColor="info"
      icon={<ShieldCheck size={28} color="#10b981" />}
      parseSpecializedFields={parseAadhaarCard}
    />
  );
};
