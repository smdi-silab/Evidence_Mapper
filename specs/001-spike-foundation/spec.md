# Spec 001: Spike foundation

- **Status:** Draft
- **Owner:** Tony Lizza
- **Created:** 2026-11-24
- **Branch:** feat/001-spike-foundation

## Problem
There's no runnable code yet. Before writing any pipeline stage (docket shortlist, fetch and freeze, extraction), the feasibility spike needs a reproducible Python package skeleton. It needs tests, linting, configuration, and the data-handling guardrails in place from the first line of code ([ADR 0002](../../docs/decisions/0002-feasibility-spike-first.md), SiLab spec §10).

## Users and context
Developers working on the spike, including Claude Code. Later specs build each pipeline stage on top of this skeleton.

## Goals
- A Python CLI package that installs and runs with one command.
- One module per pipeline stage reserved from the start, so failures can be traced to a stage.
- Configuration and secrets come only from the environment.
- Raw data can't be committed by accident; manifests can be.
- Testing and linting work from day one.

## Non-goals
- Any pipeline logic: docket shortlist (planned spec 002), fetch and freeze (planned spec 003), extraction, and later stages.
- Any model calls, Bedrock setup, or AWS resources.
- The post-gate web stack: FastAPI, PostgreSQL, Alembic, frontend, Docker Compose (deferred by ADR 0002).

## Functional requirements
- **FR-1:** A Python 3.12 package in `pipeline/`, managed with `uv` (`pyproject.toml` and a committed `uv.lock`) (MI-08, ADR 0006).
- **FR-2:** A CLI entry point named `evidence-mapper` that supports `--help` and `--version`.
- **FR-3:** Separate, empty modules reserved for: acquisition, extraction, canonicalization, retrieval, classification, evaluation (SiLab §10).
- **FR-4:** Settings loaded from environment variables with Pydantic Settings. These include the Regulations.gov (api.data.gov) API key (DS-06, SP-04), the AWS profile, and the data directory. Settings load without error when a setting is missing; a missing setting causes an error only when a command needs it. The data directory defaults to `data/` at the repository root, wherever the command is run from.
- **FR-5:** A `pipeline/.env.example` documenting every environment variable the settings read, with placeholder values only.
- **FR-6:** A `data/` layout in which raw and extracted data are gitignored and manifests are tracked (ADR 0006, ADR 0007). The layout is for the spike only; post-gate storage will be designed in its own spec.
- **FR-7:** `pytest` and `ruff` configured for the package.
- **FR-8:** The Commands section of `CLAUDE.md` and Getting started in `README.md` are filled in.
- **FR-9:** An `evidence-mapper config check` command that lists each setting as set or not set. It shows values only for settings that aren't secret, and exits with an error naming any missing setting that the pipeline requires.

## Acceptance criteria
- **AC-1:** Given a fresh clone with `uv` installed, when I run `uv sync` and then `uv run evidence-mapper --help` in `pipeline/`, then the help text is shown and the command exits with status 0.
- **AC-2:** `uv run evidence-mapper --version` prints the package version.
- **AC-3:** `uv run pytest`, `uv run ruff check .` and `uv run ruff format --check .` pass in `pipeline/`.
- **AC-4:** Given the API key is not set, when `evidence-mapper config check` runs, then it exits with a non-zero status and a message naming the missing variable. Given the API key is set, then its value doesn't appear in the command's output or logs.
- **AC-5:** Every setting the package reads is listed in `.env.example`, and the test suite checks this.
- **AC-6:** `git check-ignore` reports files under the raw and extracted data directories as ignored, and files under the manifests directory as not ignored.

## Non-functional requirements
- No secrets committed; all config from environment variables.
- Logging follows SP-01: no comment text in logs. The skeleton only needs a logging setup that follows this rule.

## Open questions
- [x] Which CLI framework? Typer (see plan.md).
- [x] Exact `data/` subdirectory names? See plan.md. They apply to the spike only.
- [x] ADR 0006 and ADR 0007 are still Proposed (MI-08 and DS-05 are Recommended). This spec goes ahead on those recommendations; the ADRs stay Proposed until the register entries are marked Decided.
- [x] Spike first instead of the web skeleton? Yes (ADR 0002, decided 2026-11-24).
- [x] Python 3.12 vs. MI-08's "3.11+"? 3.12 meets both.
