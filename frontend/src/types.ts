export type Status = 'PASS' | 'FAIL' | 'REVIEW';

export interface ApplicationData {
  brand_name: string;
  class_type: string;
  alcohol_content: string;
  net_contents: string;
}

export interface FieldResult {
  field: string;
  status: Status;
  expected?: string | null;
  found?: string | null;
  message: string;
  evidence?: string | null;
}

export interface VerificationResult {
  overall_status: Status;
  summary: string;
  ocr_text: string;
  ocr_status?: Status;
  ocr_message?: string;
  fields: FieldResult[];
  metadata?: Record<string, unknown>;
}
