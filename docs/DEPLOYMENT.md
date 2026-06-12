# Deployment Guide — Render

This project is designed to deploy as one Docker-backed Render web service.

## What Render Runs

- FastAPI backend on port `8000`
- Built React frontend served by FastAPI from `/`
- API endpoints under `/api/*`
- Health check at `/api/health`
- Tesseract OCR installed inside the Docker image

## Prerequisites

1. A GitHub repository containing the clean project folder contents.
2. Render account access.
3. No separate database, storage bucket, or external OCR service is required for the MVP.

## Repository Shape Expected by Render

The repository root should contain:

```text
backend/
frontend/
samples/
docs/
Dockerfile
render.yaml
README.md
PROJECT_PLAN.md
APPROACH.md
CHANGELOG.md
HANDOFF.md
LICENSE
READY_FOR_GITHUB.md
```

## Option A — Deploy with render.yaml

1. Push the repository to GitHub.
2. In Render, choose `New` -> `Blueprint`.
3. Connect the GitHub repository.
4. Select the repository branch.
5. Render reads `render.yaml`.
6. Confirm the generated web service:
   - Name: `ttb-label-verification`
   - Environment: Docker
   - Health check path: `/api/health`
7. Create/apply the blueprint.
8. Wait for the Docker build and deploy to complete.
9. Open the public Render URL.
10. Verify:
    - `https://<render-service>.onrender.com/api/health` returns `{"status":"ok"}`
    - `https://<render-service>.onrender.com/` serves the React frontend

## Option B — Manual Render Web Service

1. Push the repository to GitHub.
2. In Render, choose `New` -> `Web Service`.
3. Connect the GitHub repository.
4. Configure:
   - Runtime/Environment: Docker
   - Root directory: repository root
   - Branch: target deployment branch
   - Health check path: `/api/health`
   - Auto-deploy: optional; enabled is fine for MVP review
5. Leave build/start commands empty; Dockerfile controls the image and command.
6. Create the service.
7. Wait for build/deploy completion.
8. Verify `/api/health` and `/` as above.

## Dockerfile Behavior

The Dockerfile uses a multi-stage build:

1. Node stage installs frontend dependencies and runs `npm run build`.
2. Python stage installs system `tesseract-ocr`.
3. Python stage installs backend dependencies from `backend/requirements.txt`.
4. Built frontend files are copied to `/app/frontend/dist`.
5. FastAPI starts with `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

## Local Docker Smoke Test

From the repository root:

```bash
docker build -t ttb-label-verification .
docker run --rm -p 8000:8000 ttb-label-verification
```

In another terminal:

```bash
curl http://localhost:8000/api/health
curl -I http://localhost:8000/
```

Expected:

```text
{"status":"ok"}
HTTP/1.1 200 OK
```

## Sample Verification After Deploy

Use the frontend UI:

1. Open the deployed root URL.
2. Click `Load sample data`.
3. Upload `samples/labels/passing-bourbon-label.png` for the passing bourbon scenario.
4. Paste values from `samples/applications/abv-mismatch.json` and upload the passing label for the ABV mismatch scenario.
5. Use `samples/labels/government-warning-failure-label.png` with the passing bourbon application values for the government warning failure scenario.

## Known Deployment Notes

- Render free services may sleep when inactive; first request after sleep can be slow.
- OCR depends on image quality. Poor scans should return REVIEW rather than overclaiming PASS.
- No persistent storage is required; uploaded files are processed in-memory for the MVP.
- Local WSL runs need `tesseract-ocr` installed unless Docker is used.
