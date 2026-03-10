import type { DocumentType } from "./document";

export const MatchStatus = {
  MATCH: "match",
  MISMATCH: "mismatch",
  MISSING: "missing",
  NOT_APPLICABLE: "n/a",
} as const;

export type MatchStatus = (typeof MatchStatus)[keyof typeof MatchStatus];

export const Severity = {
  CRITICAL: "critical",
  WARNING: "warning",
  INFO: "info",
} as const;

export type Severity = (typeof Severity)[keyof typeof Severity];

export interface FieldComparison {
  field_name: string;
  field_category: string;
  lc_value: string | null;
  doc_value: string | null;
  match_status: MatchStatus;
  match_strategy: string;
  similarity_score: number | null;
  severity: Severity;
  ucp_rule: string | null;
  note: string | null;
}

export interface ComparisonSummary {
  match_count: number;
  mismatch_count: number;
  missing_count: number;
  total_fields: number;
  compliance_score: number;
}

export interface DocumentComparison {
  doc_id: string;
  document_type: DocumentType;
  original_filename: string;
  field_comparisons: FieldComparison[];
  summary: ComparisonSummary;
}

export interface ComplianceReport {
  session_id: string;
  overall_compliance_score: number;
  document_comparisons: DocumentComparison[];
  critical_discrepancies: FieldComparison[];
  warnings: FieldComparison[];
  generated_at: string;
}
