export const DocumentType = {
  LC_ADVICE: "lc_advice",
  COMMERCIAL_INVOICE: "commercial_invoice",
  CERTIFICATE_OF_ORIGIN: "certificate_of_origin",
  BILL_OF_LADING: "bill_of_lading",
  PACKING_LIST: "packing_list",
} as const;

export type DocumentType = (typeof DocumentType)[keyof typeof DocumentType];

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  [DocumentType.LC_ADVICE]: "LC Bank Advice",
  [DocumentType.COMMERCIAL_INVOICE]: "Commercial Invoice",
  [DocumentType.CERTIFICATE_OF_ORIGIN]: "Certificate of Origin",
  [DocumentType.BILL_OF_LADING]: "Bill of Lading",
  [DocumentType.PACKING_LIST]: "Packing List",
};

export interface ExtractedField {
  value: string | null;
  raw_source_text: string | null;
  confidence: number;
  manually_corrected: boolean;
}

export interface ExtractedDocument {
  doc_id: string;
  session_id: string;
  document_type: DocumentType;
  original_filename: string;
  file_path: string;
  extraction_method: "text" | "ocr";
  uploaded_at: string;
  raw_text: string;
  fields: Record<string, ExtractedField>;
}

export interface UploadResponse {
  doc_id: string;
  document_type: DocumentType;
  original_filename: string;
  extraction_method: string;
  fields: Record<string, ExtractedField>;
  field_count: number;
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
  lc_uploaded: boolean;
  supporting_doc_count: number;
  has_comparison: boolean;
}
