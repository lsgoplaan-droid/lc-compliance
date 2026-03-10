from fastapi import APIRouter, HTTPException

from models.schemas import ComplianceReport
from storage.session_store import session_store
from services.report_generator import report_generator

router = APIRouter(tags=["reports"])


@router.get("/sessions/{session_id}/report", response_model=ComplianceReport)
def get_report(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.comparison_results:
        raise HTTPException(status_code=400, detail="No comparison results. Run comparison first.")

    report = report_generator.generate(session)
    session.report = report
    session_store.save(session)
    return report
