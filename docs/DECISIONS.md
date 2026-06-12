# Decision Log

## Decision 1: Build a standalone prototype instead of COLA integration

Decision made:

- Do not integrate with COLA in the take-home MVP.

Alternatives considered:

- Direct COLA integration
- Mock COLA API
- Standalone upload/form workflow

Why selected:

- Assignment context says COLA integration is not expected
- Standalone workflow is easier for reviewers to run
- Avoids federal authorization and integration complexity

Tradeoffs:

- Less realistic production integration
- Much faster and safer for take-home evaluation

## Decision 2: Use local OCR with Tesseract

Decision made:

- Use Tesseract OCR through Python.

Alternatives considered:

- Azure AI Vision
- Google Vision API
- AWS Textract
- LLM vision model

Why selected:

- Avoids blocked outbound network/API issues
- No credentials required
- Fits prototype deployment
- Transparent and reproducible

Tradeoffs:

- Less accurate than some commercial OCR services
- Requires system dependency in deployment image

## Decision 3: Use deterministic matching instead of LLM judgment

Decision made:

- Implement matching with normalization, regex, and conservative fuzzy matching.

Alternatives considered:

- LLM-based semantic validation
- Pure exact string matching

Why selected:

- Compliance workflows need explainability
- Tests can verify deterministic behavior
- Avoids hallucination and unpredictable outputs

Tradeoffs:

- Less flexible for unusual labels
- Requires careful handling of OCR noise

## Decision 4: Use PASS / FAIL / REVIEW status model

Decision made:

- Add REVIEW as a first-class result.

Alternatives considered:

- Binary pass/fail only
- Numeric confidence only

Why selected:

- Matches real compliance workflow
- Respects Dave's concern about nuance
- Avoids false certainty when OCR is unclear

Tradeoffs:

- Requires clear explanation of when REVIEW is used

## Decision 5: Use React/Vite/TypeScript frontend

Decision made:

- Build frontend with React, Vite, and TypeScript.

Alternatives considered:

- Plain HTML/JS
- Next.js
- Streamlit

Why selected:

- Fast, polished, reviewer-friendly UI
- Strong state management for upload/form/results
- Lower deployment complexity than Next.js

Tradeoffs:

- More setup than plain HTML
- Requires Node build step

## Decision 6: Use FastAPI backend

Decision made:

- Build backend with FastAPI and Python.

Alternatives considered:

- Flask
- Node/Express
- Serverless functions

Why selected:

- Python has strongest OCR/image tooling
- FastAPI is clean, typed, and fast to document
- Easy pytest testing

Tradeoffs:

- Requires Python deployment environment

## Decision 7: Keep batch upload as stretch goal

Decision made:

- Do not include batch upload in MVP unless core features are complete.

Alternatives considered:

- Batch-first design
- No batch mention

Why selected:

- Sarah values batch processing, but MVP correctness matters more
- Architecture can leave room for batch later

Tradeoffs:

- Peak-season workflow not fully solved in MVP
