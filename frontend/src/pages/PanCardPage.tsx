import React from 'react';
import { CreditCard } from 'lucide-react';
import { DocumentOCRModule } from '../components/DocumentOCRModule';
import { parsePANCard } from '../utils/documentExtractors';

export const PanCardPage: React.FC = () => {
  return (
    <DocumentOCRModule
      title="PAN Card OCR"
      description="Extract PAN Number, Name, Father's Name, and Date of Birth with strict regex validation."
      badgeLabel="PAN Validated"
      badgeColor="success"
      icon={<CreditCard size={28} color="#10b981" />}
      parseSpecializedFields={parsePANCard}
    />
  );
};
