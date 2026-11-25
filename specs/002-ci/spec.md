# Spec 002: Continuous integration for the pipeline

- **Status:** Draft
- **Owner:** Tony Lizza
- **Created:** 2026-11-25
- **Branch:** feat/002-ci

## Problem
Pipeline tests and lint checks run only when someone remembers to run them locally. PR #3 was merged on the strength of a local run. As specs 003 and later add pipeline stages, a check that runs automatically on every pull request makes sure `main` always passes its tests, without depending on memory.

## Users and context
Developers, including Claude Code, opening pull requests against `main`, and the reviewer deciding whether to merge.

## Goals
- Every pull request to `main`, and every push to `main`, runs the pipeline's tests, lint check and format check automatically.
- The result shows on the pull request as a pass or fail check.
- The workflow uses no secrets, has read-only access to the repository, and pins its third-party actions.

## Non-goals
- Terraform checks (`infra/` doesn't exist yet). Add them in the spec that creates `infra/`.
- Backend and frontend checks (after the gate).
- Branch protection rules that block merging until CI passes. This is a repository setting, not code. See Open questions.
- Deployment, releases, or anything that calls Regulations.gov, Bedrock, or other external services.
- A type checker (not adopted yet; see spec 001 plan Risks).

## Functional requirements
- **FR-1:** A GitHub Actions workflow in `.github/workflows/` that runs on pull requests targeting `main` and on pushes to `main`.
- **FR-2:** The workflow installs the pipeline exactly as locked (`uv sync --locked`), then runs `uv run pytest`, `uv run ruff check .` and `uv run ruff format --check .` in `pipeline/`.
- **FR-3:** The workflow uses the Python version from `pipeline/.python-version` and a pinned `uv` version.
- **FR-4:** The workflow's token has read-only repository permissions, and the workflow uses no repository secrets.
- **FR-5:** Third-party actions are pinned to full commit SHAs, with the version tag in a comment.
- **FR-6:** `CLAUDE.md` and `README.md` mention the CI check.

## Acceptance criteria
- **AC-1:** Given a pull request to `main`, when it is opened or updated, then the workflow runs and the pull request shows its result as a check.
- **AC-2:** Given a change that breaks a test, fails `ruff check`, is not `ruff`-formatted, or leaves `uv.lock` out of date with `pyproject.toml`, when the workflow runs, then the check fails.
- **AC-3:** Given the current `main` code, when the workflow runs, then the check passes.
- **AC-4:** The workflow file declares `permissions: contents: read` and references no `secrets.*` values.
- **AC-5:** Every `uses:` line references a full 40-character commit SHA.

## Non-functional requirements
- **Cost:** the repository is public, so GitHub-hosted runner minutes are free. A run should finish within a few minutes; the job has a 10-minute timeout.
- **Security:** no secrets in CI. Tests never call external services (all current tests are offline).
- **Supply chain:** pin actions by SHA, and prefer releases at least two weeks old.

## Data
None. CI never sees comment data: `data/` holds only manifests in git, and the tests use no data files.

## Open questions
- [ ] Should `main` require this check to pass before merging (a branch protection rule)? It's a repository setting you or an org admin would turn on in GitHub, after this spec merges. Recommended, but outside this spec.
- [x] Spec number: this spec takes 002 because it was started first. The docket shortlist and fetch-and-freeze specs move to 003 and 004 (spec 001's references are updated).

## Related
- [Spec 001](../001-spike-foundation/spec.md): the commands this workflow runs.
- CLAUDE.md "Testing policy" and "Commands".
