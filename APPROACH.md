# Approach

## Summary

The recommended approach is a small, polished, standalone web prototype that uses OCR plus deterministic matching to verify common alcohol label requirements.

This approach favors working software, clarity, and evaluator speed over enterprise-scale architecture.

## Stakeholder Analysis

### Sarah Chen

Sarah needs faster routine review without creating another tool agents avoid. The solution focuses on fast single-label verification, clear results, and future batch-processing potential.

### Marcus Williams

Marcus needs a prototype that avoids COLA integration, avoids fragile cloud API dependencies, and does not create security headaches. The solution is standalone, local-OCR based, and does not persist uploads.

### Dave Morrison

Dave needs the tool to respect human judgment. The solution uses PASS / FAIL / REVIEW and shows evidence instead of hiding decisions.

### Jenny Park

Jenny wants the repetitive checklist automated, especially government warning checks. The solution turns the checklist into field-level verification cards and treats warning validation as a first-class feature.

## Design Decisions

- Standalone prototype, no COLA integration
- React/Vite/TypeScript frontend
- FastAPI/Python backend
- Tesseract local OCR
- Deterministic matching engine
- PASS / FAIL / REVIEW status model
- Batch processing reserved for stretch goal

## Tradeoffs

### Accuracy vs Simplicity

Tesseract is not perfect, but it is local, free, and deployable. The MVP should return REVIEW when OCR is uncertain rather than overclaim accuracy.

### Strictness vs Usability

Government warning validation should be strict. Brand names and class/type can tolerate case and punctuation differences.

### Scope vs Polish

Batch upload and advanced image correction are valuable but should wait until the single-label workflow is reliable and polished.

## Why These Technologies Were Selected

### React + Vite + TypeScript

Selected for fast UI development, good developer experience, and clean typed state.

### FastAPI + Python

Selected because Python has strong OCR/image tooling and FastAPI is simple to test and deploy.

### Tesseract OCR

Selected to avoid network-blocked OCR APIs and keep the prototype self-contained.

### Deterministic Matching

Selected because compliance workflows need explainable, testable results.

## Alternative Approaches Considered

### Cloud OCR APIs

Rejected for MVP due to credentials, firewall risk, and deployment complexity.

### LLM-Based Validation

Rejected for MVP because deterministic compliance checks are easier to test and explain.

### Streamlit-Only App

Considered for speed, but rejected because a React/FastAPI app better demonstrates full-stack engineering and can provide a more polished reviewer experience.

### Azure Deployment

Rejected for take-home MVP because it adds complexity without improving review outcome.
