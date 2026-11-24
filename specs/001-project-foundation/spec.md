# Spec 001: Project foundation

- **Status:** Draft
- **Owner:**echo "# Evidence Mapper" > README.md
git add README.md
git commit -m "Test commit"
git push
- **Created:**
- **Branch:** feat/001-project-foundation

## Problem
There's no runnable application yet. Before building features we need a working skeleton of the backend, frontend, and database that runs locally with one command and has tests, linting, and migrations wired up.

## Users and context
Developers working on Evidence Mapper, including Claude Code.

## Goals
- One command starts the full stack locally.
- Backend, frontend, and database are connected end to end.
- Testing, linting, and migrations work from day one.

## Non-goals
- Any Evidence Mapper features.
- Authentication.
- AWS deployment (covered by a later spec).

## Functional requirements
- **FR-1:** A FastAPI backend in `backend/` with a health endpoint at `GET /api/v1/health`.
- **FR-2:** The health endpoint reports whether the database is reachable.
- **FR-3:** Alembic configured with an initial (empty) migration.
- **FR-4:** A React + TypeScript (Vite) frontend in `frontend/` that calls the health endpoint and displays the result.
- **FR-5:** A `docker-compose.yml` that runs Postgres, the backend, and the frontend together.
- **FR-6:** A `.env.example` documenting every environment variable.
- **FR-7:** The Commands section of `CLAUDE.md` and Getting started in `README.md` are filled in.

## Acceptance criteria
- **AC-1:** Given a fresh clone and Docker installed, when I copy `.env.example` to `.env` and run `docker compose up`, then the frontend, backend, and database all start without errors.
- **AC-2:** Given the stack is running, when I call `GET /api/v1/health`, then I get HTTP 200 with `{"status": "ok", "database": "ok"}`.
- **AC-3:** Given the database is stopped, when I call `GET /api/v1/health`, then the response reports the database as unavailable.
- **AC-4:** Given the stack is running, when I open the frontend in a browser, then it shows the backend and database status.
- **AC-5:** `uv run pytest` and `uv run ruff check .` pass in `backend/`; `npm test` passes in `frontend/`.
- **AC-6:** `alembic upgrade head` runs successfully against the local database.

## Non-functional requirements
- No secrets committed; all config from environment variables.

## Open questions
- [x] Is TypeScript for the frontend OK? (Assumed yes.)
- [x] Is `uv` OK for Python dependency management? (Assumed yes.)
