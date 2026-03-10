from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from models.enums import DocumentType
from models.schemas import ExtractedDocument, UploadResponse
from storage.session_store import session_store
from storage.file_store import file_store
from services.document_parser import document_parser

router = APIRouter(tags=["upload"])


@router.post("/sessions/{session_id}/upload", response_model=UploadResponse)
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    allowed_ext = (".pdf", ".txt")
    if not file.filename or not any(file.filename.lower().endswith(ext) for ext in allowed_ext):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are accepted")

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 20MB limit")

    saved_path = file_store.save(session_id, file.filename, content)

    doc_id = uuid4().hex[:12]
    raw_text, extraction_method, fields = document_parser.parse(
        str(saved_path), document_type
    )

    doc = ExtractedDocument(
        doc_id=doc_id,
        session_id=session_id,
        document_type=document_type,
        original_filename=file.filename,
        file_path=str(saved_path),
        extraction_method=extraction_method,
        uploaded_at=datetime.now(),
        raw_text=raw_text,
        fields=fields,
    )

    if document_type == DocumentType.LC_ADVICE:
        session.lc_document = doc
    else:
        session.supporting_documents.append(doc)

    # Clear previous comparison when new docs are added
    session.comparison_results = None
    session.report = None
    session_store.save(session)

    return UploadResponse(
        doc_id=doc.doc_id,
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        extraction_method=doc.extraction_method,
        fields=doc.fields,
        field_count=len([f for f in doc.fields.values() if f.value]),
    )
