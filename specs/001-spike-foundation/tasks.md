# Tasks 001: Spike foundation

- **Spec:** [spec.md](spec.md) · **Plan:** [plan.md](plan.md)
- **Status:** Not started

Work top to bottom, one task at a time. Check off each task when its code and tests are done.
Each task names the requirements (FR) or acceptance criteria (AC) it covers.

## Tasks
- [ ] **T1:** Prerequisites: install `uv` (needs approval); `uv` fetches Python 3.12. (covers FR-1)
- [ ] **T2:** Package scaffold: `pyproject.toml`, `.python-version`, `src/evidence_mapper/` with the six empty stage modules, ruff and pytest config, `uv.lock`. (covers FR-1, FR-3, FR-7)
- [ ] **T3:** CLI: Typer app with `--help` and `--version`, plus tests. (covers FR-2, AC-1, AC-2)
- [ ] **T4:** Settings, `.env.example`, `config check` command and SP-01 logging setup, plus tests. (covers FR-4, FR-5, FR-9, AC-4, AC-5, logging NFR)
- [ ] **T5:** `data/` layout: `.gitignore` rules, `data/README.md`, manifests `.gitkeep` files, plus test. (covers FR-6, AC-6)
- [ ] **T6:** Docs: `README.md` Getting started; add `ruff format --check` to `CLAUDE.md` Commands; update `docs/architecture.md` with the package and data layout. (covers FR-8)
- [ ] **T7:** Verify from a fresh clone in the scratchpad: `uv sync`, `--help`, `--version`, pytest, ruff check, ruff format check. (covers AC-1, AC-3)

## Definition of done
- [ ] Every acceptance criterion has a passing test (AC-3 checked by running the commands)
- [ ] Lint and format checks pass (no type checker in scope; see plan Risks)
- [ ] `docs/architecture.md` updated
- [ ] ADR written for any significant decision (none expected; Typer and the data layout are recorded in plan.md)
- [ ] Spec Status set to Implemented
