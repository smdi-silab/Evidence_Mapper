# ADR 0002: Feasibility spike before the web application

- **Status:** Accepted
- **Date:** 2026-11-24

## Context
The SiLab spec ([`specs/Regulatory_Evidence_Mapper_SiLab_Spec.md`](../../specs/Regulatory_Evidence_Mapper_SiLab_Spec.md)) sets this governing principle: before building an application, show that a small, reproducible analytical pipeline can reliably extract claims and recommendations, keep their sources, find equivalent propositions, and detect relationships (§1, §7.6, §10). The spike ends with a go, narrow, or stop decision (§7.10). Ingestion, persistence, and UI come only after a "go" (§3.1, §8).

The original project scaffolding (ADR 0001, spec 001) instead started with a web-app skeleton: FastAPI, PostgreSQL, React, and Docker Compose.

## Decision
- Build the **Argument Relationship Feasibility Spike** first.
- The spike needs no database, web API, UI, or graph visualization (SiLab §7.6).
- The web-application parts of ADR 0001 are **deferred until after the feasibility gate**: FastAPI, SQLAlchemy, Alembic, PostgreSQL, the frontend, and Docker Compose. They remain the provisional post-gate stack and will be confirmed or revised by the first post-gate spec.
- Spec 001 is retargeted from "project foundation (web skeleton)" to "spike foundation".

## Consequences
- The first code is a Python package for the pipeline (see ADR 0006), not a web app.
- If the gate result is NARROW or STOP, no effort has been spent on a UI or persistence layer.
- `backend/` and `frontend/` won't exist until after the gate. The docs mark them as post-gate.
- The post-gate UI choice is still open: React (ADR 0001) or Streamlit (SiLab §4.8, §9.8).

## Alternatives considered
- Web skeleton first (the original spec 001): rejected. It builds infrastructure the gate might make unnecessary and goes against SiLab §10.
