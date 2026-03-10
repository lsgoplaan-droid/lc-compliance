from fastapi import APIRouter, HTTPException

from models.schemas import ExtractedDocument, ExtractedField, FieldUpdateRequest
from storage.session_store import session_store
from storage.file_store import file_store

router = APIRouter(tags=["documents"])


@router.get("/sessions/{session_id}/documents", response_model=list[ExtractedDocument])
def list_documents(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    docs = []
    if session.lc_document:
        docs.append(session.lc_document)
    docs.extend(session.supporting_documents)
    return docs


@router.get("/sessions/{session_id}/documents/{doc_id}", response_model=ExtractedDocument)
def get_document(session_id: str, doc_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    doc = _find_doc(session, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/sessions/{session_id}/documents/{doc_id}")
def delete_document(session_id: str, doc_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.lc_document and session.lc_document.doc_id == doc_id:
        file_store.delete_file(session.lc_document.file_path)
        session.lc_document = None
    else:
        found = False
        for i, doc in enumerate(session.supporting_documents):
            if doc.doc_id == doc_id:
                file_store.delete_file(doc.file_path)
                session.supporting_documents.pop(i)
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail="Document not found")

    session.comparison_results = None
    session.report = None
    session_store.save(session)
    return {"detail": "Document deleted"}


@router.patch("/sessions/{session_id}/documents/{doc_id}/fields")
def update_fields(session_id: str, doc_id: str, req: FieldUpdateRequest):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    doc = _find_doc(session, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    for field_name, new_value in req.fields.items():
        if field_name in doc.fields:
            doc.fields[field_name].value = new_value
            doc.fields[field_name].manually_corrected = True
        else:
            doc.fields[field_name] = ExtractedField(
                value=new_value, confidence=1.0, manually_corrected=True
            )

    session.comparison_results = None
    session.report = None
    session_store.save(session)
    return {"detail": "Fields updated", "updated_count": len(req.fields)}


def _find_doc(session, doc_id):
    if session.lc_document and session.lc_document.doc_id == doc_id:
        return session.lc_document
    for doc in session.supporting_documents:
        if doc.doc_id == doc_id:
            return doc
    return None
