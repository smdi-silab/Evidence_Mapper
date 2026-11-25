# Tasks 002: Continuous integration for the pipeline

- **Spec:** [spec.md](spec.md) · **Plan:** [plan.md](plan.md)
- **Status:** Done

Work top to bottom, one task at a time. Check off each task when its code and tests are done.
Each task names the requirements (FR) or acceptance criteria (AC) it covers.

## Tasks
- [x] **T1:** Add `.github/workflows/pipeline.yml` as designed in the plan; check AC-4 and AC-5 with `grep`. (covers FR-1 to FR-5, AC-4, AC-5)
- [x] **T2:** Docs: mention the CI check in `CLAUDE.md` (Commands) and `README.md` (Getting started). (covers FR-6)
- [x] **T3:** Push the branch and open the PR; confirm the check runs and passes. (covers AC-1, AC-3)
- [x] **T4:** AC-2 check: draft PR from a temporary branch, four breaking commits, confirm each fails; close the PR and delete the branch. (covers AC-2)

## Definition of done
- [x] Every acceptance criterion checked (all manual; see plan Testing strategy)
- [x] `docs/architecture.md` updated if the architecture changed (not expected)
- [x] ADR written for any significant decision (none expected)
- [x] Spec Status set to Implemented

## Verification results (2026-11-25)
- **AC-1, AC-3:** PR #4's `checks` run passed in about 10 s: Python 3.12.16, 20 packages installed, ruff clean, 18 tests passed.
- **AC-2:** draft PR #5 (closed unmerged, branch deleted). Each break failed at the expected step:
  - failing test → Tests (`1 failed, 18 passed`)
  - unused import → Lint
  - unformatted file → Format check
  - `pyproject.toml` dependency added without re-locking → Install locked dependencies
  - Note: a first attempt at the failing-test break used `assert False`. Ruff flags that (B011), so it failed at Lint before the tests ran. It was redone with a lint-clean failing assertion.
- **AC-4, AC-5:** `grep` found `permissions: contents: read`, no `secrets.` references, and every `uses:` pinned to a 40-character SHA.
