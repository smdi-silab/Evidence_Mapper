# ADR 0001: Core tech stack

- **Status:** Accepted. The web-application parts are deferred until after the feasibility gate by [ADR 0002](0002-feasibility-spike-first.md).
- **Date:** 2026-11-24

## Context
We need a stack the team knows well, that Claude Code works effectively with, and that deploys cleanly to AWS. Per ADR 0003, it must also stay portable to local hosting.

## Decision
Applies now, to the feasibility spike:
- Language: Python 3.12, Pydantic v2
- Python dependency management: uv; lint and format with ruff; tests with pytest
- Infrastructure as code: Terraform (HCL) with the AWS provider, state stored remotely in S3 with state locking

Provisional for the post-gate application (deferred by ADR 0002):
- Backend: FastAPI, SQLAlchemy 2.x, Alembic
- Database: PostgreSQL (optionally pgvector, per SiLab spec §4.8)
- Frontend: React + TypeScript, built with Vite (confirmed over Streamlit by [ADR 0013](0013-react-frontend.md))
- Local development: Docker Compose

## Consequences
- Infrastructure is written in HCL, a second language alongside Python and TypeScript, but Terraform is widely used, well documented, and not tied to a single cloud.
- `terraform plan` gives a readable preview of every change before it is applied.
- Terraform state must be managed carefully: it lives in a remote S3 backend with locking and is never committed.
- The backend runs as a container, so local and AWS environments behave the same way.
- TypeScript adds a little setup but catches frontend bugs early.

## Alternatives considered
- AWS CDK (Python) instead of Terraform: keeps infrastructure in Python, but is AWS-only, synthesizes to CloudFormation (an extra layer to debug), and needs a per-account `cdk bootstrap` step. Originally chosen, then rejected in favor of Terraform.
- Plain JavaScript frontend: less setup, weaker safety.
- Streamlit frontend: proposed in SiLab spec §4.8; rejected in ADR 0013.
