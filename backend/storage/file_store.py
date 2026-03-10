import shutil
from pathlib import Path
from uuid import uuid4

from config import UPLOAD_DIR


class FileStore:
    def save(self, session_id: str, filename: str, content: bytes) -> Path:
        session_dir = UPLOAD_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid4().hex[:8]}_{filename}"
        file_path = session_dir / safe_name
        file_path.write_bytes(content)
        return file_path

    def get_path(self, session_id: str, filename: str) -> Path | None:
        session_dir = UPLOAD_DIR / session_id
        for f in session_dir.iterdir():
            if f.name.endswith(filename):
                return f
        return None

    def delete_file(self, file_path: str) -> None:
        p = Path(file_path)
        if p.exists():
            p.unlink()

    def delete_session_files(self, session_id: str) -> None:
        session_dir = UPLOAD_DIR / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)


file_store = FileStore()
