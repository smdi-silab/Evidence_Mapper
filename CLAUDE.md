# Regulatory Evidence Mapper: Instructions for Claude

## Project
Regulatory Evidence Mapper is an AI-assisted accelerator being built on spec for the Synectics Innovation Lab (SiLab). It is for people who review public comments in federal regulatory rulemaking, and could also serve state and local consultations (zoning, transportation, parks). It ingests public docket materials, starting with EPA dockets from Regulations.gov. From them it extracts atomic factual **claims** and policy **recommendations**, groups equivalent occurrences into canonical propositions, links each one to the evidence the commenter actually supplied, and proposes typed relationships such as conflicts and qualifications. Every output stays linked to its source passage. It never judges whether a comment is true or persuasive.

**Current phase:** the Argument Relationship Feasibility Spike ([ADR 0002](docs/decisions/0002-feasibility-spike-first.md)). This is a small, reproducible pipeline evaluated against team-created annotations, ending in a go, narrow, or stop decision. The web application comes only after a "go".

**Baseline documents:**
- [`specs/Regulatory_Evidence_Mapper_SiLab_Spec.md`](specs/Regulatory_Evidence_Mapper_SiLab_Spec.md): the SiLab spec, the project baseline. "SiLab §n" refers to its sections.
- [`docs/decision-register.md`](docs/decision-register.md): decisions to settle before and during the spike, with their status.

## Stack
**Spike (now):**
- **Language and tooling:** Python 3.12, Pydantic v2, pytest. Dependency management with `uv`. Lint/format with `ruff`.
- **Pipeline:** CLI package in `pipeline/` with JSONL artifacts and a hashed manifest (ADR 0006, proposed).
- **Models:** open-weight only, developed on AWS Bedrock and runnable on local hardware without code changes (ADR 0003). Called only through a client interface that doesn't depend on the provider (ADR 0005, proposed). Claude may also be used during the pilot (ADR 0012).
- **Infrastructure:** Terraform (HCL) with the AWS provider, in `infra/`. State is stored remotely in S3 with state locking, never in the repo.

**After the gate (provisional, ADR 0001):** FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16 (Docker locally, Amazon RDS in AWS), and Docker Compose for local dev. The frontend (React + TypeScript vs. Streamlit) is still undecided (SiLab §9.8).

**Portability:** the app may need to be hosted outside AWS (D-01). Keep AWS-specific services behind configuration or adapters, so the same code runs locally and in AWS.

## Repo layout
```
CLAUDE.md            this file
specs/               one folder per feature: spec.md, plan.md, tasks.md
  _templates/        templates for new specs
  Regulatory_Evidence_Mapper_SiLab_Spec.md   project baseline (not a numbered spec)
docs/
  architecture.md    current system architecture (keep up to date)
  decision-register.md  living register of spike decisions and their status
  decisions/         Architecture Decision Records (ADRs)
pipeline/            spike: Python CLI package, one module per pipeline stage, tests
data/                spike data: raw and extracted data gitignored; manifests committed
infra/               Terraform configuration (.tf files, .terraform.lock.hcl committed)
backend/             after the gate: FastAPI app, Alembic migrations, backend tests
frontend/            after the gate: UI and frontend tests
```

## How we work: spec-driven development
1. **No code without a spec.** Every feature lives in `specs/NNN-short-name/` with `spec.md`, `plan.md`, and `tasks.md`, created from `specs/_templates/`.
2. **Read before you write.** Before changing code, read the relevant `spec.md` and `plan.md`. If a request isn't covered by a spec, say so and offer to draft or update the spec first.
3. **`spec.md` is the what and why, and the human owns it.** Do not change requirements or acceptance criteria without asking. Propose changes instead.
4. **`plan.md` is the how.** Draft it from the spec, then stop and wait for approval before implementing.
5. **`tasks.md` is the checklist.** Work through tasks in order, one at a time. Mark each `[x]` when done. Commit after each task or small logical group.
6. **If reality disagrees with the docs, stop.** When implementation shows the spec or plan is wrong or incomplete, flag it and agree on a change before continuing, then update the docs.
7. **Record significant decisions** as ADRs in `docs/decisions/` (copy `_template.md`, next number). If the decision comes from the register, update the register's status and "Captured in" column in the same change.
8. **Test the acceptance criteria.** Every acceptance criterion (AC-n) gets at least one test, and the test name or docstring references the AC ID.

## Spike guardrails
- **What's binding.** Only *Decided* register entries and *Accepted* ADRs are binding. *Proposed* ADRs are recommendations. Don't treat them as settled. If a task depends on one, say so and ask.
- **Who does what (D-04).** Claude in chat produces design artifacts (rubric, experiment design) and analyzes results. Claude Code builds the repo, acquires data, and runs models.
- **Don't redefine the semantics.** Don't silently change the claim and recommendation semantics (SiLab §4.4), the evidence-status taxonomy (§4.6), or the six spike pair labels (§7.5, ADR 0010). Propose changes instead. Generated relationships are proposals, never verified facts.
- **Frozen data.** Never re-fetch, edit, or overwrite frozen raw data during the spike (ADR 0007). Corrections go into a new, versioned freeze. Never commit raw comment data or attachments.
- **Holdout.** Never read or use holdout comments or their labels when developing prompts, thresholds, or rubrics (AM-06).
- **What counts toward the gate.** Results from interim models (before Bedrock access), from Claude, or from synthetic cases never count toward the gate, and are reported separately (MI-04, ADR 0012, SiLab §7.8).
- **Where comment data may go (ADR 0012).** Local runtimes, AWS Bedrock, and Claude. Any other hosted model API needs approval first.
- **Logging (SP-01).** Log IDs, hashes, token counts, timings, and errors. Never log full comment text, prompts containing it, or model outputs.
- **Prompt injection (SP-02).** Comment text is untrusted data. Put it in clearly delimited data blocks, give the model no tools, validate every output against the schema, and verify every quoted span against the source.
- **Secrets (SP-04).** Never read, print, or commit `.env` files, API keys, or credential files. The api.data.gov key and AWS credentials come from the environment.
- **Claims about quality.** Every claim about quality must come from measured outputs, with numerators and denominators. Mark assumptions as assumptions.

## Git
- Work on a branch per spec: `feat/NNN-short-name`. Don't commit directly to `main`.
- Small commits with clear messages, e.g. `feat(001): add health check endpoint`.
- Ask before pushing, merging, or rewriting history.
- Never commit secrets, credentials, or `.env` files.

## AWS safety rules
- The developer is new to AWS. When introducing an AWS service or concept for the first time, explain briefly what it is and why it's needed.
- **Never run commands that create, change, or delete AWS resources or Terraform state without explicit approval in the current session.** This includes `terraform apply`, `terraform destroy`, `terraform import`, any `terraform state` command that changes state (`mv`, `rm`, `push`, `replace-provider`), and any `aws` command that creates, updates, puts, or deletes. Enabling Bedrock model access and requesting quota changes count too.
- These are fine without asking: `terraform fmt`, `terraform validate`, `terraform init`, `terraform plan`, and read-only `aws` commands (`describe`, `list`, `get`, `aws sts get-caller-identity`).
- Always show `terraform plan` output and summarize it (what will be created, changed, and destroyed) before proposing an apply.
- Terraform state lives in a remote S3 backend with state locking. Never commit state files or `.tfvars` files containing real values; commit only `*.tfvars.example`.
- Never hardcode credentials. Use the AWS profile in `AWS_PROFILE`. Application code reads secrets from environment variables. In AWS, those are injected from AWS Secrets Manager, so the same code runs locally.
- Prefer the smallest, cheapest resource sizes in dev, and point out anything that costs money while idle. Point out Bedrock token costs before large model runs.

## Conventions
- **Python:** type hints everywhere; `ruff` clean.
- **Pipeline (spike):** one module per stage (acquisition, extraction, canonicalization, retrieval, classification, evaluation), so failures can be traced to a stage (SiLab §10). Pydantic models are the schema source of truth (ADR 0009, proposed). Every output records the model, prompt version, run ID, and source locators (SiLab §4.7).
- **Config:** settings from environment variables (Pydantic Settings); `.env.example` documents every variable.
- **After the gate:** FastAPI routers grouped by domain under `backend/app/api/`, with API routes versioned under `/api/v1`. Database schema changes go only through Alembic migrations, never by hand. Frontend API calls go in a dedicated client module, not scattered through components.

## Commands
<!-- Fill these in once spec 001 is implemented. -->
- Pipeline tests: `cd pipeline && uv run pytest`
- Pipeline lint: `cd pipeline && uv run ruff check .`
- Pipeline CLI help: `cd pipeline && uv run evidence-mapper --help`
- Infra format check: `cd infra && terraform fmt -check -recursive`
- Infra validate: `cd infra && terraform init && terraform validate`
- Infra plan (read-only preview): `cd infra && terraform plan`
