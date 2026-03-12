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

# OCR settings (uses rapidocr-onnxruntime, no system packages needed)
OCR_MIN_CHARS_PER_PAGE = 50
OCR_DPI = int(os.environ.get("OCR_DPI", "300"))  # 300 for local, set 150 on Render free tier
OCR_MAX_DIM = int(os.environ.get("OCR_MAX_DIM", "3600"))  # cap image dimension

# CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
