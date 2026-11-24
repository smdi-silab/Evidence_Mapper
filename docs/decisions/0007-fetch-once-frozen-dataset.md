# ADR 0007: Fetch once and freeze the dataset

- **Status:** Proposed
- **Date:** 2026-11-24
- **Register:** DS-04, DS-05

## Context
Spike results must be reproducible against frozen inputs (SiLab §7.4 item 4, §7.9 item 1). Regulations.gov records can change, and the API has rate limits. Text-extractable PDF attachments are in scope; scanned PDFs needing OCR are not (D-02, SiLab §3.2).

## Decision
- **Fetch once.** Store the raw API JSON and the downloaded files, each with a SHA-256 hash. Never re-fetch during the spike.
- **Manifest.** A manifest lists IDs, hashes, selection reasons, and exclusions.
- **Extraction.** Use PyMuPDF for PDF text. Pages with no text layer are detected and excluded. The extractor name and version are recorded.
- **Locators.** A locator is document ID + page + character offset within that page's normalized text.

## Consequences
- Every result can be traced to exact, hashed inputs.
- Quoted spans can be checked by exact match against frozen normalized text (AM-09).
- If a fetch was incomplete, the fix is a new, versioned freeze, not a quiet re-fetch.
- Whether attachment copies may be kept and shown is still open (DS-07).

## Alternatives considered
- Fetching live during experiments: not reproducible, and exposed to rate limits.
- pdfplumber, pdftotext: viable alternatives. PyMuPDF was preferred for its per-page text and speed.
