# Spike data

This layout is for the feasibility spike only ([spec 001](../specs/001-spike-foundation/plan.md)). After the gate, data moves to PostgreSQL and object storage, designed in its own spec.

Everything here is gitignored except this README and `manifests/`. Comment text, attachments, annotations and model outputs are never committed (ADR 0007, ADR 0011).

```
data/
  manifests/                       TRACKED: IDs, hashes, settings; never comment text
    freezes/<freeze-id>.jsonl      one row per document: IDs, SHA-256, selection reason, exclusions
    splits/<split-id>.json         dev/holdout comment IDs and hashes; the holdout lock (AM-06)
    runs/<run-id>.json             model, prompt version, input and output hashes
  raw/<freeze-id>/                 IGNORED: as fetched, never edited
    api/                           raw Regulations.gov JSON
    files/                         downloaded attachments
  extracted/<freeze-id>/           IGNORED: normalized per-page text JSONL
  annotations/                     IGNORED: contains quoted comment spans
    dev/
    holdout/                       never read while developing prompts, thresholds or rubrics (AM-06)
  runs/<run-id>/                   IGNORED: stage outputs as JSONL
```

## Rules
- **Freeze IDs** are `<docket-id>.v<n>`, for example `EPA-HQ-OAR-2021-0317.v1`.
- **Never re-fetch, edit or overwrite** anything under `raw/` or `extracted/`. A correction becomes a new freeze (`.v2`) next to the old one.
- The stage that writes a folder creates it. Only `manifests/` exists in a fresh clone.
- The location can be changed with `EVIDENCE_MAPPER_DATA_DIR`.
