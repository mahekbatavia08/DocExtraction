import { OCRResponse, OCRResultItem } from '../types';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

export type ExportFormat = 'csv' | 'xlsx' | 'pdf' | 'txt' | 'json';

export interface ExportOptions {
  ocrResult: OCRResponse;
  documentTitle?: string;
  format: ExportFormat;
}

/**
 * Formats a Date object into YYYYMMDD_HHMMSS string for standard file naming.
 */
export function getFormattedTimestamp(date: Date = new Date()): string {
  const pad = (num: number) => String(num).padStart(2, '0');
  const yyyy = date.getFullYear();
  const mm = pad(date.getMonth() + 1);
  const dd = pad(date.getDate());
  const hh = pad(date.getHours());
  const min = pad(date.getMinutes());
  const ss = pad(date.getSeconds());
  return `${yyyy}${mm}${dd}_${hh}${min}${ss}`;
}

/**
 * Generates clean filename following DocumentName_YYYYMMDD_HHMMSS.ext
 */
export function generateExportFilename(docName: string, ext: string): string {
  const cleanDocName = (docName || 'Document')
    .trim()
    .replace(/[^a-zA-Z0-9_-]/g, '_')
    .replace(/_+/g, '_');
  const timestamp = getFormattedTimestamp();
  return `${cleanDocName}_${timestamp}.${ext}`;
}

/**
 * Helper to trigger file download in browser
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Calculates overall average confidence percentage
 */
function getOverallConfidence(res: OCRResponse): string {
  if (res.overall_confidence !== undefined && res.overall_confidence > 0) {
    return `${res.overall_confidence.toFixed(1)}%`;
  }
  if (!res.results || res.results.length === 0) return '0.0%';
  const sum = res.results.reduce((acc, item) => acc + item.confidence, 0);
  const avg = (sum / res.results.length) * 100;
  return `${avg.toFixed(1)}%`;
}

/**
 * Main export handler supporting CSV, Excel (.xlsx), PDF, TXT, and JSON
 */
export async function exportOCRData(options: ExportOptions): Promise<{ success: boolean; filename: string; message: string }> {
  const { ocrResult, documentTitle = 'Document', format } = options;
  const filename = generateExportFilename(documentTitle, format);

  try {
    const docName = ocrResult.image_name || documentTitle;
    const processDateTime = ocrResult.timestamp || new Date().toLocaleString();
    const processingTime = `${ocrResult.processing_time.toFixed(2)} seconds`;
    const overallConf = getOverallConfidence(ocrResult);
    const modelVer = ocrResult.model_version || 'PaddleOCR PP-OCRv4 / EasyOCR';
    const rawText = ocrResult.full_text || ocrResult.results.map((r: OCRResultItem) => r.text).join('\n');

    switch (format) {
      case 'json': {
        const jsonPayload = {
          metadata: {
            document_name: docName,
            processing_date_time: processDateTime,
            ocr_processing_time: processingTime,
            overall_confidence: overallConf,
            ocr_model_version: modelVer,
            detected_blocks_count: ocrResult.detected_blocks_count,
            image_size: ocrResult.image_size
          },
          extracted_fields: ocrResult.extracted_fields || {},
          pan_details: ocrResult.pan_details || null,
          extracted_data_table: ocrResult.results.map((r, idx) => ({
            sr_no: idx + 1,
            extracted_text: r.text,
            raw_text: r.raw_text || r.text,
            confidence_score: `${(r.confidence * 100).toFixed(1)}%`,
            is_low_confidence: r.is_low_confidence || r.confidence < 0.95,
            bounding_box: r.bbox || r.coordinates
          })),
          raw_ocr_text: rawText
        };
        const blob = new Blob([JSON.stringify(jsonPayload, null, 2)], { type: 'application/json;charset=utf-8;' });
        downloadBlob(blob, filename);
        break;
      }

      case 'txt': {
        let content = `===========================================================\n`;
        content += `                  OCR EXTRACTION REPORT                    \n`;
        content += `===========================================================\n`;
        content += `Document Name         : ${docName}\n`;
        content += `Processing Date & Time: ${processDateTime}\n`;
        content += `OCR Processing Time   : ${processingTime}\n`;
        content += `Overall Confidence    : ${overallConf}\n`;
        content += `OCR Model Version     : ${modelVer}\n`;
        content += `Total Text Blocks     : ${ocrResult.detected_blocks_count}\n`;
        content += `===========================================================\n\n`;

        if (ocrResult.extracted_fields && Object.keys(ocrResult.extracted_fields).length > 0) {
          content += `--- EXTRACTED ATTRIBUTES ---\n`;
          Object.entries(ocrResult.extracted_fields).forEach(([k, v]) => {
            content += `${k.padEnd(25)}: ${v}\n`;
          });
          content += `\n`;
        }

        content += `--- EXTRACTED DATA TABLE ---\n`;
        content += `Sr. No | Confidence | Extracted Text\n`;
        content += `-----------------------------------------------------------\n`;
        ocrResult.results.forEach((r, idx) => {
          const srNo = String(idx + 1).padEnd(6);
          const conf = `${(r.confidence * 100).toFixed(1)}%`.padEnd(10);
          content += `${srNo} | ${conf} | ${r.text}\n`;
        });

        content += `\n--- RAW OCR TEXT ---\n`;
        content += rawText;
        content += `\n===========================================================\n`;

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8;' });
        downloadBlob(blob, filename);
        break;
      }

      case 'csv': {
        const rows: string[] = [];
        rows.push(`"METADATA"`);
        rows.push(`"Document Name","${docName.replace(/"/g, '""')}"`);
        rows.push(`"Processing Date & Time","${processDateTime}"`);
        rows.push(`"OCR Processing Time","${processingTime}"`);
        rows.push(`"Overall Confidence","${overallConf}"`);
        rows.push(`"OCR Model Version","${modelVer}"`);
        rows.push(``);
        rows.push(`"EXTRACTED DATA TABLE"`);
        rows.push(`"Sr. No","Extracted Text","Confidence Score","Low Confidence Flag"`);

        ocrResult.results.forEach((r, idx) => {
          const text = r.text.replace(/"/g, '""');
          const conf = `${(r.confidence * 100).toFixed(1)}%`;
          const lowConf = (r.is_low_confidence || r.confidence < 0.95) ? 'YES (<95%)' : 'NO';
          rows.push(`"${idx + 1}","${text}","${conf}","${lowConf}"`);
        });

        rows.push(``);
        rows.push(`"RAW OCR TEXT"`);
        rows.push(`"${rawText.replace(/"/g, '""')}"`);

        const csvContent = rows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        downloadBlob(blob, filename);
        break;
      }

      case 'xlsx': {
        const wb = XLSX.utils.book_new();

        // Summary Sheet
        const metadataData = [
          ['OCR EXTRACTION REPORT SUMMARY', ''],
          ['Document Name', docName],
          ['Processing Date & Time', processDateTime],
          ['OCR Processing Time', processingTime],
          ['Overall Confidence', overallConf],
          ['OCR Model Version', modelVer],
          ['Total Detected Blocks', ocrResult.detected_blocks_count],
          ['', '']
        ];

        if (ocrResult.extracted_fields && Object.keys(ocrResult.extracted_fields).length > 0) {
          metadataData.push(['EXTRACTED ATTRIBUTES', '']);
          Object.entries(ocrResult.extracted_fields).forEach(([k, v]) => {
            metadataData.push([k, v]);
          });
        }

        const summaryWs = XLSX.utils.aoa_to_sheet(metadataData);
        XLSX.utils.book_append_sheet(wb, summaryWs, 'Summary & Metadata');

        // Table Data Sheet
        const tableData = [
          ['Sr. No', 'Extracted Text', 'Raw Text', 'Confidence Score', 'Low Confidence Alert']
        ];
        ocrResult.results.forEach((r, idx) => {
          tableData.push([
            (idx + 1) as any,
            r.text,
            r.raw_text || r.text,
            `${(r.confidence * 100).toFixed(1)}%`,
            (r.is_low_confidence || r.confidence < 0.95) ? 'WARNING (<95%)' : 'PASS'
          ]);
        });

        const tableWs = XLSX.utils.aoa_to_sheet(tableData);
        XLSX.utils.book_append_sheet(wb, tableWs, 'Extracted Data Table');

        // Raw Text Sheet
        const rawTextWs = XLSX.utils.aoa_to_sheet([['Full Raw OCR Output'], [rawText]]);
        XLSX.utils.book_append_sheet(wb, rawTextWs, 'Raw OCR Text');

        XLSX.writeFile(wb, filename);
        break;
      }

      case 'pdf': {
        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

        // Header Banner
        doc.setFillColor(16, 185, 129); // Modern Emerald Green
        doc.rect(0, 0, 210, 20, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('AI OCR Document Extraction Report', 14, 13);

        // Metadata Table
        doc.setTextColor(30, 41, 59);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text('Document Metadata & Stats:', 14, 28);

        const metaRows = [
          ['Document Name:', docName, 'Processing Time:', processingTime],
          ['Date & Time:', processDateTime, 'Overall Confidence:', overallConf],
          ['OCR Model:', modelVer, 'Detected Text Blocks:', String(ocrResult.detected_blocks_count)]
        ];

        autoTable(doc, {
          startY: 31,
          body: metaRows,
          theme: 'plain',
          styles: { fontSize: 8.5, cellPadding: 1.5 },
          columnStyles: {
            0: { fontStyle: 'bold', cellWidth: 35 },
            1: { cellWidth: 60 },
            2: { fontStyle: 'bold', cellWidth: 35 },
            3: { cellWidth: 60 }
          }
        });

        const finalY = (doc as any).lastAutoTable ? (doc as any).lastAutoTable.finalY + 8 : 55;

        // Table Header
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(16, 185, 129);
        doc.text('Extracted Data Table:', 14, finalY);

        const tableBody = ocrResult.results.map((r, idx) => [
          String(idx + 1),
          r.text,
          `${(r.confidence * 100).toFixed(1)}%`,
          (r.is_low_confidence || r.confidence < 0.95) ? 'Review Needed (<95%)' : 'High Confidence'
        ]);

        autoTable(doc, {
          startY: finalY + 3,
          head: [['Sr. No', 'Extracted Text', 'Confidence Score', 'Status']],
          body: tableBody,
          theme: 'striped',
          headStyles: { fillColor: [15, 23, 42], textColor: 255, fontStyle: 'bold' },
          styles: { fontSize: 8.5, cellPadding: 2.5 },
          columnStyles: {
            0: { cellWidth: 16, halign: 'center' },
            1: { cellWidth: 110 },
            2: { cellWidth: 30, halign: 'center' },
            3: { cellWidth: 30, halign: 'center' }
          },
          didParseCell: (data) => {
            if (data.section === 'body' && data.column.index === 3) {
              if (data.cell.raw === 'Review Needed (<95%)') {
                data.cell.styles.textColor = [239, 68, 68]; // Red warning
                data.cell.styles.fontStyle = 'bold';
              } else {
                data.cell.styles.textColor = [16, 185, 129]; // Emerald success
              }
            }
          }
        });

        doc.save(filename);
        break;
      }
    }

    return {
      success: true,
      filename,
      message: `Export Successful (${filename})`
    };
  } catch (err: any) {
    console.error('Export Failed:', err);
    return {
      success: false,
      filename,
      message: `Export Failed: ${err.message || 'Error creating export file.'}`
    };
  }
}
