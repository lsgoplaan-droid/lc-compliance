from fastapi import APIRouter, HTTPException

from models.schemas import DocumentComparison
from storage.session_store import session_store
from services.comparison_engine import comparison_engine

router = APIRouter(tags=["compare"])


@router.post("/sessions/{session_id}/compare", response_model=list[DocumentComparison])
def run_comparison(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.lc_document:
        raise HTTPException(status_code=400, detail="No LC advice document uploaded")
    if not session.supporting_documents:
        raise HTTPException(status_code=400, detail="No supporting documents uploaded")

    results = []
    for doc in session.supporting_documents:
        comparison = comparison_engine.compare_document(session.lc_document, doc)
        results.append(comparison)

    session.comparison_results = results
    session_store.save(session)
    return results


@router.get("/sessions/{session_id}/compare/{doc_id}", response_model=DocumentComparison)
def get_comparison(session_id: str, doc_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.comparison_results:
        raise HTTPException(status_code=400, detail="No comparison results. Run comparison first.")

    for result in session.comparison_results:
        if result.doc_id == doc_id:
            return result
    raise HTTPException(status_code=404, detail="Comparison not found for this document")
