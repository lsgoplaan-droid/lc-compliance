"""Demo endpoint: creates a pre-populated session with sample LC and supporting documents."""

from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter

from models.enums import DocumentType
from models.schemas import (
    ExtractedDocument,
    ExtractedField,
    Session,
    SessionResponse,
)
from storage.session_store import session_store

router = APIRouter(tags=["demo"])


def _field(value: str, confidence: float = 0.9) -> ExtractedField:
    return ExtractedField(value=value, confidence=confidence)


def _build_lc_document(session_id: str) -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=uuid4().hex[:12],
        session_id=session_id,
        document_type=DocumentType.LC_ADVICE,
        original_filename="LC_Advice_DEMO.TXT",
        file_path="demo",
        extraction_method="text",
        uploaded_at=datetime.now(),
        raw_text="[Demo data — LC Bank Advice]",
        fields={
            "lc_number": _field("202507LC008431"),
            "date_of_issue": _field("15JUL25"),
            "expiry_date": _field("30SEP25"),
            "applicant_name": _field("PACIFIC RIM TRADING CO. LTD."),
            "applicant_address": _field("12 HARBOUR ROAD, INDUSTRIAL ZONE, CHITTAGONG 4100, BANGLADESH"),
            "beneficiary_name": _field("GOLDEN BRIDGE CHEMICALS PTE LTD."),
            "beneficiary_address": _field("8 MARINA VIEW, #28-05, ASIA SQUARE TOWER 1, SINGAPORE 018960"),
            "currency_amount": _field("USD 23,460.00"),
            "goods_description": _field("INDUSTRIAL GRADE SODIUM HYDROXIDE (CAUSTIC SODA FLAKES)"),
            "quantity": _field("26.00 MT"),
            "unit_price": _field("902.31/MT"),
            "hs_codes": _field("2815.11.00 (CHINA) 2815.12.10 (BANGLADESH)"),
            "incoterms": _field("CFR CHITTAGONG PORT, BANGLADESH (INCOTERMS 2020)"),
            "port_of_loading": _field("ANY SEAPORT OF CHINA"),
            "port_of_discharge": _field("CHITTAGONG PORT, BANGLADESH"),
            "latest_shipment_date": _field("15SEP25"),
            "country_of_origin": _field("CHINA"),
            "issuing_bank": _field("EASTERN COMMERCIAL BANK LTD"),
        },
    )


def _build_invoice(session_id: str) -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=uuid4().hex[:12],
        session_id=session_id,
        document_type=DocumentType.COMMERCIAL_INVOICE,
        original_filename="Commercial_Invoice_GBC-2025-0891.pdf",
        file_path="demo",
        extraction_method="ocr",
        uploaded_at=datetime.now(),
        raw_text="[Demo data — Commercial Invoice]",
        fields={
            "lc_number": _field("202507LC008431"),
            "invoice_number": _field("GBC/INV/2025-0891"),
            "invoice_date": _field("10-8-2025"),
            "applicant_name": _field("PACIFIC RIM TRADING CO. LIMITED"),
            "applicant_address": _field("12 HARBOUR ROAD, INDUSTRIAL ZONE, CHITTAGONG 4100 BANGLADESH"),
            "beneficiary_name": _field("GOLDEN BRIDGE CHEMICALS PTE LTD."),
            "beneficiary_address": _field("8 MARINA VIEW, #28-05, ASIA SQUARE TOWER 1, SINGAPORE 018960"),
            "currency_amount": _field("USD 23,460.00"),
            "goods_description": _field("INDUSTRIAL GRADE SODIUM HYDROXIDE (CAUSTIC SODA FLAKES)"),
            "quantity": _field("26,000.000 KGS"),
            "unit_price": _field("902.31/MT"),
            "hs_codes": _field("2815.11.00 (CHINA) 2815.12.10 (BANGLADESH)"),
            "incoterms": _field("CFR CHITTAGONG PORT, BANGLADESH (INCOTERMS 2020)"),
            "port_of_loading": _field("SHANGHAI, CHINA"),
            "port_of_discharge": _field("CHITTAGONG PORT, BANGLADESH"),
            "country_of_origin": _field("CHINA"),
            "vessel_name": _field("ORIENT STAR V.25W032"),
        },
    )


def _build_certificate_of_origin(session_id: str) -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=uuid4().hex[:12],
        session_id=session_id,
        document_type=DocumentType.CERTIFICATE_OF_ORIGIN,
        original_filename="Certificate_of_Origin_GBC.pdf",
        file_path="demo",
        extraction_method="ocr",
        uploaded_at=datetime.now(),
        raw_text="[Demo data — Certificate of Origin]",
        fields={
            "lc_number": _field("202507LC008431"),
            "applicant_name": _field("PACIFIC RIM TRADING CO. LIMITED"),
            "applicant_address": _field("12 HARBOUR ROAD, INDUSTRIAL ZONE, CHITTAGONG 4100 BANGLADESH"),
            "beneficiary_name": _field("GOLDEN BRIDGE CHEMICALS PTE LTD."),
            "goods_description": _field("INDUSTRIAL GRADE SODIUM HYDROXIDE (CAUSTIC SODA FLAKES)"),
            "quantity": _field("26,000.000 KGS"),
            "hs_codes": _field("2815.11.00 (CHINA) 2815.12.10 (BANGLADESH)"),
            "incoterms": _field("CFR CHITTAGONG PORT, BANGLADESH (INCOTERMS 2020)"),
            "port_of_loading": _field("SHANGHAI, CHINA"),
            "port_of_discharge": _field("CHITTAGONG PORT, BANGLADESH"),
            "country_of_origin": _field("CHINA"),
            "vessel_name": _field("ORIENT STAR V.25W032"),
        },
    )


def _build_packing_list(session_id: str) -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=uuid4().hex[:12],
        session_id=session_id,
        document_type=DocumentType.PACKING_LIST,
        original_filename="Packing_List_GBC-2025-0891.pdf",
        file_path="demo",
        extraction_method="ocr",
        uploaded_at=datetime.now(),
        raw_text="[Demo data — Packing List]",
        fields={
            "lc_number": _field("202507LC008431"),
            "applicant_name": _field("PACIFIC RIM TRADING CO. LIMITED"),
            "applicant_address": _field("12 HARBOUR ROAD, INDUSTRIAL ZONE, CHITTAGONG 4100 BANGLADESH"),
            "beneficiary_name": _field("GOLDEN BRIDGE CHEMICALS PTE LTD."),
            "goods_description": _field("INDUSTRIAL GRADE SODIUM HYDROXIDE (CAUSTIC SODA FLAKES)"),
            "quantity": _field("26,000.000 KGS"),
            "port_of_loading": _field("SHANGHAI, CHINA"),
            "port_of_discharge": _field("CHITTAGONG PORT, BANGLADESH"),
            "vessel_name": _field("ORIENT STAR V.25W032"),
        },
    )


@router.post("/demo", response_model=SessionResponse)
def create_demo_session():
    """Create a demo session pre-populated with sample LC and trade documents."""
    session_id = "demo-" + uuid4().hex[:8]
    session = Session(session_id=session_id, created_at=datetime.now())

    session.lc_document = _build_lc_document(session_id)
    session.supporting_documents = [
        _build_invoice(session_id),
        _build_certificate_of_origin(session_id),
        _build_packing_list(session_id),
    ]

    session_store.save(session)

    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        lc_uploaded=True,
        supporting_doc_count=3,
        has_comparison=False,
    )
