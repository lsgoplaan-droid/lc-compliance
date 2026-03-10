import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

UPLOAD_DIR = BASE_DIR / "uploads"
SESSIONS_DIR = BASE_DIR / "sessions"

UPLOAD_DIR.mkdir(exist_ok=True)
SESSIONS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = {".pdf", ".txt"}

# Fuzzy matching thresholds
FUZZY_NAME_THRESHOLD = 0.85
FUZZY_ADDRESS_THRESHOLD = 0.70
FUZZY_GOODS_THRESHOLD = 0.75
FUZZY_PORT_THRESHOLD = 0.85

# OCR settings
OCR_MIN_CHARS_PER_PAGE = 50

import shutil

def _find_tesseract() -> str:
    """Find Tesseract binary: env var > system PATH > local extracted."""
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd and os.path.isfile(env_cmd):
        return env_cmd
    system_cmd = shutil.which("tesseract")
    if system_cmd:
        return system_cmd
    # Check locally extracted (Render build)
    local_cmd = str(BASE_DIR / "tesseract_local" / "usr" / "bin" / "tesseract")
    if os.path.isfile(local_cmd):
        return local_cmd
    # Windows default
    win_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.isfile(win_default):
        return win_default
    return ""

TESSERACT_CMD = _find_tesseract()

# Set LD_LIBRARY_PATH for locally extracted tesseract
_local_lib = str(BASE_DIR / "tesseract_local" / "usr" / "lib")
if os.path.isdir(_local_lib):
    os.environ["LD_LIBRARY_PATH"] = _local_lib + ":" + os.environ.get("LD_LIBRARY_PATH", "")

# CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
