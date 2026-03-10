from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

from models.enums import DocumentType, MatchStatus, MatchStrategy, Severity


class ExtractedField(BaseModel):
    value: Optional[str] = None
    raw_source_text: Optional[str] = None
    confidence: float = 0.0
    manually_corrected: bool = False


class ExtractedDocument(BaseModel):
    doc_id: str
    session_id: str
    document_type: DocumentType
    original_filename: str
    file_path: str
    extraction_method: str  # "text" or "ocr"
    uploaded_at: datetime
    raw_text: str = ""
    fields: Dict[str, ExtractedField] = {}


class FieldComparison(BaseModel):
    field_name: str
    field_category: str  # "core", "goods", "shipping"
    lc_value: Optional[str] = None
    doc_value: Optional[str] = None
    match_status: MatchStatus
    match_strategy: MatchStrategy
    similarity_score: Optional[float] = None
    severity: Severity
    ucp_rule: Optional[str] = None
    note: Optional[str] = None


class ComparisonSummary(BaseModel):
    match_count: int = 0
    mismatch_count: int = 0
    missing_count: int = 0
    total_fields: int = 0
    compliance_score: float = 0.0


class DocumentComparison(BaseModel):
    doc_id: str
    document_type: DocumentType
    original_filename: str
    field_comparisons: List[FieldComparison] = []
    summary: ComparisonSummary = ComparisonSummary()


class ComplianceReport(BaseModel):
    session_id: str
    lc_document: Optional[ExtractedDocument] = None
    document_comparisons: List[DocumentComparison] = []
    overall_compliance_score: float = 0.0
    critical_discrepancies: List[FieldComparison] = []
    warnings: List[FieldComparison] = []
    generated_at: datetime = datetime.now()


class Session(BaseModel):
    session_id: str
    created_at: datetime = datetime.now()
    lc_document: Optional[ExtractedDocument] = None
    supporting_documents: List[ExtractedDocument] = []
    comparison_results: Optional[List[DocumentComparison]] = None
    report: Optional[ComplianceReport] = None


# Request/Response models
class UploadResponse(BaseModel):
    doc_id: str
    document_type: DocumentType
    original_filename: str
    extraction_method: str
    fields: Dict[str, ExtractedField]
    field_count: int


class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    lc_uploaded: bool
    supporting_doc_count: int
    has_comparison: bool


class FieldUpdateRequest(BaseModel):
    fields: Dict[str, str]  # field_name -> new_value
