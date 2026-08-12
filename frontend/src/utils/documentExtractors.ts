/**
 * documentExtractors.ts
 * Specialized Document Feature Parsers & Pre-Extraction Document Type Validators
 * Supports PAN, Aadhaar (with detailed sub-address), ID Cards, Business Cards, Payment Cards, and Invoices.
 */

export interface FieldValue {
  value: string;
  confidence: number;
  needsReview: boolean;
}

export interface ExtractedFieldMap {
  [key: string]: string;
}

export interface DocumentParseOutput {
  isValidDoc: boolean;
  validationWarning?: string;
  fields: Record<string, string>;
  fieldMeta?: Record<string, FieldValue>;
}

// Lists of States and Cities for Aadhaar & Location Validation
const INDIAN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 
  'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 
  'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 
  'Odisha', 'Orissa', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 
  'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi', 'Jammu & Kashmir', 
  'Ladakh', 'Chandigarh', 'Puducherry', 'Pondicherry', 'Dadra and Nagar Haveli', 'Daman and Diu'
];

const MAJOR_CITIES = [
  'Mumbai', 'Delhi', 'Bangalore', 'Bengaluru', 'Hyderabad', 'Ahmedabad', 'Chennai', 
  'Kolkata', 'Surat', 'Pune', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 
  'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri', 'Patna', 'Vadodara', 'Ghaziabad', 
  'Ludhiana', 'Agra', 'Nashik', 'Faridabad', 'Meerut', 'Rajkot', 'Kalyan', 'Varanasi', 
  'Srinagar', 'Aurangabad', 'Dhanbad', 'Amritsar', 'Navi Mumbai', 'Allahabad', 'Prayagraj', 
  'Ranchi', 'Howrah', 'Coimbatore', 'Jabalpur', 'Gwalior', 'Vijayawada', 'Jodhpur', 
  'Madurai', 'Raipur', 'Kota', 'Guwahati', 'Chandigarh', 'Solapur', 'Hubli', 'Dharwad', 
  'Bareilly', 'Moradabad', 'Mysore', 'Gurgaon', 'Gurugram', 'Noida', 'Aligarh', 'Jalandhar', 
  'Tiruchirappalli', 'Bhubaneswar', 'Salem', 'Warangal', 'Thiruvananthapuram', 'Dehradun',
  'Cuttack', 'Kochi', 'Udaipur', 'Shimla', 'Rohtak', 'Hisar', 'Panipat', 'Karnal'
];

// Helper to compute confidence & needsReview tag
const createFieldValue = (val: string | null | undefined): string => {
  if (!val || val.trim() === '' || val.toUpperCase() === 'N/A' || val.toUpperCase() === 'NOT FOUND') {
    return 'Not Found';
  }
  return val.trim();
};

// ── 1. PAN Card Extractor ──────────────────────────────────────────────────
export const parsePANCard = (textList: string[], rawText: string): Record<string, string> => {
  const fields: Record<string, string> = {};
  const upper = rawText.toUpperCase();

  const panMatch = upper.match(/\b[A-Z]{5}\s?[0-9]{4}\s?[A-Z]\b/);
  const hasPanKeywords = ['INCOME TAX DEPARTMENT', 'GOVT OF INDIA', 'GOVT. OF INDIA', 'PERMANENT ACCOUNT NUMBER', 'INCOME TAX', 'FATHER'].some(kw => upper.includes(kw));

  if (!panMatch && !hasPanKeywords && textList.length < 2) {
    fields['__validation_warning__'] = 'Uploaded file does not match standard PAN Card layout.';
  }

  // Extract PAN Number
  if (panMatch) {
    fields['PAN Number'] = panMatch[0].replace(/\s/g, '');
  } else {
    fields['PAN Number'] = 'Not Found';
  }

  // Extract Date of Birth
  const dobMatch = rawText.match(/\b(?:0[1-9]|[12]\d|3[01])[/.-](?:0[1-9]|1[0-2])[/.-](?:19|20)\d\d\b/);
  fields['Date of Birth'] = dobMatch ? dobMatch[0] : 'Not Found';

  // Extract Father's Name
  let fatherName = 'Not Found';
  const fatherMatch = rawText.match(/(?:Father'?s?\s*Name|पिता\s*का\s*नाम)[:\s]+([A-Za-z\s]{3,})/i);
  if (fatherMatch && fatherMatch[1].trim().length > 2) {
    fatherName = fatherMatch[1].trim();
  } else {
    for (let i = 0; i < textList.length; i++) {
      const u = textList[i].toUpperCase();
      if ((u.includes('FATHER') || u.includes('PITA') || u.includes('पिता')) && i + 1 < textList.length) {
        for (let offset = 1; offset <= 2; offset++) {
          if (i + offset < textList.length) {
            const nextLine = textList[i + offset].trim();
            if (
              nextLine.length > 2 && 
              !/\d/.test(nextLine) && 
              !['DATE', 'BIRTH', 'INCOME', 'TAX', 'GOVT', 'SIGNATURE', 'PERMANENT', 'PITA', 'FATHER', 'NAME', 'पिता'].some(kw => nextLine.toUpperCase().includes(kw))
            ) {
              fatherName = nextLine;
              break;
            }
          }
        }
        if (fatherName !== 'Not Found') break;
      }
    }
  }
  fields["Father's Name"] = fatherName;

  // Extract Cardholder Name
  let nameFound = false;
  for (const line of textList) {
    const clean = line.trim();
    if (
      clean.length > 4 && 
      !/\d/.test(clean) && 
      !['INCOME', 'TAX', 'DEPARTMENT', 'GOVT', 'INDIA', 'PERMANENT', 'ACCOUNT', 'NUMBER', 'SIGNATURE', 'CARD', 'FATHER'].some(kw => clean.toUpperCase().includes(kw))
    ) {
      fields['Cardholder Name'] = clean;
      nameFound = true;
      break;
    }
  }
  if (!nameFound) {
    fields['Cardholder Name'] = 'Not Found';
  }

  if (fields['PAN Number'] !== 'Not Found' || fields['Cardholder Name'] !== 'Not Found') {
    delete fields['__validation_warning__'];
  }

  return fields;
};

// ── 2. Aadhaar Card Extractor ──────────────────────────────────────────────
export const parseAadhaarCard = (textList: string[], rawText: string): Record<string, string> => {
  const fields: Record<string, string> = {};
  const upper = rawText.toUpperCase();

  const uidMatch = rawText.match(/\b\d{4}\s?\d{4}\s?\d{4}\b/);
  const hasAadhaarKeywords = [
    'GOVERNMENT OF INDIA', 'GOVT OF INDIA', 'UNIQUE IDENTIFICATION', 
    'AUTHORITY OF INDIA', 'UIDAI', 'AADHAAR', 'AADHAR', 'HELP@UIDAI', 'WWW.UIDAI', 'ADDRESS'
  ].some(kw => upper.includes(kw));

  if (!uidMatch && !hasAadhaarKeywords && textList.length < 3) {
    fields['__validation_warning__'] = 'Uploaded file does not match standard Aadhaar Card layout.';
  }

  // 1. Masked Aadhaar Number
  if (uidMatch) {
    const cleanUid = uidMatch[0].replace(/\s/g, '');
    fields['Aadhaar Number'] = `XXXX XXXX ${cleanUid.slice(-4)}`;
  } else {
    fields['Aadhaar Number'] = 'Not Found';
  }

  // 2. Date of Birth
  const dobMatch = rawText.match(/(?:DOB|Date of Birth|Year of Birth)[:\s]*([^\n]+)/i) || rawText.match(/\b(?:0[1-9]|[12]\d|3[01])[/.-](?:0[1-9]|1[0-2])[/.-](?:19|20)?\d\d\b/);
  fields['Date of Birth'] = dobMatch ? (dobMatch[1] || dobMatch[0]) : 'Not Found';

  // 3. Gender
  const genderMatch = rawText.match(/\b(MALE|FEMALE|TRANSGENDER)\b/i);
  fields['Gender'] = genderMatch ? genderMatch[0].toUpperCase() : 'Not Found';

  // 4. Address Block Capture
  const addressLines: string[] = [];
  let isAddressBlock = false;

  for (let i = 0; i < textList.length; i++) {
    const line = textList[i].trim();
    const upperLine = line.toUpperCase();

    if (/(?:Address|S\/O|D\/O|W\/O|C\/O)[:\s]/i.test(line) || upperLine.startsWith('ADDRESS') || upperLine.startsWith('S/O') || upperLine.startsWith('D/O') || upperLine.startsWith('W/O') || upperLine.startsWith('C/O')) {
      isAddressBlock = true;
      const cleanLine = line.replace(/^(?:Address|S\/O|D\/O|W\/O|C\/O)[:\s]*/i, '').trim();
      if (cleanLine) addressLines.push(cleanLine);
      continue;
    }

    if (isAddressBlock) {
      if (/\b\d{4}\s?\d{4}\s?\d{4}\b/.test(line) || upperLine.includes('UNIQUE IDENTIFICATION') || upperLine.includes('GOVERNMENT OF INDIA') || upperLine.includes('WWW.UIDAI')) {
        break;
      }
      addressLines.push(line);
      if (/\b\d{6}\b/.test(line)) break;
    }
  }

  if (addressLines.length === 0) {
    for (const line of textList) {
      const clean = line.trim();
      if (/\b\d{6}\b/.test(clean) || /(?:Pin|Pincode|Post|Dist|District|State|Street|Road|Nagar|Marg|Gali|House|Flat|Village)/i.test(clean)) {
        if (!['GOVERNMENT', 'INDIA', 'UNIQUE', 'AUTHORITY', 'HELP'].some(kw => clean.toUpperCase().includes(kw))) {
          addressLines.push(clean);
        }
      }
    }
  }

  const fullAddrStr = addressLines.length > 0 ? addressLines.join(', ') : 'Not Found';
  fields['Address'] = fullAddrStr;

  // PIN & Location Details
  const pinMatch = fullAddrStr !== 'Not Found' ? fullAddrStr.match(/\b\d{6}\b/) : rawText.match(/\b\d{6}\b/);
  fields['PIN Code'] = pinMatch ? pinMatch[0] : 'Not Found';

  let stateFound = 'Not Found';
  for (const st of INDIAN_STATES) {
    if (new RegExp(`\\b${st}\\b`, 'i').test(rawText)) {
      stateFound = st;
      break;
    }
  }
  fields['State'] = stateFound;

  let cityFound = 'Not Found';
  for (const city of MAJOR_CITIES) {
    if (new RegExp(`\\b${city}\\b`, 'i').test(rawText)) {
      cityFound = city;
      break;
    }
  }
  fields['City'] = cityFound;
  fields['District'] = cityFound;

  // Name
  let nameFound = false;
  for (const line of textList) {
    const clean = line.trim();
    if (
      clean.length > 3 &&
      !/\d/.test(clean) &&
      !['GOVERNMENT', 'INDIA', 'UNIQUE', 'IDENTIFICATION', 'AUTHORITY', 'MALE', 'FEMALE', 'ADDRESS', 'DOB', 'HELP', 'ENROLMENT'].some(kw => clean.toUpperCase().includes(kw))
    ) {
      fields['Name'] = clean;
      nameFound = true;
      break;
    }
  }
  if (!nameFound) {
    fields['Name'] = 'Not Found';
  }

  if (fields['Aadhaar Number'] !== 'Not Found' || fields['Name'] !== 'Not Found' || fields['Address'] !== 'Not Found') {
    delete fields['__validation_warning__'];
  }

  return fields;
};

// ── 3. ID Card Extractor ────────────────────────────────────────────────────
export const parseIDCard = (textList: string[], rawText: string): Record<string, string> => {
  const fields: Record<string, string> = {};

  const idMatch = rawText.match(/(?:ID No|Roll No|Employee ID|Emp No|Card No|Code)[:\s]*([A-Z0-9/-]+)/i);
  fields['ID Number'] = idMatch ? idMatch[1].trim() : 'Not Found';

  const deptMatch = rawText.match(/(?:STD|Class|Dept|Department|Section|Designation)[:\s]*([^\n]+)/i);
  fields['Department / Class'] = deptMatch ? deptMatch[1].trim() : 'Not Found';

  if (textList.length > 0) {
    fields['Organization / Institution'] = textList[0];
  } else {
    fields['Organization / Institution'] = 'Not Found';
  }

  if (textList.length > 1) {
    fields['Name'] = textList[1];
  } else {
    fields['Name'] = 'Not Found';
  }

  return fields;
};

// ── 4. Business Card Extractor (Universal Multi-Format Support) ──────────────
export const parseBusinessCard = (textList: string[], rawText: string): Record<string, string> => {
  const fields: Record<string, string> = {};
  const upper = rawText.toUpperCase();

  // 1. Email Regex (Priority 1)
  const emailMatch = rawText.match(/\b[a-zA-Z0-9._%+-]+(?:\s*@\s*|\s*\[at\]\s*)[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}\b/);
  fields['Email'] = emailMatch ? emailMatch[0].replace(/\s/g, '').replace('[at]', '@') : 'Not Found';

  // 2. Phone Regex (Priority 2: Supports +91-0000000000, 10-digit Indian, 5+5, 11-digit landline, US)
  const phoneMatch = rawText.match(/(?:\+\s?91[\s.-]*)?[6-9]\d{4}[\s.-]*\d{5}\b|(?:\+\s?\d{1,4}[\s.-]*)?\(?\d{2,5}\)?[\s.-]*\d{3,5}[\s.-]*\d{3,5}\b|\b[6-9]\d{9}\b|\b\d{10}\b/);
  fields['Phone'] = phoneMatch ? phoneMatch[0].trim() : 'Not Found';

  // 3. Website Regex (Priority 3)
  const webMatch = rawText.match(/(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+\.(?:com|in|co\.in|org|net|io|ai|biz|gov)(?:\/[^\s]*)?/i);
  fields['Website'] = (webMatch && !webMatch[0].includes('@')) ? webMatch[0].trim() : 'Not Found';

  // 4. Address Detection (Priority 4)
  let extractedAddr = 'Not Found';
  const addrMatch = rawText.match(/(?:Address|Location|Landmark|Office|Plot|Road|Street|Nagar|Marg|City|State|PIN)[:\s]*([^\n]+)/i);
  if (addrMatch) {
    extractedAddr = addrMatch[1].trim();
  } else {
    for (const line of textList) {
      const u = line.toUpperCase();
      if (['ADDRESS', 'LOCATION', 'LANDMARK', 'ROAD', 'STREET', 'NAGAR', 'MARG', 'CITY', 'STATE', 'PIN'].some(kw => u.includes(kw))) {
        extractedAddr = line.trim();
        break;
      }
    }
  }
  fields['Address'] = extractedAddr;

  // 5. Designation Keywords (Priority 5)
  const desigMatch = rawText.match(/(?:Chartered Accountant|Accountant|Manager|Director|Engineer|Developer|CEO|CTO|CFO|COO|Founder|Consultant|President|VP|Executive|Specialist|Lawyer|Advocate|Doctor|Architect|Partner|Proprietor|Owner|Lead|Associate|Analyst|Officer|Secretary|Principal|Professor|Advisor|CA)\b/i);
  fields['Designation'] = desigMatch ? desigMatch[0].trim() : 'Not Found';

  // 6. Smart Company Extraction (Priority 6)
  let extractedCompany = 'Not Found';
  for (const line of textList) {
    const clean = line.trim();
    const u = clean.toUpperCase();
    if (
      clean.length >= 3 &&
      !u.includes('@') && !/\d/.test(clean) &&
      !['ADDRESS', 'LOCATION', 'LANDMARK', 'ROAD', 'STREET', 'PIN', 'PHONE', 'MOBILE'].some(kw => u.includes(kw)) &&
      ['SHOP', 'STORE', 'COMPANY', 'FIRM', 'LTD', 'PVT', 'INC', 'LLP', 'SERVICES', 'SOLUTIONS', 'INDUSTRIES', 'ENTERPRISES', 'STUDIO', 'LABS', 'CORP', 'GROUP', 'GLOBAL', 'TECHNOLOGIES', 'ASSOCIATES', 'CA'].some(kw => u.includes(kw))
    ) {
      extractedCompany = clean;
      break;
    }
  }
  if (extractedCompany === 'Not Found' && textList.length > 0) {
    for (const line of textList) {
      const u = line.toUpperCase();
      if (!u.includes('@') && !/\d/.test(line) && !['ADDRESS', 'LOCATION', 'LANDMARK', 'ROAD', 'STREET', 'PHONE'].some(kw => u.includes(kw))) {
        extractedCompany = line.trim();
        break;
      }
    }
  }
  fields['Company'] = extractedCompany;

  // 7. Smart Name Extraction (Priority 7: Anti-contamination applied)
  let extractedName = 'Not Found';
  const nameLabelMatch = rawText.match(/(?:Name|Contact Person|Holder)[:\s]*([^\n]+)/i);
  if (nameLabelMatch && nameLabelMatch[1].trim().length > 2) {
    extractedName = nameLabelMatch[1].trim();
  } else {
    for (const line of textList) {
      const clean = line.trim();
      const u = clean.toUpperCase();
      if (
        clean.length >= 3 && clean.length <= 35 &&
        !/\d/.test(clean) &&
        !u.includes('@') && !u.includes('.COM') && !u.includes('.IN') && !u.includes('WWW') &&
        clean !== extractedCompany && clean !== fields['Designation'] && clean !== extractedAddr &&
        !['COMPANY', 'FIRM', 'LTD', 'PVT', 'INC', 'SERVICES', 'SOLUTIONS', 'INDUSTRIES', 'ENTERPRISES', 'ACCOUNTANT', 'CHARTERED', 'ADDRESS', 'LOCATION', 'LANDMARK', 'PHONE', 'MOBILE', 'TEL'].some(kw => u.includes(kw))
      ) {
        if (clean.split(/\s+/).length <= 4) {
          extractedName = clean;
          break;
        }
      }
    }
  }
  fields['Name'] = extractedName;

  // Clear validation warning if valid fields present
  const foundCount = Object.values(fields).filter(v => v !== 'Not Found').length;
  if (foundCount === 0 && textList.length < 2) {
    fields['__validation_warning__'] = 'Uploaded file does not match standard Business Card format.';
  } else {
    delete fields['__validation_warning__'];
  }

  return fields;
};

// ── 5. Payment / Debit / Credit Card Extractor ──────────────────────────────
export const parsePaymentCard = (textList: string[], rawText: string): Record<string, string> => {
  const fields: Record<string, string> = {};
  const upper = rawText.toUpperCase();

  const cardMatch = rawText.match(/\b(?:\d[ -]*?){13,16}\b/);
  const expMatch = rawText.match(/\b(?:0[1-9]|1[0-2])\s?\/\s?(?:2[0-9]|[3-9]\d)\b/);

  if (cardMatch) {
    const digitsOnly = cardMatch[0].replace(/\D/g, '');
    fields['Card Number'] = `**** **** **** ${digitsOnly.slice(-4)}`;
  } else {
    fields['Card Number'] = 'Not Found';
  }

  fields['Expiry Date'] = expMatch ? expMatch[0] : 'Not Found';

  let nameFound = false;
  for (const line of textList) {
    const clean = line.trim();
    if (
      clean.length > 4 &&
      /^[A-Z\s]+$/.test(clean) &&
      !['VISA', 'MASTERCARD', 'DEBIT', 'CREDIT', 'BANK', 'EXPRESS', 'VALID', 'THRU', 'RUPAY', 'CARD'].some(kw => clean.includes(kw))
    ) {
      fields['Cardholder Name'] = clean;
      nameFound = true;
      break;
    }
  }
  if (!nameFound) {
    fields['Cardholder Name'] = 'Not Found';
  }

  return fields;
};

// ── 6. Invoice Extractor ────────────────────────────────────────────────────
export const parseInvoice = (textList: string[], rawText: string): Record<string, string> => {
  const fields: Record<string, string> = {};

  const invNoMatch = rawText.match(/(?:Invoice No|Invoice #|Inv No|Bill No|Tax Invoice No)[:\s]*([A-Z0-9/-]+)/i);
  fields['Invoice Number'] = invNoMatch ? invNoMatch[1].trim() : 'Not Found';

  const dateMatch = rawText.match(/(?:Invoice Date|Date|Bill Date)[:\s]*([^\n]+)/i) || rawText.match(/\b(?:0[1-9]|[12]\d|3[01])[/.-](?:0[1-9]|1[0-2])[/.-](?:19|20)?\d\d\b/);
  fields['Invoice Date'] = dateMatch ? (dateMatch[1] || dateMatch[0]) : 'Not Found';

  const totalMatch = rawText.match(/(?:Grand Total|Total Amount|Amount Due|Total|Net Amount)[:\s]*[₹$]?\s?([\d,]+\.?\d*)/i);
  fields['Total Amount'] = totalMatch ? `${totalMatch[1]}` : 'Not Found';

  const gstMatch = rawText.match(/(?:GSTIN|GST No|VAT No|Tax ID)[:\s]*([A-Z0-9]+)/i);
  fields['GST / VAT ID'] = gstMatch ? gstMatch[1].trim() : 'Not Found';

  if (textList.length > 0) {
    fields['Vendor Name'] = textList[0];
  } else {
    fields['Vendor Name'] = 'Not Found';
  }

  return fields;
};
