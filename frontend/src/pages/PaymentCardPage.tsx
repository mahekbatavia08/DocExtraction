import React from 'react';
import { CreditCard } from 'lucide-react';
import { DocumentOCRModule } from '../components/DocumentOCRModule';
import { parsePaymentCard } from '../utils/documentExtractors';

export const PaymentCardPage: React.FC = () => {
  return (
    <DocumentOCRModule
      title="Debit / Credit Card OCR"
      description="Extract Cardholder Name, Masked Card Number (**** **** **** 1234), and Expiry Date. CVV is never exposed."
      badgeLabel="PCI Masked"
      badgeColor="error"
      icon={<CreditCard size={28} color="#10b981" />}
      parseSpecializedFields={parsePaymentCard}
    />
  );
};
