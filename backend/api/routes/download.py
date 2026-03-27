"""Download endpoint for generated PDF documents."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from storage.session_store import session_store

router = APIRouter(tags=["download"])


@router.get("/sessions/{session_id}/download/{doc_id}")
def download_document(session_id: str, doc_id: str):
    """Download a generated document PDF by its doc_id."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Find the document
    doc = None
    for d in session.supporting_documents:
        if d.doc_id == doc_id:
            doc = d
            break

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,
        media_type="application/pdf",
    )
