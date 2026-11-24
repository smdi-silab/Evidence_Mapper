# ADR 0009: Pydantic models as the schema source of truth

- **Status:** Proposed
- **Date:** 2026-11-24
- **Register:** TX-06

## Context
SiLab §7.6 calls for Pydantic/JSON Schema for outputs. Reruns need to be comparable occurrence by occurrence (MI-07, SiLab §6.4 stability).

## Decision
- Pydantic v2 models are the single source of truth for every output schema.
- Versioned JSON Schema files are exported from them.
- Occurrence IDs are deterministic hashes of source ID + span offsets.

## Consequences
- One definition is used for validation (ADR 0005), documentation, and annotation exports.
- The same span gets the same ID across runs, so run-to-run agreement can be computed directly.
- Changing span normalization changes IDs. Normalization must be versioned along with the schema.

## Alternatives considered
- JSON Schema written by hand: duplicates the models and drifts out of sync.
