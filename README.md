# Regulatory Evidence Mapper

An AI-assisted accelerator, built on spec for the Synectics Innovation Lab (SiLab), for people who review public comments in federal regulatory rulemaking. It extracts the claims and policy recommendations in public comments, groups equivalent ones across submissions, links each to the evidence its commenter supplied, and proposes relationships such as conflicts and qualifications. Everything stays traceable to the original passage. It does not judge whether comments are true. The same approach could serve state and local public consultations.

**Current phase:** feasibility spike. This is a small, reproducible pipeline tested against team-created annotations on one completed EPA docket, ending in a go, narrow, or stop decision. See the [SiLab spec](specs/Regulatory_Evidence_Mapper_SiLab_Spec.md) and the [decision register](docs/decision-register.md).

## Development process
This project uses spec-driven development. See [`specs/README.md`](specs/README.md) for the workflow and [`CLAUDE.md`](CLAUDE.md) for project conventions.

## Stack
Spike: a Python 3.12 CLI pipeline (uv, Pydantic, pytest) using open-weight models on AWS Bedrock or local hardware. After the gate (provisional): FastAPI + PostgreSQL backend and a web UI, deployed to AWS with Terraform. See [`docs/architecture.md`](docs/architecture.md) and the ADRs in [`docs/decisions/`](docs/decisions/).

## Getting started
The spike pipeline is a Python CLI package in [`pipeline/`](pipeline/).

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/). It downloads Python 3.12 for you if needed.
2. Install the package and its dependencies:
   ```bash
   cd pipeline
   uv sync
   ```
3. Check that it runs:
   ```bash
   uv run evidence-mapper --help
   uv run evidence-mapper --version
   ```
4. Set the environment variables listed in [`pipeline/.env.example`](pipeline/.env.example). The pipeline reads settings only from the environment. For local use, copy the example to `pipeline/.env` (gitignored), fill it in, and pass it to `uv`:
   ```bash
   cp .env.example .env    # then edit .env; never commit it
   uv run --env-file .env evidence-mapper config check
   ```
   `config check` lists each setting as set or not set and exits with an error if a required one is missing. It never prints secret values.
5. Run the tests and checks:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run ruff format --check .
   ```

Spike data lives in [`data/`](data/README.md). Everything there except the manifests is gitignored. The default data location assumes the editable install that `uv sync` creates; set `EVIDENCE_MAPPER_DATA_DIR` if you install the package another way.
