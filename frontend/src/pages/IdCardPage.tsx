import React from 'react';
import { UserCheck } from 'lucide-react';
import { DocumentOCRModule } from '../components/DocumentOCRModule';
import { parseIDCard } from '../utils/documentExtractors';

export const IdCardPage: React.FC = () => {
  return (
    <DocumentOCRModule
      title="ID Card OCR"
      description="Extract School, College, and Employee ID attributes (Name, ID Number, Department, Class)."
      badgeLabel="Identity Card"
      badgeColor="primary"
      icon={<UserCheck size={28} color="#10b981" />}
      parseSpecializedFields={parseIDCard}
    />
  );
};
