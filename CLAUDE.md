# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LC Compliance Checker — a web app that compares a bank's Letter of Credit (LC) advice against supporting trade documents (Invoice, Certificate of Origin, Bill of Lading, Packing List) to verify field-level compliance per UCP 600 rules.

## Commands

### Backend (Python FastAPI)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001
```
Note: Port 8000 may be occupied; use 8001. Tesseract OCR must be installed (currently at `C:\Program Files\Tesseract-OCR\tesseract.exe`).

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev      # Dev server on http://localhost:5173
npm run build    # TypeScript check + production build
npm run lint     # ESLint
```

The Vite dev server proxies `/api` requests to `http://localhost:8001`.

### Testing
No test suite exists yet. pytest and httpx are in backend requirements for future use.

## Deployment

Split deployment: **Netlify** (frontend) + **Render** (backend API).

- `netlify.toml` — Builds `frontend/dist`, proxies `/api/*` to `https://lc-compliance.onrender.com`
- `render.yaml` — Python web service, 1 worker, free tier (512MB RAM)
- `backend/Dockerfile` — Python 3.12-slim with system Tesseract; used if deploying via Docker

### Environment Variables
- `FRONTEND_URL` (backend) — CORS origin, default `http://localhost:5173`
- `PORT` (backend) — Render assigns dynamically, default `8000`
- `PYTHON_VERSION` — Set to `3.12.0` on Render

### OCR Memory Constraints
Render free tier has 512MB RAM. OCR (rapidocr-onnxruntime) can OOM on large/high-DPI scans. Current mitigations: reduced DPI and image size caps in `ocr_extractor.py`. Future option: migrate to AWS Lambda or Google Cloud Run for more RAM headroom.

## Architecture

### Data Flow
1. Frontend creates a **session** (UUID-based, stored as JSON files in `backend/sessions/`)
2. User uploads LC advice (PDF or TXT), then supporting documents
3. Backend **extracts text** (PyMuPDF for PDFs, direct read for TXT, OCR fallback for scanned PDFs)
4. Document-type-specific **field extractors** (regex-based) parse structured fields from raw text
5. **Comparison engine** matches LC fields against each supporting document using configurable strategies
6. **Report generator** aggregates results with UCP 600 rule validation

### OCR Pipeline
Text extraction order: PyMuPDF (fast, text-based PDFs) → rapidocr-onnxruntime fallback (scanned PDFs, triggered when <50 chars extracted per page). Tesseract is available in Docker but rapidocr is the primary OCR engine in production.

### Backend (`backend/`)
- `main.py` — FastAPI app, all routes prefixed with `/api`
- `api/routes/` — REST endpoints: sessions, upload, documents, compare, reports
- `extractors/` — Per-document-type field extraction (LC advice, invoice, B/L, C/O, packing list). Each extends `BaseFieldExtractor` with regex patterns.
- `services/` — Core logic:
  - `document_parser.py` — Orchestrates text extraction → field extraction; handles PDF vs TXT
  - `text_extractor.py` — PyMuPDF-based PDF/TXT text extraction
  - `ocr_extractor.py` — rapidocr-onnxruntime OCR with memory-constrained image processing
  - `comparison_engine.py` — 6 match strategies: exact, fuzzy, numeric, date, boolean, contains
  - `fuzzy_matcher.py` — rapidfuzz wrapper with name/address normalization
  - `report_generator.py` — Aggregates comparisons into compliance report
- `rules/` — `field_mappings.py` maps LC fields to corresponding doc fields; `match_config.py` defines strategy/threshold/severity per field; `ucp600.py` applies cross-field UCP 600 rules
- `storage/` — JSON file-based session and file persistence (no database)
- `config.py` — Thresholds, paths, allowed extensions

### API Routes
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/sessions` | Create new session |
| GET | `/api/sessions/{id}` | Get session details |
| POST | `/api/sessions/{id}/upload` | Upload document (file + document_type) |
| GET | `/api/documents/{id}` | Get document with extracted fields |
| POST | `/api/sessions/{id}/compare` | Run field-level comparison |
| GET | `/api/sessions/{id}/reports` | Get compliance report |
| GET | `/api/health` | Health check |

### Frontend (`frontend/src/`)
- 4-step wizard UI: Upload → Review → Compare → Report
- `context/SessionContext.tsx` — Central state (session, documents, comparisons, report)
- `api/` — Axios client with `/api` baseURL
- `types/` — Uses `const` objects + type aliases (not enums) due to `erasableSyntaxOnly`
- `components/` — Reusable UI: FileDropzone, FieldComparisonTable, MatchStatusBadge, etc.

### Key Design Decisions
- **No AI API for parsing** — All extraction is regex + rule-based to avoid API costs
- **Type-only imports required** — Vite config enforces `verbatimModuleSyntax`; use `import type` for type-only imports
- **No TypeScript enums** — `erasableSyntaxOnly` is enabled; use `as const` objects with type aliases instead
- **File-based storage** — Sessions persist as JSON in `backend/sessions/`, uploads in `backend/uploads/`
- **Comparison is cached** — Stored in session; cleared when new documents are uploaded

### Reference Documents
Sample test documents are in `reference/` (Invoice.pdf, Certificate of origin.pdf, Packing list.pdf, LC advice TXT).
