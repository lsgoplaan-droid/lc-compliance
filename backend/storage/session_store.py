import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import SESSIONS_DIR
from models.schemas import Session


class SessionStore:
    def _path(self, session_id: str) -> Path:
        return SESSIONS_DIR / f"{session_id}.json"

    def create(self, session_id: str) -> Session:
        session = Session(session_id=session_id, created_at=datetime.now())
        self.save(session)
        return session

    def get(self, session_id: str) -> Optional[Session]:
        p = self._path(session_id)
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return Session.model_validate(data)

    def save(self, session: Session) -> None:
        p = self._path(session.session_id)
        p.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    def list_all(self) -> list[Session]:
        sessions = []
        for p in SESSIONS_DIR.glob("*.json"):
            data = json.loads(p.read_text(encoding="utf-8"))
            sessions.append(Session.model_validate(data))
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def delete(self, session_id: str) -> bool:
        p = self._path(session_id)
        if p.exists():
            p.unlink()
            return True
        return False


session_store = SessionStore()
