# AI-Powered Alcohol Label Verification App

A practical Treasury / TTB take-home prototype for single-label alcohol label verification.

The app lets a reviewer upload label artwork, enter expected application data, run local OCR, and receive explainable PASS / FAIL / REVIEW results for core compliance fields.

## Features

- Single-label PNG/JPG upload
- OCR extraction through Tesseract / pytesseract
- Application data entry for the core take-home workflow:
  - Brand Name
  - Class/Type
  - Alcohol Content
  - Net Contents
- Government Warning validation from OCR text
- Overall PASS / FAIL / REVIEW status
- Extracted OCR text display
- Friendly upload and verification errors
- Sample label/application test cases
- No database
- No COLA integration
- No cloud OCR dependency
- No LLM compliance judge

## Architecture Diagram

```text
Browser UI
  |
  v
React + Vite + TypeScript Frontend
  |
  v
FastAPI Backend
  |
  +--> OCR Pipeline: Pillow preprocessing + Tesseract OCR
  |
  +--> Matching Engine: deterministic field checks
  |
  +--> Government Warning Validator
  |
  v
Structured PASS / FAIL / REVIEW Result JSON
```

## Technology Stack

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Python
- OCR: Tesseract via pytesseract
- Image preprocessing: Pillow
- Matching: deterministic Python normalization, regex, and conservative fuzzy logic
- Tests: pytest
- Deployment: Docker with Tesseract installed; Render/Railway/Fly compatible

## Installation Instructions

### System OCR Dependency

Tesseract must be installed for OCR to work locally.

Ubuntu/WSL:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

If Tesseract is not installed, the backend returns REVIEW with a clear OCR message instead of crashing. In WSL or local Linux environments, OCR requires installing `tesseract-ocr`; using Docker avoids that local dependency because the Docker image installs Tesseract automatically.

### Backend Dependencies

Recommended with `uv` for one-shot test runs:

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
```

Standard Python virtual environment setup:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

Run the backend from the repository root after activating the virtual environment:

```bash
PYTHONPATH=backend python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Dependencies

```bash
cd frontend
npm install
```

## Local Development Instructions

Terminal 1 — backend:

```bash
PYTHONPATH=backend uv run --with fastapi --with uvicorn --with pydantic --with pillow --with pytesseract --with python-multipart python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 — frontend:

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

## One-URL Local Production Mode

Build frontend:

```bash
cd frontend
npm run build
```

Run FastAPI from the repo root:

```bash
PYTHONPATH=backend uv run --with fastapi --with uvicorn --with pydantic --with pillow --with pytesseract --with python-multipart python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000
```

FastAPI serves the built React frontend from `frontend/dist` when present.

## Deployment Instructions

Preferred deployment is Docker on Render/Railway/Fly.

Docker build from the repository root:

```bash
docker build -t ttb-label-verification .
docker run -p 8000:8000 ttb-label-verification
```

The Dockerfile builds the React frontend, installs Python dependencies, installs system Tesseract, and serves the built frontend through FastAPI from one URL.

Render:

- Use the included `render.yaml`, or create a Docker web service.
- Root directory: repository root.
- Environment: Docker.
- Health check path: `/api/health`.
- Public app URL serves both API and frontend.
- Expected runtime on Render free tier is usually around 9–11 seconds for OCR verification after the service is awake; first request after sleep can be slower. The intended sub-5-second target remains a future optimization goal, not the current deployed behavior.
- See `docs/DEPLOYMENT.md` for exact Render steps.

## Testing Instructions

Backend tests:

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
```

Frontend build check:

```bash
cd frontend
npm run build
```

Required test scenarios included:

- Passing bourbon label
- ABV mismatch
- Government warning failure

## Sample Data Instructions

Application JSON:

- `samples/applications/passing-bourbon.json`
- `samples/applications/abv-mismatch.json`

Generated label images:

- `samples/labels/passing-bourbon-label.png`
- `samples/labels/government-warning-failure-label.png`

Use the included files directly in the UI:

1. Click `Load sample data` for the passing bourbon expected values.
2. Upload `samples/labels/passing-bourbon-label.png` for the passing case.
3. Paste `samples/applications/abv-mismatch.json` and upload the passing label for the ABV mismatch case.
4. Use `samples/labels/government-warning-failure-label.png` with the passing bourbon application data for the government warning failure case.

## Assumptions

- Prototype is standalone and does not integrate with COLA.
- No authentication is required for take-home review.
- Uploaded images do not need persistent storage.
- Tesseract OCR is acceptable for MVP demonstration.
- Government warning bold styling cannot be reliably confirmed with basic OCR.

## Limitations

- OCR can struggle with glare, skew, tiny print, and low-resolution images.
- No batch upload in MVP.
- No persistent storage or audit trail.
- No production federal security/compliance controls.

## Future Enhancements

- Batch upload after single-label flow is proven
- Optional common label elements such as Bottler/Producer Name and Address and Country of Origin for imports
- Bounding-box evidence highlighting
- Beer/wine/spirits rule profiles
- Exportable CSV/JSON reports
- Better image preprocessing
- Accessibility polish

## Important Docs

- `PROJECT_PLAN.md`
- `APPROACH.md`
- `HANDOFF.md`
- `docs/README-FIRST.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/TROUBLESHOOTING.md`

