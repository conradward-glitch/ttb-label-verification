# Architecture

## High-Level Architecture

```text
User Browser
   |
   | upload image + application fields
   v
React/Vite Frontend
   |
   | HTTP multipart/form-data or JSON API request
   v
FastAPI Backend
   |
   +--> OCR Pipeline
   |      - image validation
   |      - preprocessing
   |      - Tesseract OCR
   |      - extracted text
   |
   +--> Matching Engine
   |      - normalization
   |      - brand/class matching
   |      - ABV/net contents extraction
   |      - government warning validation
   |      - status aggregation
   |
   v
Verification Result JSON
   |
   v
Results Dashboard
```

## Frontend Responsibilities

- Label image upload
- Image preview
- Application data form
- Submit verification request
- Display field-level results
- Display extracted OCR text
- Display overall PASS / FAIL / REVIEW status
- Show friendly error messages

## Backend Responsibilities

- Accept uploads
- Validate files
- Run OCR
- Normalize extracted text
- Compare application fields against OCR text
- Validate government warning text
- Return structured results

## OCR Pipeline

Recommended steps:

1. Read uploaded image
2. Convert to grayscale
3. Increase contrast
4. Apply thresholding if useful
5. Run Tesseract OCR
6. Return extracted text and basic quality signals

## Matching Engine

The matching engine should be deterministic and explainable.

Field strategy:

- Brand name: normalized and optionally fuzzy match
- Class/type: normalized and optionally fuzzy match
- ABV: regex extraction and numeric comparison
- Net contents: regex extraction and unit normalization
- Bottler/producer: normalized text match
- Country of origin: optional/import-specific match
- Government warning: strict phrase validation with OCR whitespace tolerance

## Status Model

- PASS: field is confidently verified
- FAIL: field clearly mismatches or required warning is invalid/missing
- REVIEW: OCR or matching confidence is too low for a safe automated result

Overall status:

- FAIL if any required field fails
- REVIEW if no required field fails but one or more fields require review
- PASS if all required fields pass

## Deployment Architecture

Preferred take-home deployment:

```text
Render / Railway / Fly.io
   |
   +--> FastAPI app
          |
          +--> serves API
          +--> optionally serves built frontend static files
          +--> includes Tesseract in Docker image
```

This keeps the review URL simple and reduces CORS/deployment complexity.

## Data Storage

MVP should avoid persistent storage.

- Uploaded images processed in-memory or temporary files
- Results returned immediately
- No long-term label retention
- No authentication for prototype

## Security Scope

Prototype security should be sensible but not overbuilt.

- Validate supported upload file types
- Do not store uploaded documents long-term
- Do not require real applicant PII
- Do not integrate with COLA
- Document production gaps clearly
