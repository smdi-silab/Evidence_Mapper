# Regulatory Evidence Mapper

An AI-assisted accelerator, built on spec for the Synectics Innovation Lab (SiLab), for people who review public comments in federal regulatory rulemaking. It extracts the claims and policy recommendations in public comments, groups equivalent ones across submissions, links each to the evidence its commenter supplied, and proposes relationships such as conflicts and qualifications. Everything stays traceable to the original passage. It does not judge whether comments are true. The same approach could serve state and local public consultations.

**Current phase:** feasibility spike. This is a small, reproducible pipeline tested against team-created annotations on one completed EPA docket, ending in a go, narrow, or stop decision. See the [SiLab spec](specs/Regulatory_Evidence_Mapper_SiLab_Spec.md) and the [decision register](docs/decision-register.md).

## Development process
This project uses spec-driven development. See [`specs/README.md`](specs/README.md) for the workflow and [`CLAUDE.md`](CLAUDE.md) for project conventions.

## Stack
Spike: a Python 3.12 CLI pipeline (uv, Pydantic, pytest) using open-weight models on AWS Bedrock or local hardware. After the gate (provisional): FastAPI + PostgreSQL backend and a web UI, deployed to AWS with Terraform. See [`docs/architecture.md`](docs/architecture.md) and the ADRs in [`docs/decisions/`](docs/decisions/).

## Getting started
<!-- Filled in by spec 001 (spike foundation). -->
