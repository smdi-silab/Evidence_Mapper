# Tasks 002: Continuous integration for the pipeline

- **Spec:** [spec.md](spec.md) · **Plan:** [plan.md](plan.md)
- **Status:** Not started

Work top to bottom, one task at a time. Check off each task when its code and tests are done.
Each task names the requirements (FR) or acceptance criteria (AC) it covers.

## Tasks
- [ ] **T1:** Add `.github/workflows/pipeline.yml` as designed in the plan; check AC-4 and AC-5 with `grep`. (covers FR-1 to FR-5, AC-4, AC-5)
- [ ] **T2:** Docs: mention the CI check in `CLAUDE.md` (Commands) and `README.md` (Getting started). (covers FR-6)
- [ ] **T3:** Push the branch and open the PR; confirm the check runs and passes. (covers AC-1, AC-3)
- [ ] **T4:** AC-2 check: draft PR from a temporary branch, four breaking commits, confirm each fails; close the PR and delete the branch. (covers AC-2)

## Definition of done
- [ ] Every acceptance criterion checked (all manual; see plan Testing strategy)
- [ ] `docs/architecture.md` updated if the architecture changed (not expected)
- [ ] ADR written for any significant decision (none expected)
- [ ] Spec Status set to Implemented
