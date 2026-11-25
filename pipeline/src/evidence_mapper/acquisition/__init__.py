"""Pipeline stage: acquisition.

Read public docket data from Regulations.gov. Spec 003 builds the docket shortlist; spec 004
(planned) fetches and freezes the chosen docket (ADR 0007).

Modules:
- `regulations_gov`: read-only API client with throttle, request budget and disk cache.
- `shortlist`: candidate discovery, enrichment and ranking (spec 003).
- `pdf_text`: text-layer check for sampled PDF attachments (spec 003, DS-04).
- `report`: shortlist outputs under `data/manifests/shortlist/` (spec 003).
"""
