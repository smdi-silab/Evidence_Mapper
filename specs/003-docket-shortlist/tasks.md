# Tasks 003: Docket shortlist

- **Spec:** [spec.md](spec.md) · **Plan:** [plan.md](plan.md)
- **Status:** Not started

Work top to bottom, one task at a time. Check off each task when its code and tests are done.
Each task names the requirements (FR) or acceptance criteria (AC) it covers.

## Tasks
- [ ] **T1:** Verify the API assumptions live (plan, Risks). A throwaway script in the scratchpad, run with `uv run --env-file .env`, makes at most 15 GET requests. It checks: the `/documents` filters (`agencyId`, `documentType=Rule`, `postedDate` range); the page-size and page-count limits; `/comments?filter[docketId]` with `meta.totalElements`; `/comments/{id}?include=attachments` and the `fileFormats` shape; and the `X-RateLimit-*` headers. It also measures how many dockets would reach phase 2 with the default date range and exclusions. The script prints only field names, counts and headers, never comment text. Record the findings below. If anything differs from the plan, stop and update the plan before T2. (covers plan Risks)
- [ ] **T2:** Add `httpx` and `pymupdf`, then re-lock. Turn `acquisition.py` into the `acquisition/` package with empty `regulations_gov.py`, `shortlist.py`, `pdf_text.py` and `report.py`. Ruff and the existing tests pass. (covers FR-1)
- [ ] **T3:** API client in `regulations_gov.py`: `X-Api-Key` header only to `api.regulations.gov`; minimum interval with an injectable clock and sleep; request budget with `BudgetExhausted`; disk cache of 200 responses; 429 handling (`stop` or `wait`, never cached); retries on 5xx and timeouts; a separate download client without the key. Tests: `test_ac3_*`, `test_ac4_rerun_makes_no_repeat_requests`, download-client-sends-no-key. (covers FR-6, FR-7, AC-3, AC-4)
- [ ] **T4:** Text-layer check in `pdf_text.py`: count pages with ≥20 non-whitespace characters, then store the result (pages, pages with text, size, SHA-256) in `results.json` and delete the PDF. Test: `test_ac6_one_text_page_one_without`. (covers FR-5, AC-6)
- [ ] **T5:** Hand-made fixtures matching the shapes T1 confirmed. Phases 1–3 in `shortlist.py`: month-window discovery, title exclusions with per-pattern counts, comment counts, document listing, final-rule and RTC detection, ranking. Pydantic models for shortlist rows. Tests: `test_ac2_*`. (covers FR-2, FR-3, AC-2)
- [ ] **T6:** Phase 4 in `shortlist.py`: seeded sample of comment IDs, attachment details, format tallies, share with attachments, share with download links, PDF selection with the size cap, text-layer figures per docket. Tests on fixtures. (covers FR-4, FR-5)
- [ ] **T7:** `report.py`: `shortlist.jsonl`, `summary.md` and `run.json` under `data/manifests/shortlist/<run-id>/`, with request and download counts, `stopped_early` and reason, options, patterns, threshold and caveats. Incomplete dockets are marked by phase. Tests: `test_ac1_fixture_dockets_produce_expected_table`, `test_ac5_budget_caps_requests_and_reports_it`, `test_ac7_no_comment_or_attachment_text_or_key_in_outputs`. (covers FR-8, AC-1, AC-5, AC-7)
- [ ] **T8:** `evidence-mapper shortlist` command in `cli.py` with the plan's options and defaults. It checks the key first, catches `BudgetExhausted` and 429 stops, and prints the output paths and request use. Test: `test_ac8_shortlist_without_key_exits_nonzero_naming_variable`. (covers FR-1, AC-8)
- [ ] **T9:** Docs: `data/README.md` (`cache/`, `manifests/shortlist/`), `docs/architecture.md`, `pipeline/README.md`, `CLAUDE.md` Commands. Add the new paths to `test_gitignore.py`. (covers plan, Data layout and docs)
- [ ] **T10:** Live run (AC-9). Before running, estimate the request count from T1's measurement and confirm it with you. Run with the defaults, rerunning after an hour if the budget stops it. Check that the outputs contain metadata only, then commit `data/manifests/shortlist/<run-id>/`. Record the results below. (covers AC-9)
- [ ] **T11:** Register: mark pre-development task 5 done; add the shortlist evidence to A-01 and A-02; note the PyMuPDF AGPL license next to DS-04. DS-01 stays Open for the people to decide (register task 7). Set the spec Status to Implemented. (covers spec Related)

## Definition of done
- [ ] Every acceptance criterion has a passing test (AC-9: manual, recorded below)
- [ ] `uv run ruff check .`, `uv run ruff format --check .` and `uv run pytest` pass (no type checker in scope; see plan 001)
- [ ] `docs/architecture.md` updated
- [ ] ADR written for any significant decision (none expected; PyMuPDF licensing goes to the register)
- [ ] Spec Status set to Implemented

## Verification results
_Filled in at T1 and T10._
