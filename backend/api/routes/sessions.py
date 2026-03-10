from uuid import uuid4

from fastapi import APIRouter, HTTPException

from models.schemas import SessionResponse
from storage.session_store import session_store
from storage.file_store import file_store

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=SessionResponse)
def create_session():
    session_id = uuid4().hex[:12]
    session = session_store.create(session_id)
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        lc_uploaded=False,
        supporting_doc_count=0,
        has_comparison=False,
    )


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions():
    sessions = session_store.list_all()
    return [
        SessionResponse(
            session_id=s.session_id,
            created_at=s.created_at,
            lc_uploaded=s.lc_document is not None,
            supporting_doc_count=len(s.supporting_documents),
            has_comparison=s.comparison_results is not None,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        lc_uploaded=session.lc_document is not None,
        supporting_doc_count=len(session.supporting_documents),
        has_comparison=session.comparison_results is not None,
    )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    if not session_store.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    file_store.delete_session_files(session_id)
    return {"detail": "Session deleted"}
