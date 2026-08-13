import axios from 'axios';
import { 
  OCRResponse, HealthResponse, StatsResponse,
  DBDocument, ExtractedField, ProcessingLog, BusinessContact, DBStats, AIStatusResponse
} from '../types';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
  },
});

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

export const getAIStatus = async (): Promise<AIStatusResponse> => {
  const response = await apiClient.get<AIStatusResponse>('/api/ai/status');
  return response.data;
};


export const getStats = async (): Promise<StatsResponse> => {
  const response = await apiClient.get<StatsResponse>('/stats');
  return response.data;
};

export const processImage = async (file: File): Promise<OCRResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<OCRResponse>('/ocr/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const processPdf = async (file: File): Promise<OCRResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<OCRResponse>('/ocr/pdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export interface FrameQualityResponse {
  is_acceptable: boolean;
  blur_score: number;
  brightness: number;
  document_detected: boolean;
  reason: string;
}

export const checkImageQuality = async (imageBase64: string): Promise<FrameQualityResponse> => {
  const response = await apiClient.post<FrameQualityResponse>('/ocr/quality_check', {
    image_base64: imageBase64,
  });
  return response.data;
};

export const processWebcamFrame = async (imageBase64: string): Promise<OCRResponse> => {
  const response = await apiClient.post<OCRResponse>('/ocr/webcam', {
    image_base64: imageBase64,
  });
  return response.data;
};

export const processUniversal = async (file: File): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<any>('/ocr/universal', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export interface PrescriptionExtractionResponse {
  success: boolean;
  needs_manual_review: boolean;
  data: {
    document_type: string;
    doctor: {
      name: string | null;
      registration_number: string | null;
      specialization: string | null;
    };
    patient: {
      name: string | null;
      age: string | null;
      gender: string | null;
    };
    prescription_date: string | null;
    diagnosis: string[];
    medicines: Array<{
      name: string | null;
      strength: string | null;
      dosage: string | null;
      frequency: string | null;
      duration: string | null;
      route: string | null;
      instructions: string | null;
      confidence: number;
      needs_review: boolean;
    }>;
    tests: string[];
    general_instructions: string[];
    raw_text: string;
    overall_confidence: number;
    needs_manual_review: boolean;
    model_used: string;
    fallback_attempt: number;
  };
  processing: {
    model_used: string;
    fallback_attempt: number;
    fallback_used: boolean;
    used_openrouter: boolean;
    quality_grade: string;
    validation_issues: string[];
    ocr_time_ms: number;
    total_time_ms: number;
    medicine_count: number;
    overall_confidence: number;
    attempt_logs: Array<{
      model: string;
      attempt: number;
      retry: number;
      status: string;
      api_time_ms: number;
      fallback_used: boolean;
      error_type?: string;
      overall_confidence?: number;
      medicine_count?: number;
      validation_reason?: string;
    }>;
  };
}

export const extractPrescriptionWithFallback = async (file: File): Promise<PrescriptionExtractionResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<PrescriptionExtractionResponse>('/api/prescription/extract', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// ── DATABASE API HELPERS ───────────────────────────────────────────────────

export const uploadDocumentDB = async (file: File, documentType?: string): Promise<{ success: boolean; id: number; document: DBDocument }> => {
  const formData = new FormData();
  formData.append('file', file);
  if (documentType) formData.append('document_type', documentType);

  const response = await apiClient.post<{ success: boolean; id: number; document: DBDocument }>('/api/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDBDocuments = async (params?: {
  search?: string;
  document_type?: string;
  sort_by?: string;
  order?: string;
}): Promise<{ count: number; documents: DBDocument[] }> => {
  const response = await apiClient.get<{ count: number; documents: DBDocument[] }>('/api/documents', { params });
  return response.data;
};

export const getDBDocumentById = async (id: number): Promise<DBDocument> => {
  const response = await apiClient.get<DBDocument>(`/api/documents/${id}`);
  return response.data;
};

export const deleteDBDocument = async (id: number): Promise<{ success: boolean; message: string }> => {
  const response = await apiClient.delete<{ success: boolean; message: string }>(`/api/documents/${id}`);
  return response.data;
};

export const getDBDocumentFields = async (id: number): Promise<ExtractedField[]> => {
  const response = await apiClient.get<ExtractedField[]>(`/api/documents/${id}/fields`);
  return response.data;
};

export const getDBDocumentLogs = async (id: number): Promise<ProcessingLog[]> => {
  const response = await apiClient.get<ProcessingLog[]>(`/api/documents/${id}/logs`);
  return response.data;
};

export const getDBContacts = async (search?: string): Promise<{ count: number; contacts: BusinessContact[] }> => {
  const response = await apiClient.get<{ count: number; contacts: BusinessContact[] }>('/api/contacts', { params: { search } });
  return response.data;
};

export const getDBContactById = async (id: number): Promise<BusinessContact> => {
  const response = await apiClient.get<BusinessContact>(`/api/contacts/${id}`);
  return response.data;
};

export const getDBStats = async (): Promise<DBStats> => {
  const response = await apiClient.get<DBStats>('/api/documents/stats');
  return response.data;
};

export const retryDBDocument = async (id: number): Promise<{ success: boolean; message: string; document: DBDocument }> => {
  const response = await apiClient.post<{ success: boolean; message: string; document: DBDocument }>(`/api/documents/${id}/retry`);
  return response.data;
};

export const reviewDBDocumentField = async (
  id: number,
  fieldName: string,
  correctedValue: string,
  approved: boolean = true
): Promise<{ success: boolean; message: string; document: DBDocument }> => {
  const response = await apiClient.post<{ success: boolean; message: string; document: DBDocument }>(`/api/documents/${id}/review`, {
    field_name: fieldName,
    corrected_value: correctedValue,
    approved: approved
  });
  return response.data;
};



