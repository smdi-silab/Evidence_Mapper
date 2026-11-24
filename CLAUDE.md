# Evidence Mapper: Instructions for Claude

## Project
Evidence Mapper is <!-- TODO: one-paragraph description of what the app does and who it's for -->.

## Stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic (migrations), Pydantic v2, pytest. Dependency management with `uv`. Lint/format with `ruff`.
- **Database:** PostgreSQL 16. Docker locally; Amazon RDS in AWS.
- **Frontend:** React + TypeScript (strict), built with Vite, tested with Vitest.
- **Infrastructure:** AWS CDK (Python) in `infra/`.
- **Local dev:** Docker Compose (`docker-compose.yml` at the repo root).

## Repo layout
```
CLAUDE.md            this file
specs/               one folder per feature: spec.md, plan.md, tasks.md
  _templates/        templates for new specs
docs/
  architecture.md    current system architecture (keep up to date)
  decisions/         Architecture Decision Records (ADRs)
backend/             FastAPI app, Alembic migrations, backend tests
frontend/            React app and frontend tests
infra/               AWS CDK app
```

## How we work: spec-driven development
1. **No code without a spec.** Every feature lives in `specs/NNN-short-name/` with `spec.md`, `plan.md`, and `tasks.md`, created from `specs/_templates/`.
2. **Read before you write.** Before changing code, read the relevant `spec.md` and `plan.md`. If a request isn't covered by a spec, say so and offer to draft or update the spec first.
3. **`spec.md` is the what and why, and the human owns it.** Do not change requirements or acceptance criteria without asking. Propose changes instead.
4. **`plan.md` is the how.** Draft it from the spec, then stop and wait for approval before implementing.
5. **`tasks.md` is the checklist.** Work through tasks in order, one at a time. Mark each `[x]` when done. Commit after each task or small logical group.
6. **If reality disagrees with the docs, stop.** When implementation shows the spec or plan is wrong or incomplete, flag it and agree on a change before continuing, then update the docs.
7. **Record significant decisions** as ADRs in `docs/decisions/` (copy `_template.md`, next number).
8. **Test the acceptance criteria.** Every acceptance criterion (AC-n) gets at least one test, and the test name or docstring references the AC ID.

## Git
- Work on a branch per spec: `feat/NNN-short-name`. Don't commit directly to `main`.
- Small commits with clear messages, e.g. `feat(001): add health check endpoint`.
- Ask before pushing, merging, or rewriting history.
- Never commit secrets, credentials, or `.env` files.

## AWS safety rules
- The developer is new to AWS. When introducing an AWS service or concept for the first time, explain briefly what it is and why it's needed.
- **Never run commands that create, change, or delete AWS resources without explicit approval in the current session.** This includes `cdk deploy`, `cdk destroy`, `cdk bootstrap`, and any `aws` command that creates, updates, puts, or deletes.
- Read-only commands are fine: `cdk synth`, `cdk diff`, `aws ... describe/list/get`, `aws sts get-caller-identity`.
- Always show `cdk diff` output and summarize it before proposing a deploy.
- Never hardcode credentials. Use the AWS profile in `AWS_PROFILE`. App secrets go in AWS Secrets Manager.
- Prefer the smallest, cheapest resource sizes in dev, and point out anything that costs money while idle.

## Conventions
- **Python:** type hints everywhere; `ruff` clean; FastAPI routers grouped by domain under `backend/app/api/`; API routes versioned under `/api/v1`.
- **Database:** schema changes only through Alembic migrations, never by hand.
- **Frontend:** function components and hooks; API calls in a dedicated client module, not scattered through components.
- **Config:** settings from environment variables (Pydantic Settings); `.env.example` documents every variable.

## Commands
<!-- Fill these in once spec 001 is implemented. -->
- Start everything locally: `docker compose up`
- Backend tests: `cd backend && uv run pytest`
- Backend lint: `cd backend && uv run ruff check .`
- Frontend tests: `cd frontend && npm test`
- Infra synth: `cd infra && cdk synth`
