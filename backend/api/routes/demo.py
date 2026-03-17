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
        original_filename="SGHSBC5G31532406-T02.TXT",
        file_path="demo",
        extraction_method="text",
        uploaded_at=datetime.now(),
        raw_text="[Demo data — LC Bank Advice]",
        fields={
            "lc_number": _field("141325010091"),
            "date_of_issue": _field("30JUL25"),
            "expiry_date": _field("21SEP25"),
            "applicant_name": _field("BRB CABLE INDUSTRIES LTD."),
            "applicant_address": _field("BSCIC INDUSTRIAL ESTATE KUSHTIA 7000, BANGLADESH"),
            "beneficiary_name": _field("HARESH PETROCHEM SINGAPORE PTE LTD."),
            "beneficiary_address": _field("1 NORTH BRIDGE ROAD, NO 16-07, HIGH STREET CENTRE, SINGAPORE 179094"),
            "currency_amount": _field("USD 15640.00"),
            "goods_description": _field("MONO ETHYLENE GLYCOL"),
            "quantity": _field("18.40 MT"),
            "unit_price": _field("850/MT"),
            "hs_codes": _field("2905.31.00 (CHINA) 2905.31.90 (BANGLADESH)"),
            "incoterms": _field("CFR CHATTOGRAM SEAPORT, BANGLADESH (INCOTERMS 2020)"),
            "port_of_loading": _field("ANY SEAPORT OF CHINA"),
            "port_of_discharge": _field("CHATTORGRAM SEAPORT, BANGLADESH"),
            "latest_shipment_date": _field("31AUG25"),
            "country_of_origin": _field("CHINA"),
            "issuing_bank": _field("DHAKA BANK PLC"),
        },
    )


def _build_invoice(session_id: str) -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=uuid4().hex[:12],
        session_id=session_id,
        document_type=DocumentType.COMMERCIAL_INVOICE,
        original_filename="Invoice.pdf",
        file_path="demo",
        extraction_method="ocr",
        uploaded_at=datetime.now(),
        raw_text="[Demo data — Commercial Invoice]",
        fields={
            "lc_number": _field("141325010091"),
            "invoice_number": _field("HPS/INV/087/25-26"),
            "invoice_date": _field("25-8-2025"),
            "applicant_name": _field("BRB CABLE INDUSTRIES LIMITED"),
            "applicant_address": _field("BSCIC INDUSTRIAL ESTATE KUSHTIA - 7000 BANGLADESH"),
            "beneficiary_name": _field("HARESH PETROCHEM SINGAPORE PTE LTD."),
            "beneficiary_address": _field("1 NORTH BRIDGE ROAD, NO 16-07, HIGH STREET CENTRE, SINGAPORE 179094"),
            "currency_amount": _field("USD 15,640.00"),
            "goods_description": _field("MONO ETHYLENE GLYCOL"),
            "quantity": _field("18,400.000 KGS"),
            "unit_price": _field("850/MT"),
            "hs_codes": _field("2905.31.00 (CHINA) 2905.31.90 (BANGLADESH)"),
            "incoterms": _field("CFR CHATTOGRAM SEAPORT, BANGLADESH (INCOTERMS 2020)"),
            "port_of_loading": _field("QINGDAO, CHINA"),
            "port_of_discharge": _field("CHATTOGRAM SEAPORT, BANGLADESH"),
            "country_of_origin": _field("CHINA"),
            "vessel_name": _field("TERATAKI V.0XKMFS1NC/0XKMFS"),
        },
    )


def _build_certificate_of_origin(session_id: str) -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=uuid4().hex[:12],
        session_id=session_id,
        document_type=DocumentType.CERTIFICATE_OF_ORIGIN,
        original_filename="Certificate of origin.pdf",
        file_path="demo",
        extraction_method="ocr",
        uploaded_at=datetime.now(),
        raw_text="[Demo data — Certificate of Origin]",
        fields={
            "lc_number": _field("141325010091"),
            "applicant_name": _field("BRB CABLE INDUSTRIES LIMITED"),
            "applicant_address": _field("BSCIC INDUSTRIAL ESTATE KUSHTIA - 7000 BANGLADESH"),
            "beneficiary_name": _field("HARESH PETROCHEM SINGAPORE PTE LTD."),
            "goods_description": _field("MONO ETHYLENE GLYCOL"),
            "quantity": _field("18,400.000 KGS"),
            "hs_codes": _field("2905.31.00 (CHINA) 2905.31.90 (BANGLADESH)"),
            "incoterms": _field("CFR CHATTOGRAM SEAPORT, BANGLADESH (INCOTERMS 2020)"),
            "port_of_loading": _field("QINGDAO, CHINA"),
            "port_of_discharge": _field("CHATTOGRAM SEAPORT, BANGLADESH"),
            "country_of_origin": _field("CHINA"),
            "vessel_name": _field("TERATAKI V.0XKMFS1NC/0XKMFS"),
        },
    )


def _build_packing_list(session_id: str) -> ExtractedDocument:
    return ExtractedDocument(
        doc_id=uuid4().hex[:12],
        session_id=session_id,
        document_type=DocumentType.PACKING_LIST,
        original_filename="Packing list.pdf",
        file_path="demo",
        extraction_method="ocr",
        uploaded_at=datetime.now(),
        raw_text="[Demo data — Packing List]",
        fields={
            "lc_number": _field("141325010091"),
            "applicant_name": _field("BRB CABLE INDUSTRIES LIMITED"),
            "applicant_address": _field("BSCIC INDUSTRIAL ESTATE KUSHTIA - 7000 BANGLADESH"),
            "beneficiary_name": _field("HARESH PETROCHEM SINGAPORE PTE LTD."),
            "goods_description": _field("MONO ETHYLENE GLYCOL"),
            "quantity": _field("18,400.000 KGS"),
            "port_of_loading": _field("QINGDAO, CHINA"),
            "port_of_discharge": _field("CHATTOGRAM SEAPORT, BANGLADESH"),
            "vessel_name": _field("TERATAKI V.0XKMFS1NC/0XKMFS"),
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
