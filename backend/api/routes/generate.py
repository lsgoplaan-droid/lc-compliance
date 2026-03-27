"""API route to generate supporting documents from an uploaded LC advice."""

import os
from uuid import uuid4
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.enums import DocumentType
from models.schemas import ExtractedDocument, SessionResponse
from services.document_generator import generate_all_documents
from services.pdf_generator import generate_pdf
from services.document_parser import DocumentParser
from storage.session_store import session_store

router = APIRouter(tags=["generate"])

ALL_DOC_TYPES = [
    "commercial_invoice",
    "bill_of_lading",
    "certificate_of_origin",
    "packing_list",
]


class GenerateRequest(BaseModel):
    doc_types: Optional[list[str]] = None  # None = all


@router.post("/sessions/{session_id}/generate", response_model=SessionResponse)
def generate_supporting_docs(session_id: str, body: GenerateRequest = GenerateRequest()):
    """Generate supporting documents (as PDFs) from the uploaded LC advice.

    Pass doc_types to generate specific documents, or omit for all four.
    """
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.lc_document:
        raise HTTPException(status_code=400, detail="LC advice must be uploaded first")

    requested = body.doc_types or ALL_DOC_TYPES
    # Validate
    for dt in requested:
        if dt not in ALL_DOC_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid doc type: {dt}")

    lc_fields = session.lc_document.fields

    # Generate text content for requested types
    all_generated = generate_all_documents(lc_fields)
    generated = {k: v for k, v in all_generated.items() if k in requested}

    parser = DocumentParser()
    new_docs = []

    # Keep existing docs that weren't regenerated
    for existing in session.supporting_documents:
        if existing.document_type.value not in requested:
            new_docs.append(existing)

    for doc_type_str, content in generated.items():
        doc_type = DocumentType(doc_type_str)
        doc_id = uuid4().hex[:12]
        fname = f"Generated_{doc_type_str}.pdf"

        # Generate PDF and save to uploads folder
        from config import UPLOAD_DIR
        upload_dir = UPLOAD_DIR / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(upload_dir / fname)
        generate_pdf(content, pdf_path, doc_type_str)

        # Parse the PDF through normal extraction pipeline
        _, raw_text, fields = parser.parse(pdf_path, doc_type_str)

        doc = ExtractedDocument(
            doc_id=doc_id,
            session_id=session_id,
            document_type=doc_type,
            original_filename=fname,
            file_path=pdf_path,
            extraction_method="generated",
            uploaded_at=datetime.now(),
            raw_text=raw_text,
            fields=fields,
        )
        new_docs.append(doc)

    session.supporting_documents = new_docs
    session.comparison_results = None
    session.report = None
    session_store.save(session)

    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        lc_uploaded=True,
        supporting_doc_count=len(new_docs),
        has_comparison=False,
    )
