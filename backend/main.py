from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import FRONTEND_URL
from api.routes import sessions, upload, documents, compare, reports

app = FastAPI(title="LC Compliance Checker", version="1.0.0")

allowed_origins = [o.strip() for o in FRONTEND_URL.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/api/health")
def health():
    import shutil
    import subprocess
    tesseract_path = shutil.which("tesseract")
    tesseract_version = None
    if tesseract_path:
        try:
            result = subprocess.run([tesseract_path, "--version"], capture_output=True, text=True)
            tesseract_version = result.stdout.split("\n")[0] if result.stdout else result.stderr.split("\n")[0]
        except Exception:
            pass
    from services.ocr_extractor import OCR_AVAILABLE
    return {
        "status": "ok",
        "tesseract_path": tesseract_path,
        "tesseract_version": tesseract_version,
        "ocr_available": OCR_AVAILABLE,
    }
