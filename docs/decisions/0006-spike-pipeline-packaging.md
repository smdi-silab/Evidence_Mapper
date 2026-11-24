# ADR 0006: Spike pipeline as a Python CLI package with JSONL artifacts

- **Status:** Proposed
- **Date:** 2026-11-24
- **Register:** MI-08

## Context
SiLab §7.6 allows notebooks, scripts, or a CLI, with versioned JSONL input and output. §10 asks for separate modules for extraction, canonicalization, candidate retrieval, classification, and evaluation, so failures can be traced to one stage.

## Decision
- The spike is a Python 3.12 CLI package in `pipeline/`, managed with `uv` and tested with `pytest`. (MI-08 says 3.11+; 3.12 matches ADR 0001.)
- Each pipeline stage is its own module.
- Stages read and write versioned JSONL files.
- Use a hashed manifest committed to git instead of DVC, a data versioning tool. Raw data itself is never committed (ADR 0007).

## Consequences
- Runs are repeatable from the command line and easy to test, without notebook state.
- There are no extra data-versioning tools to learn during a 1–2 week spike.
- The package can later become the processing jobs behind the post-gate app (SiLab §4.8).
- A JSONL manifest in git doesn't scale far beyond spike-sized data. Revisit after the gate.

## Alternatives considered
- Notebooks: hard to test and to rerun reproducibly.
- DVC: more tooling than the spike needs.
