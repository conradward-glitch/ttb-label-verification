# Ready for GitHub Checklist

Final readiness checklist for the TTB Label Verification MVP.

## Repository Boundary

- [x] Project moved into a dedicated clean folder: `ttb-label-verification`
- [x] Unrelated `/mnt/c/Users/Conrad` profile files excluded
- [x] `node_modules`, `.venv`, caches, and `__pycache__` excluded
- [x] No batch upload or enterprise extras added

## Expected Top-Level Contents

- [x] `backend/`
- [x] `frontend/`
- [x] `samples/`
- [x] `docs/`
- [x] `Dockerfile`
- [x] `render.yaml`
- [x] `README.md`
- [x] `PROJECT_PLAN.md`
- [x] `APPROACH.md`
- [x] `CHANGELOG.md`
- [x] `HANDOFF.md`
- [x] `LICENSE`

Additional readiness file:

- [x] `READY_FOR_GITHUB.md`

## Backend Readiness

- [x] FastAPI app present
- [x] `/api/health` endpoint present
- [x] `/api/verify` endpoint present
- [x] `/api/ocr` endpoint present
- [x] Deterministic matching engine present
- [x] Government warning validator present
- [x] Tests present under `backend/tests/`
- [x] Backend test suite passes: 15 passed

## Frontend Readiness

- [x] React/Vite/TypeScript app present
- [x] Upload workflow present
- [x] Application data form present
- [x] Sample data loading present
- [x] Field-level PASS / FAIL / REVIEW result display present
- [x] OCR text display present

## Docker / Render Readiness

- [x] Dockerfile installs system Tesseract
- [x] Dockerfile builds frontend inside Docker
- [x] Dockerfile serves built frontend through FastAPI
- [x] Docker CMD starts Uvicorn on port 8000
- [x] `render.yaml` declares a Docker web service
- [x] Health check path set to `/api/health`
- [x] `docs/DEPLOYMENT.md` documents exact Render steps

## Sample Scenarios

- [x] Passing bourbon sample application present
- [x] ABV mismatch sample application present
- [x] Passing bourbon label image present
- [x] Government warning failure label image present
- [x] README documents how to run all sample scenarios
- [x] Sample scenario tests cover passing bourbon, ABV mismatch, and government warning failure

## Documentation Readiness

- [x] README includes setup instructions
- [x] README includes Docker instructions
- [x] README includes deployment instructions
- [x] README includes testing/sample instructions
- [x] README documents local WSL Tesseract limitation
- [x] Troubleshooting docs present
- [x] Deployment docs present

## Pre-Push Checks

Run from repository root before pushing:

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
```

```bash
cd frontend
npm install
npm run build
```

```bash
cd ..
docker build -t ttb-label-verification .
docker run --rm -p 8000:8000 ttb-label-verification
```

Then verify:

```bash
curl http://localhost:8000/api/health
curl -I http://localhost:8000/
```

## Remaining Intentional MVP Limits

- No batch upload
- No database
- No COLA integration
- No cloud OCR
- No LLM compliance judge
- No production federal authentication/compliance layer
