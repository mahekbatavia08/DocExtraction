import React from 'react';
import { FileText } from 'lucide-react';
import { DocumentOCRModule } from '../components/DocumentOCRModule';
import { parseInvoice } from '../utils/documentExtractors';

export const InvoicePage: React.FC = () => {
  return (
    <DocumentOCRModule
      title="Invoice OCR"
      description="Extract Vendor Name, Invoice Number, Invoice Date, Total Amount, and GST/VAT identifiers."
      badgeLabel="Financial Invoice"
      badgeColor="success"
      icon={<FileText size={28} color="#10b981" />}
      parseSpecializedFields={parseInvoice}
    />
  );
};
