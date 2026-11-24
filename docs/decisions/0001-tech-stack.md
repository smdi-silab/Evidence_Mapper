# ADR 0001: Core tech stack

- **Status:** Accepted
- **Date:** <!-- YYYY-MM-DD -->

## Context
We need a stack the team knows well, that Claude Code works effectively with, and that deploys cleanly to AWS.

## Decision
- Backend: Python 3.12 + FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2
- Database: PostgreSQL
- Frontend: React + TypeScript, built with Vite
- Infrastructure as code: Terraform (HCL) with the AWS provider, state stored remotely in S3 with state locking
- Local development: Docker Compose
- Python dependency management: uv

## Consequences
- Infrastructure is written in HCL, a second language alongside Python and TypeScript, but Terraform is widely used, well documented, and not tied to a single cloud.
- `terraform plan` gives a readable preview of every change before it is applied.
- Terraform state must be managed carefully: it lives in a remote S3 backend with locking and is never committed.
- The backend runs as a container, so local and AWS environments behave the same way.
- TypeScript adds a little setup but catches frontend bugs early.

## Alternatives considered
- AWS CDK (Python) instead of Terraform: keeps infrastructure in Python, but is AWS-only, synthesizes to CloudFormation (an extra layer to debug), and needs a per-account `cdk bootstrap` step. Originally chosen, then rejected in favor of Terraform.
- Plain JavaScript frontend: less setup, weaker safety.
