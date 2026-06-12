# Engineering Handoff

## Current Status

Single-label MVP implemented. Batch upload has not been implemented by design.

## Project Goal

A take-home prototype for AI-powered alcohol label verification. Reviewers upload a label, enter application data, run OCR, and receive PASS / FAIL / REVIEW results.

## Architecture Summary

- Frontend: React + Vite + TypeScript in `frontend/`
- Backend: FastAPI + Python in `backend/`
- OCR: Tesseract via pytesseract, with Pillow preprocessing
- Matching: deterministic Python matching engine
- Deployment: Docker with Tesseract installed; FastAPI serves built React frontend from `frontend/dist`

## File Structure

```text
frontend/                 React UI
backend/app/main.py       FastAPI API and static frontend serving
backend/app/ocr.py        OCR pipeline
backend/app/matching.py   Field matching and status aggregation
backend/app/warning.py    Government warning validation
backend/tests/            pytest coverage
samples/                  Sample labels and application data
Dockerfile
render.yaml
```

## Setup Steps

Install frontend dependencies:

```bash
cd frontend
npm install
```

Backend testing with uv:

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
```

Install local OCR if available:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

## Local Development

Backend:

```bash
PYTHONPATH=backend uv run --with fastapi --with uvicorn --with pydantic --with pillow --with pytesseract --with python-multipart python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

## One-URL Mode

```bash
cd frontend
npm run build
cd ..
PYTHONPATH=backend uv run --with fastapi --with uvicorn --with pydantic --with pillow --with pytesseract --with python-multipart python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Deployment Steps

```bash
cd frontend
npm install
npm run build
cd ..
docker build -t ttb-label-verification .
docker run -p 8000:8000 ttb-label-verification
```

For Render, use `render.yaml` or create a Docker web service with health check `/api/health`.

## Testing Process

Backend:

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
```

Frontend:

```bash
cd frontend
npm run build
```

## Known Issues

- Local OCR requires system Tesseract. Without it, OCR returns REVIEW instead of crashing.
- OCR may struggle with small warning text, glare, skew, or low resolution.
- Bold styling in the warning cannot be confirmed reliably by OCR.
- No database, authentication, COLA integration, or batch upload in MVP.

## Future Improvements

- Batch upload
- Bounding-box evidence highlighting
- Rule profiles for beer/wine/spirits
- CSV/JSON export
- Better image preprocessing and deskewing
