# Troubleshooting

## OCR Failures

### Symptom

OCR returns empty text or the app returns REVIEW with a Tesseract message.

### Likely Causes

- Tesseract is not installed locally
- Tesseract is not in PATH
- Image is too low resolution
- Label has glare, skew, or tiny text
- File is not a PNG/JPG image

### Fixes

Check Tesseract:

```bash
tesseract --version
```

Install Tesseract on Ubuntu/WSL:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

Use the Docker deployment path if local install is blocked; the Dockerfile installs Tesseract automatically.

## Missing Python Dependencies

Use uv:

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
```

Or venv:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If `python -m venv` fails on Ubuntu/WSL, install `python3-venv` or use uv.

## Missing Frontend Dependencies

```bash
cd frontend
npm install
npm run build
```

## Deployment Failures

### Symptom

App deploys but OCR fails.

### Likely Cause

Tesseract was not installed in the runtime image.

### Fix

Use the included root `Dockerfile`, which contains:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr
```

## Environment Issues

### Frontend Cannot Reach Backend

In dev mode, Vite proxies `/api` to `http://localhost:8000`.

Make sure backend is running:

```bash
curl http://localhost:8000/api/health
```

In production mode, run after building frontend:

```bash
cd frontend
npm run build
cd ..
PYTHONPATH=backend uv run --with fastapi --with uvicorn --with pydantic --with pillow --with pytesseract --with python-multipart python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Build Issues

### TypeScript/Vite Build

```bash
cd frontend
npm run build
```

If packages are missing:

```bash
npm install
```

### Backend Tests

```bash
PYTHONPATH=backend uv run --with pytest --with fastapi --with pydantic --with pillow --with pytesseract --with rapidfuzz --with httpx --with python-multipart python -m pytest backend/tests -q
```

## Verification Issues

### ABV Mismatch Not Detected

Check that both application and label use parseable values such as:

- `45% Alc./Vol.`
- `45% ABV`
- `90 Proof`

### Government Warning False Failure

The validator is intentionally strict about required wording and all-caps `GOVERNMENT WARNING:`. OCR noise can cause REVIEW or FAIL. Use clearer images for demo.

### Brand/Class False Mismatch

The engine normalizes case, punctuation, apostrophes, and whitespace. Borderline fuzzy matches return REVIEW to preserve human judgment.
