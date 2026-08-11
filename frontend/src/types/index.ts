export interface OCRResultItem {
  id: number;
  text: string;
  raw_text?: string;
  corrected_text?: string;
  confidence: number;
  is_low_confidence?: boolean;
  coordinates: number[][]; // [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
  bbox: number[][]; // [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
}

export interface PANDetails {
  is_pan_card: boolean;
  name?: string;
  father_name?: string;
  dob?: string;
  pan_number?: string;
  confidence: number;
}

export interface OCRResponse {
  success: boolean;
  processing_time: number;
  image_size: number[]; // [w, h]
  results: OCRResultItem[];
  pan_details?: PANDetails;
  extracted_fields?: Record<string, string>;
  full_text?: string;
  image_name?: string;
  detected_blocks_count: number;
  memory_usage_mb: number;
  annotated_image_base64?: string;
  overall_confidence?: number;
  model_version?: string;
  timestamp?: string;
}

export interface HealthResponse {
  status: string;
  ocr_engine_loaded: boolean;
  engine_type: string;
  uptime_seconds: number;
}

export interface ActivityItem {
  id: number;
  timestamp: string;
  image_name: string;
  processing_time: number;
  text_blocks: number;
  confidence: number;
}

export interface StatsResponse {
  total_images_processed: number;
  avg_processing_time: number;
  ocr_status: string;
  current_model: string;
  server_status: string;
  recent_activity: ActivityItem[];
}

export interface ExtractedField {
  id?: number;
  document_id?: number;
  field_name: string;
  field_value: string;
  confidence: number;
}

export interface ProcessingLog {
  id?: number;
  document_id?: number;
  stage: string;
  message: string;
  timestamp: string;
  duration: number;
}

export interface BusinessContact {
  id: number;
  document_id: number;
  name: string;
  company: string;
  designation: string;
  email: string;
  phone: string;
  website: string;
  address: string;
  created_at: string;
}

export interface DBDocument {
  id: number;
  original_filename: string;
  document_type: string;
  file_type: string;
  upload_timestamp: string;
  processing_time: number;
  overall_confidence: number;
  processing_status: string;
  raw_ocr_text: string;
  extracted_name?: string;
  image_data?: string;
  fields?: ExtractedField[];
  logs?: ProcessingLog[];
  contact?: BusinessContact;
}

export interface DBStats {
  total_documents: number;
  document_type_counts: Record<string, number>;
  average_confidence: number;
  average_processing_time: number;
}

export interface AIStatusResponse {
  is_available: boolean;
  ollama_host: string;
  configured_model: string;
  active_models: string[];
  message: string;
}

export interface LocationFieldEvidence {
  value: string;
  source: string;
  confidence: number;
  matched_candidate?: string;
}

export interface AddressDebugInfo {
  ocr_address_block: string;
  detected_pin: string;
  pin_db_result: string;
  detected_city: string;
  detected_state: string;
  cross_validation: string;
}

export interface AddressData {
  full_address: string;
  house_number: string;
  street: string;
  area: string;
  locality: string;
  post_office: string;
  city: string;
  district: string;
  state: string;
  pincode: string;
  address_confidence: number;
  city_confidence: number;
  state_confidence: number;
  location_mismatch: boolean;
  mismatch_reason?: string;
  extraction_evidence?: Record<string, LocationFieldEvidence | string>;
  debug_info?: AddressDebugInfo;
}


