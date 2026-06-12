# README FIRST

## Purpose

This is the first document a future engineer should read before working on the Treasury / TTB AI-Powered Alcohol Label Verification project.

## Current Status

Single-label MVP implemented.

Implemented:

- FastAPI backend
- React/Vite/TypeScript frontend
- Tesseract/pytesseract OCR pipeline
- Deterministic matching engine
- Government warning validator
- PASS / FAIL / REVIEW field-level results
- Sample labels and application JSON
- Docker deployment support

Not implemented by design:

- Batch upload
- Database
- COLA integration
- Cloud OCR
- LLM compliance judge

## Project Purpose

Create a practical take-home prototype that helps TTB compliance agents verify alcohol label artwork against application data using OCR and deterministic matching.

## Where Code Lives

- `frontend/` — React/Vite/TypeScript UI
- `backend/` — FastAPI/Python OCR and matching API
- `samples/` — sample labels and application data
- `scripts/generate_sample_labels.py` — sample PNG generator
- `docs/` — architecture, decisions, handoff, troubleshooting

## How To Run Locally

Frontend dev:

```bash
cd frontend
npm install
npm run dev
```

Backend dev:

```bash
PYTHONPATH=backend uv run --with fastapi --with uvicorn --with pydantic --with pillow --with pytesseract --with python-multipart python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:5173`.

## One-URL Local Mode

```bash
cd frontend
npm install
npm run build
cd ..
PYTHONPATH=backend uv run --with fastapi --with uvicorn --with pydantic --with pillow --with pytesseract --with python-multipart python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## How To Deploy

Use Docker. The Dockerfile installs Tesseract.

```bash
cd frontend
npm install
npm run build
cd ..
docker build -t ttb-label-verification .
docker run -p 8000:8000 ttb-label-verification
```

Render can use `render.yaml` with health check `/api/health`.

## Most Important Project Files

- `README.md` — evaluator-facing entry point
- `backend/app/main.py` — FastAPI app
- `backend/app/ocr.py` — OCR pipeline
- `backend/app/matching.py` — matching engine
- `backend/app/warning.py` — government warning validation
- `frontend/src/main.tsx` — React UI
- `docs/HANDOFF.md` — engineer takeover guide
- `docs/TROUBLESHOOTING.md` — operational fixes

## Verification Commands

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
cd frontend && npm run build
```
