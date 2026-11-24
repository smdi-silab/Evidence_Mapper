# ADR 0001: Core tech stack

- **Status:** Accepted
- **Date:** <!-- YYYY-MM-DD -->

## Context
We need a stack the team knows well, that Claude Code works effectively with, and that deploys cleanly to AWS.

## Decision
- Backend: Python 3.12 + FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2
- Database: PostgreSQL
- Frontend: React + TypeScript, built with Vite
- Infrastructure as code: AWS CDK in Python
- Local development: Docker Compose
- Python dependency management: uv

## Consequences
- One language (Python) for backend and infrastructure code.
- The backend runs as a container, so local and AWS environments behave the same way.
- TypeScript adds a little setup but catches frontend bugs early.

## Alternatives considered
- Terraform instead of CDK: more widely used, but a separate language; CDK keeps infra in Python.
- Plain JavaScript frontend: less setup, weaker safety.
