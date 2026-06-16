# AI-Powered Alcohol Label Verification App

A practical Treasury / TTB take-home prototype for single-label alcohol label verification.

The app lets a reviewer upload label artwork, enter expected application data, and receive explainable PASS / FAIL / REVIEW results for core compliance fields — powered by Claude Vision AI with local Tesseract OCR as fallback.

## Features

- Single-label PNG/JPG upload
- AI-powered OCR via Claude Vision (primary) with Tesseract / pytesseract as local fallback
- Application data entry for the core take-home workflow:
  - Brand Name
  - Class/Type
  - Bottler/Producer Name and Address
  - Alcohol Content
  - Net Contents
  - Country of Origin (conditional — verified when supplied for imports)
- Government Warning validation from OCR text
- Overall PASS / FAIL / REVIEW status
- Field-level explainable results with evidence
- Extracted OCR text display
- Friendly upload and verification errors
- Sample label/application test cases
- No database
- No COLA integration
- No external AI call required for baseline operation

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
  +--> OCR Pipeline: Claude Vision primary + local Tesseract fallback
  |
  +--> Matching Engine: deterministic field checks
  |
  +--> Government Warning Validator
  |
  v
Structured PASS / FAIL / REVIEW Result JSON
```

## Design Decisions

This prototype focuses on the single-label verification workflow described in the Treasury take-home assignment.
Several design decisions were made to balance accuracy, explainability, and implementation time:

- Claude Vision is used as the primary OCR engine because alcohol labels often contain decorative fonts, logos, borders, and complex layouts that are difficult for traditional OCR systems to read reliably.
- Tesseract OCR is retained as a local fallback so the application can continue operating when external AI services are unavailable.
- PASS / FAIL / REVIEW classifications were chosen to reflect real compliance workflows. Uncertain OCR results are routed to REVIEW rather than automatically approved or rejected.
- Verification logic uses deterministic rules and conservative matching behavior to reduce false approvals while still handling common OCR noise.
- The prototype intentionally focuses on a single-label workflow rather than batch processing so the core verification experience can be evaluated first.

The goal of the prototype is to assist compliance reviewers, not replace human judgment.

## Technology Stack

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Python
- OCR: Claude Vision (claude-sonnet-4-6) when `ANTHROPIC_API_KEY` is set; Tesseract via pytesseract as local fallback
- Image preprocessing: Pillow
- Matching: deterministic Python normalization, regex, and conservative fuzzy logic
- Tests: pytest
- Deployment: Docker with Tesseract installed; Render/Railway/Fly compatible

## Installation Instructions

### System OCR Dependency

Tesseract must be installed for local OCR fallback to work.

Ubuntu/WSL:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

If Tesseract is not installed, the backend returns REVIEW with a clear OCR message instead of crashing. Using Docker avoids that local dependency because the Docker image installs Tesseract automatically.

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
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_key_here ttb-label-verification
```

The Dockerfile builds the React frontend, installs Python dependencies, installs system Tesseract, and serves the built frontend through FastAPI from one URL.

Render:

- Use the included `render.yaml`, or create a Docker web service.
- Root directory: repository root.
- Environment: Docker.
- Health check path: `/api/health`.
- Optional environment variable: `ANTHROPIC_API_KEY` enables Claude Vision as the primary OCR path. If not set, or if the API fails, the app uses local Tesseract OCR fallback. No external AI call is required for baseline operation.
- With Claude Vision active, verification completes in approximately 3-5 seconds on Render free tier.
- Without Claude Vision, Tesseract verification runs in approximately 8-11 seconds on Render free tier.
- First request after a free tier sleep can be slower due to cold start.
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
- Government warning bold styling cannot be reliably confirmed via OCR alone; agents should verify formatting manually on REVIEW results.
- Country of Origin is only verified when supplied in the application data; an empty field is treated as a domestic product and skipped.
- TTB label requirements per Beverage Alcohol Manual (BAM) Chapter 1, distilled spirits.

## Limitations

- OCR can struggle with glare, skew, tiny print, and low-resolution images.
- No batch upload in MVP.
- No persistent storage or audit trail.
- No production federal security/compliance controls.
- Claude Vision requires an outbound connection to api.anthropic.com; Tesseract fallback operates fully offline.

## Future Enhancements

- Batch upload after single-label flow is proven
- Bounding-box evidence highlighting on label image
- Beer/wine/spirits rule profiles
- Exportable CSV/JSON audit reports
- Accessibility polish
- State of distillation verification for whiskey
- Commodity statement verification for blended spirits

## Important Docs

- `PROJECT_PLAN.md`
- `APPROACH.md`
- `HANDOFF.md`
- `docs/README-FIRST.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/TROUBLESHOOTING.md`
