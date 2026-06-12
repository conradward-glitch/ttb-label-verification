# Treasury / TTB AI-Powered Alcohol Label Verification — Project Plan

Status: Planning package only. No application code has been generated yet.

## Objective

Build the smallest impressive take-home prototype that helps TTB label compliance agents compare alcohol label artwork against application data and quickly classify each submission as PASS, FAIL, or REVIEW.

The project should optimize for:

- Working software
- Clean UX
- Clear documentation
- Fast evaluator review experience
- Practical engineering judgment

The project should not optimize for:

- Enterprise architecture
- Microservices
- Complex cloud infrastructure
- Full federal production compliance
- Direct COLA system integration

## Evaluation North Star

A reviewer should be able to open the repository, understand the problem in under 10 minutes, run the app locally, upload a sample label, enter expected application values, and see clear verification results.

## Stakeholder Analysis

### Sarah Chen — Deputy Director of Label Compliance

What Sarah actually cares about:

- Reducing routine manual matching work for 47 overburdened agents
- Keeping review time fast enough that agents will actually use the tool
- Simple workflows that work for non-technical staff
- Future potential for batch processing during importer surges
- A prototype that leadership can understand and evaluate

How the solution addresses Sarah's concerns:

- Focuses MVP on high-volume routine checks: brand name, class/type, ABV, net contents, and government warning
- Targets near-immediate feedback for single-label review; the UI should feel faster than manual checking
- Uses a clean one-page workflow: upload label, enter application data, verify, review results
- Includes batch upload as a stretch goal, not an MVP blocker
- Produces pass/fail/review outputs that map directly to compliance workflow

### Marcus Williams — IT Systems Administrator

What Marcus actually cares about:

- Avoiding risky COLA integration for a take-home prototype
- Avoiding cloud/API dependencies that may fail behind government firewalls
- Keeping deployment simple and reviewable
- Not creating security or retention headaches
- Demonstrating realistic awareness of government infrastructure constraints

How the solution addresses Marcus's concerns:

- Builds as standalone proof-of-concept; no COLA integration
- Recommends local OCR with Tesseract rather than external OCR APIs
- Recommends a simple deploy path suitable for review, not federal production
- Avoids persistent storage of uploaded labels in MVP
- Documents production limitations and assumptions clearly

### Dave Morrison — Senior Compliance Agent

What Dave actually cares about:

- The tool must not slow him down or make his job harder
- It must respect human judgment and label-review nuance
- It should avoid false confidence when matches are close but not exact
- It needs obvious buttons and plain-language outputs

How the solution addresses Dave's concerns:

- Uses PASS / FAIL / REVIEW instead of pretending every case is binary
- Applies normalization for obvious case/punctuation differences, such as `STONE'S THROW` vs `Stone's Throw`
- Shows extracted OCR text and matched evidence so agents can verify quickly
- Keeps manual review in the loop for ambiguous matches
- Uses plain explanations: `ABV mismatch: expected 45%, found 40%`

### Jenny Park — Junior Compliance Agent

What Jenny actually cares about:

- Replacing repetitive printed-checklist work with a faster digital tool
- Strong government warning validation
- Handling imperfect label images where possible
- Transparent, modern UX
- Clear output she can trust and explain

How the solution addresses Jenny's concerns:

- Converts the checklist into automated verification cards
- Treats government warning validation as a first-class requirement
- Includes OCR preprocessing as an MVP implementation step
- Documents image quality limitations and review status for unclear OCR
- Adds stretch goals for skew/glare handling after MVP completion

## Requirements Breakdown

### Must Have Requirements

- Upload a label image
- Extract text from the image using OCR
- Allow user to enter expected application data
- Compare label text against expected values
- Verify government warning presence and wording
- Show results dashboard
- Return PASS / FAIL / REVIEW status
- Show clear mismatch reasons
- Include sample labels and test scenarios
- Provide README, approach, handoff, and operational documentation
- Deploy a working prototype accessible to reviewers

### Should Have Requirements

- Normalize matching for capitalization, punctuation, whitespace, and common ABV formats
- Show extracted OCR text for reviewer confidence
- Highlight evidence snippets for matched or failed fields
- Provide image quality / OCR confidence warnings
- Include useful defaults/sample form values
- Keep processing fast for single-label use
- Use local/open-source OCR to avoid blocked network dependencies
- Include structured tests for passing, ABV mismatch, and warning failure scenarios

### Nice To Have Requirements

- Batch upload
- Side-by-side image and result review
- Bounding boxes / text-region highlighting
- Fuzzy matching explanations
- Exportable JSON or CSV result reports
- Deskew / glare / contrast image preprocessing
- Separate beer/wine/spirits rule profiles
- Sample AI-generated labels for demo breadth

## Recommended Technical Stack

### Frontend

Recommendation: React + Vite + TypeScript

Why:

- Fast to scaffold and deploy
- Excellent reviewer experience
- TypeScript keeps form/result structures clean
- Vite produces simple static assets
- Easy to build a polished one-page UX quickly

Alternative considered: plain HTML/JS. Rejected because React/TypeScript improves maintainability and structured state without much overhead.

### Backend

Recommendation: FastAPI + Python

Why:

- Python is the natural fit for OCR and image-processing libraries
- FastAPI provides quick upload endpoints and automatic API docs
- Clean separation between OCR, matching, and API layers
- Easy to test with pytest
- Small enough for a take-home project

Alternative considered: Node/Express. Rejected because OCR/image tooling is stronger and simpler in Python.

### OCR Engine

Recommendation: Tesseract OCR via `pytesseract`, with Pillow/OpenCV preprocessing

Why:

- Runs locally; avoids blocked cloud OCR endpoints
- Free and reviewable
- Good enough for prototype labels with reasonable image quality
- Shows practical awareness of Marcus's network constraints

Alternative considered: Google Vision / Azure AI Vision / AWS Textract. Rejected for MVP because external APIs add credentials, firewall risk, and deployment complexity.

### Matching Engine

Recommendation: Custom deterministic matching engine in Python

Suggested components:

- Exact and normalized text matching
- Regex extraction for ABV, proof, volume, warning statement
- Fuzzy matching only for selected fields such as brand name and class/type
- Strict matching for government warning wording
- Field-level confidence and evidence reporting

Why:

- Transparent and explainable for compliance users
- Easier to test than opaque LLM behavior
- Avoids hallucination risk
- Matches take-home scope

Alternative considered: LLM-based semantic matching. Rejected for MVP because correctness, repeatability, and explainability matter more.

### Deployment Platform

Recommendation: Render, Railway, or Fly.io for the full-stack prototype; Vercel frontend + Render backend if split deploy is easier.

Preferred fastest path: Render web service running FastAPI backend and serving built frontend static files.

Why:

- One deployed URL is easiest for Treasury reviewers
- Avoids complex cloud setup
- Supports Python apps and system packages like Tesseract
- Practical for take-home review

Alternative considered: Azure. Rejected for take-home MVP because it increases setup time without improving evaluation score.

## MVP Scope

The MVP should include only the features necessary to score well.

### 1. Image Upload

- Accept PNG/JPG label image
- Show preview after upload
- Validate file type and size
- Display friendly errors for invalid files

### 2. OCR

- Run OCR on uploaded label
- Apply basic preprocessing: grayscale, contrast, thresholding
- Return extracted text to UI
- If OCR text is too short or unreadable, return REVIEW

### 3. Application Data Entry

Fields:

- Brand name
- Class/type designation
- Alcohol content / ABV
- Net contents
- Bottler/producer name and address
- Country of origin, optional/import-specific
- Beverage type, optional selector

### 4. Label Verification

- Compare application fields against OCR text
- Produce field-by-field result cards
- Include expected value, detected value/evidence, status, and explanation

### 5. Government Warning Verification

Check for required warning text:

`GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.`

MVP should validate:

- Warning exists
- `GOVERNMENT WARNING:` appears in all caps
- Core wording is present and in the correct order
- Missing or materially altered warning returns FAIL
- OCR uncertainty returns REVIEW

Bold detection is not reliable through basic OCR, so MVP should document that it cannot confirm bold styling from OCR alone.

### 6. Results Dashboard

- Overall status: PASS / FAIL / REVIEW
- Field-level cards
- Extracted OCR text panel
- Plain-language summary
- Suggested next action

### 7. Pass / Fail / Review Status

Rules:

- PASS: all required checks pass with sufficient confidence
- FAIL: one or more required checks clearly fail
- REVIEW: OCR uncertainty, ambiguous fuzzy match, or missing evidence that may be image quality related

## Stretch Goals

Only after MVP is complete:

1. Batch upload and queue processing
2. Label image deskewing and glare/contrast enhancement
3. Bounding-box evidence highlighting
4. Beer/wine/spirits rule profiles
5. Export results as CSV/JSON
6. Drag-and-drop multi-file upload
7. Saved sample scenarios for demo mode
8. Basic accessibility audit

## Recommended Repository Structure

```text
/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── ocr.py
│   │   ├── matching.py
│   │   ├── schemas.py
│   │   └── warning.py
│   ├── tests/
│   │   ├── test_matching.py
│   │   ├── test_warning.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── Dockerfile
├── samples/
│   ├── labels/
│   ├── applications/
│   └── README.md
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── ARCHITECTURE.md
│   ├── README-FIRST.md
│   ├── HANDOFF.md
│   ├── TROUBLESHOOTING.md
│   ├── DECISIONS.md
│   └── CHANGELOG.md
├── README.md
├── PROJECT_PLAN.md
├── APPROACH.md
├── CHANGELOG.md
├── HANDOFF.md
├── LICENSE
└── .gitignore
```

## Documentation Strategy

### README.md

Primary evaluator entry point. Include overview, screenshots, architecture diagram, stack, install/run/deploy/test instructions, assumptions, limitations, and future enhancements.

### HANDOFF.md

Short operational handoff for another engineer. Should allow project takeover in under 30 minutes.

### CHANGELOG.md

Track major milestones and feature completion.

### APPROACH.md

Explain stakeholder analysis, design decisions, tradeoffs, technology choices, and alternatives considered.

### docs/README-FIRST.md

First internal engineering document to read. Should link to the most important files and explain current status.

### docs/TROUBLESHOOTING.md

Quick fixes for OCR, dependency, deployment, environment, and build issues.

### docs/DECISIONS.md

Decision log with alternatives and tradeoffs.

## Deployment Strategy

Fastest reliable approach:

1. Build React frontend with Vite
2. Serve static frontend from FastAPI or deploy frontend separately
3. Deploy FastAPI app to Render using a Dockerfile that installs Tesseract
4. Provide one public URL in README
5. Include sample images and prefilled sample data for evaluator speed

Why this deployment strategy:

- One URL minimizes reviewer friction
- Dockerfile controls OCR system dependency
- Render/Railway/Fly are faster than government-style Azure setup
- Easy rollback and redeploy for take-home context

## Testing Strategy

### Unit Tests

- Text normalization
- ABV extraction and comparison
- Net contents extraction
- Brand/class fuzzy matching thresholds
- Government warning validation
- Overall PASS / FAIL / REVIEW status aggregation

### Integration Tests

- API accepts image + form data
- OCR pipeline returns extracted text
- Verification endpoint returns structured results

### Required Test Scenarios

#### Passing Label Test

Input:

- Label contains OLD TOM DISTILLERY
- Application data matches label
- ABV is 45%
- Government warning is complete

Expected:

- Overall status: PASS
- All required fields pass

#### ABV Mismatch Test

Input:

- Application says 45% ABV
- Label says 40% ABV

Expected:

- Overall status: FAIL
- ABV field status: FAIL
- Explanation clearly states mismatch

#### Government Warning Failure Test

Input:

- Warning is missing, incomplete, title case, or altered

Expected:

- Overall status: FAIL or REVIEW depending on OCR confidence
- Warning field explains exact issue

## Risks and Assumptions

### Assumptions

- Prototype does not integrate with COLA
- Prototype does not need authentication
- Uploaded labels do not need long-term storage
- Evaluators will test with reasonable image quality
- Basic OCR is acceptable for MVP demonstration
- Bold styling in warning text cannot be reliably confirmed through OCR alone
- TTB production security requirements are out of scope for take-home MVP
- Cloud deployment is acceptable for prototype evaluation

### Risks

- OCR quality may vary with angled, glossy, or low-resolution labels
- Tesseract may misread small warning text
- Strict warning validation may fail because OCR changes punctuation
- Fuzzy matching may create false positives if thresholds are too permissive
- Deployment may fail if Tesseract is missing from the runtime image
- A split frontend/backend deployment may create CORS issues

### Mitigations

- Add preprocessing and OCR confidence heuristics
- Return REVIEW instead of PASS for ambiguous cases
- Use strict matching for critical warning text but tolerate OCR whitespace noise
- Use Docker for predictable Tesseract installation
- Prefer one-service deployment to avoid CORS

## Evaluation Strategy

### Correctness

Maximize by implementing deterministic checks, explicit field-level results, and required test scenarios.

### Completeness

Maximize by covering the full MVP: upload, OCR, data entry, verification, warning validation, dashboard, and statuses.

### Code Quality

Maximize by separating OCR, matching, schemas, API, and UI components. Keep functions small and tested.

### Technical Choices

Maximize by choosing pragmatic tools: React/Vite/TypeScript, FastAPI/Python, Tesseract, deterministic matching, simple cloud deploy.

### User Experience

Maximize by designing for Sarah's low-friction workflow and Dave's skepticism: obvious buttons, plain language, visual result cards, and no hidden complexity.

### Error Handling

Maximize by gracefully handling invalid files, OCR failures, missing fields, low confidence, and deployment/runtime dependency problems.

### Requirements Compliance

Maximize by explicitly mapping deliverables to assignment requirements in README and APPROACH.

### Creative Problem Solving

Maximize by adding REVIEW status, confidence explanations, field evidence snippets, and future batch-processing pathway without overbuilding.

## Development Roadmap

### Phase 1: Project Setup

- Initialize repository
- Create frontend and backend folders
- Add README, APPROACH, HANDOFF, CHANGELOG, docs
- Add sample data plan
- Add CI/test command placeholders

### Phase 2: OCR Pipeline

- Add upload endpoint
- Add image preprocessing
- Add Tesseract OCR wrapper
- Return OCR text and basic quality signals

### Phase 3: Matching Engine

- Implement normalization
- Implement field matchers
- Implement ABV/net-content extraction
- Implement government warning validator
- Implement overall status aggregation

### Phase 4: User Interface

- Build upload/data-entry form
- Add image preview
- Add verification results dashboard
- Add extracted text panel
- Add sample scenario helpers

### Phase 5: Testing

- Add passing label test
- Add ABV mismatch test
- Add warning failure test
- Add API integration test
- Add frontend smoke test if time permits

### Phase 6: Deployment

- Add Dockerfile or deployment config
- Deploy to Render/Railway/Fly
- Smoke test public URL
- Add deployed URL to README

### Phase 7: Documentation

- Finalize README with screenshots
- Finalize APPROACH and HANDOFF
- Add troubleshooting notes
- Add changelog entries
- Document limitations and stretch goals

## Stop Point

After this planning package is complete, stop and wait for approval before generating application code.
