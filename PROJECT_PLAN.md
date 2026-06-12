# Treasury / TTB AI-Powered Alcohol Label Verification — Completed Project Summary

## Current Status

The single-label MVP is implemented and ready for repository submission.

This project is a practical take-home prototype that helps TTB label compliance reviewers compare alcohol label artwork against expected application data and classify each submission as PASS, FAIL, or REVIEW.

## Objective Delivered

The prototype lets a reviewer:

1. Open a local or deployed web app.
2. Upload one PNG/JPG alcohol label image.
3. Enter expected application data.
4. Run OCR on the label image.
5. Review field-level verification results.
6. See an overall PASS / FAIL / REVIEW outcome.
7. Inspect extracted OCR text for confidence and manual review.

## Evaluation North Star

A reviewer should be able to understand the repository quickly, run the app locally or through Docker, load the included samples, and see clear verification results without needing external OCR services, a database, or COLA integration.

## Implemented Scope

### Frontend

- React + Vite + TypeScript single-page interface
- Label image upload
- Image preview
- Application data form for:
  - Brand Name
  - Class/Type
  - Alcohol Content
  - Net Contents
- Load sample data button
- Overall PASS / FAIL / REVIEW result display
- Field-level result cards
- Extracted OCR text panel
- Friendly validation and verification errors

### Backend

- FastAPI application
- `/api/health` health endpoint
- `/api/ocr` OCR endpoint
- `/api/verify` verification endpoint
- Multipart upload handling
- PNG/JPG filename validation
- Structured result responses
- Built React frontend served by FastAPI from one URL when `frontend/dist` exists

### OCR

- Tesseract OCR through `pytesseract`
- Pillow image preprocessing
- Graceful REVIEW response if OCR is unavailable or image text cannot be extracted confidently
- No cloud OCR dependency

### Verification Engine

- Deterministic matching engine
- Normalization for capitalization, whitespace, punctuation, and apostrophe variants
- Brand name verification
- Class/type verification
- Alcohol content verification using ABV/proof extraction
- Net contents verification using unit normalization
- Government warning validation with required wording checks
- PASS / FAIL / REVIEW aggregation
- Field-level explanations with expected/found/evidence values where available

### Samples

Included sample files support the core review scenarios:

- Passing bourbon application data
- ABV mismatch application data
- Passing bourbon label image
- Government warning failure label image

### Tests

Backend tests cover:

- Health endpoint
- Upload type rejection
- OCR helper behavior
- Matching behavior
- Government warning validation
- Sample scenario expectations

Current backend test status: 15 passed.

### Deployment

Deployment is configured for a Docker-based one-service app.

Implemented deployment assets:

- Root `Dockerfile`
- `render.yaml`
- `docs/DEPLOYMENT.md`

The Dockerfile:

1. Builds the React frontend in a Node stage.
2. Installs system `tesseract-ocr` in the Python runtime image.
3. Installs backend Python dependencies.
4. Copies the built frontend to `frontend/dist`.
5. Starts FastAPI with Uvicorn on port 8000.

Render can deploy the repository as a Docker web service with `/api/health` as the health check path.

## Technology Choices

### React + Vite + TypeScript

Selected for a polished, fast, structured single-page reviewer workflow.

### FastAPI + Python

Selected because Python has strong OCR/image-processing libraries, FastAPI is simple to test and deploy, and the backend can remain small and reviewable.

### Tesseract OCR

Selected because it runs locally, avoids external credentials, and works inside Docker for a portable evaluation environment.

### Deterministic Matching

Selected because compliance review needs explainable, repeatable behavior. The MVP intentionally avoids opaque LLM judgment for regulatory checks.

### Docker / Render

Selected to keep deployment simple and provide a single public URL path. Docker also controls the Tesseract system dependency.

## Stakeholder Fit

### Compliance Leadership

The MVP reduces routine manual matching work and presents clear results that map to existing review decisions.

### IT / Operations

The MVP avoids direct COLA integration, avoids external OCR APIs, avoids persistent storage, and keeps deployment simple.

### Compliance Agents

The MVP preserves human judgment by using REVIEW for uncertain cases and showing extracted OCR evidence instead of hiding model behavior.

## Intentional Non-Scope

The following were intentionally excluded from the MVP:

- Batch upload
- Database or persistent storage
- COLA integration
- Cloud OCR
- LLM-based compliance judgment
- Authentication
- Production federal security controls
- Audit trail and retention workflows

These are suitable future enhancements after the single-label workflow is proven.

## Known Limitations

- OCR can struggle with glare, skew, tiny print, or low-resolution images.
- Local runs require system Tesseract unless Docker is used.
- Government warning bold styling cannot be reliably confirmed with basic OCR.
- The current upload validation checks supported file extensions but does not implement upload size enforcement.
- The prototype is not a production federal compliance system.

## Repository Map

```text
backend/                  FastAPI backend, OCR, matching, tests
frontend/                 React/Vite/TypeScript frontend
samples/                  Included sample labels and application JSON
docs/                     Architecture, deployment, decisions, handoff, troubleshooting
Dockerfile                Docker deployment image with Tesseract
render.yaml               Render Docker web service config
README.md                 Primary evaluator entry point
APPROACH.md               Design rationale and tradeoffs
HANDOFF.md                Short engineering handoff
CHANGELOG.md              Version history
LICENSE                   Project license
```

## Verification Commands

Backend tests:

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
```

Frontend build:

```bash
cd frontend
npm install
npm run build
```

Docker smoke test:

```bash
docker build -t ttb-label-verification .
docker run --rm -p 8000:8000 ttb-label-verification
```

Health check:

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

## Submission State

The repository now represents the completed single-label MVP implementation record. Future work should build on this foundation without expanding the initial submission scope.
