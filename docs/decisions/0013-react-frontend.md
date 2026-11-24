# ADR 0013: React frontend for the post-gate application

- **Status:** Accepted
- **Date:** 2026-11-24

## Context
After a "go" at the feasibility gate, the application needs a review UI: the source-linked issue matrix and the contextual graph drill-down (SiLab spec §5). SiLab §4.8 proposes Streamlit, possibly embedding Cytoscape.js. §9.8 asks whether Cytoscape.js inside Streamlit can reliably support node and edge inspection, or whether a small React app would be simpler. ADR 0001 had chosen React + TypeScript.

## Decision
The post-gate frontend is **React + TypeScript, built with Vite and tested with Vitest**, as in ADR 0001. This resolves SiLab §9.8 and amends the Streamlit proposal in §4.8. A graph library such as Cytoscape.js may still be used inside the React app for the drill-down.

## Consequences
- Full control over the interactions in §5.2 (selecting, filtering, expanding, comparing, and jumping to the source passage) without working around Streamlit's rerun model.
- The UI calls the FastAPI backend through a dedicated API client module (CLAUDE.md conventions).
- More setup than Streamlit, and a second language (TypeScript) in the repo.
- Still deferred until after the gate (ADR 0002).

## Alternatives considered
- Streamlit with embedded Cytoscape.js (SiLab §4.8): fastest to start, but interactive node and edge inspection through embedded components is the risk §9.8 raises.
