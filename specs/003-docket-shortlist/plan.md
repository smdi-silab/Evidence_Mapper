# Plan 003: Docket shortlist

- **Spec:** [spec.md](spec.md)
- **Status:** Approved

## Approach
Add a read-only Regulations.gov v4 client and an `evidence-mapper shortlist` command to the acquisition stage. The command works in phases:

1. Find EPA final rules posted in a date range.
2. Count posted comments for each of their dockets.
3. For dockets in the comment range, list their documents to find the final rule and any RTC candidates.
4. For the top 10 candidates, sample comments, tally attachment formats, and test a few PDFs for a text layer.

Every API response is cached on disk, so a rerun replays finished work for free and continues where the last run stopped. The command writes a JSONL shortlist and a Markdown summary under `data/manifests/shortlist/`, where they are committed. Both contain metadata only.

Tests use hand-made fixtures served through `httpx.MockTransport`, so the test suite needs no network and no key. Tests are optional for `pipeline/` code, but the spec asks for them (FR-9, AC-1 to AC-8).

## Components affected
- [x] Pipeline: `acquisition` becomes a package, plus a new CLI command
- [x] Data layout: `data/cache/` (ignored), `data/manifests/shortlist/` (tracked), `data/README.md`
- [x] Docs: `docs/architecture.md`, `pipeline/README.md`, `CLAUDE.md` Commands
- [ ] Backend, database, frontend: none (ADR 0002)
- [ ] Infrastructure (AWS): none. No AWS cost.

## Decisions taken in this plan

### `acquisition` becomes a package
FR-1 puts the command "in the `acquisition` module". The stage now has three distinct parts, so `acquisition.py` becomes a package `acquisition/`. It stays one stage, so failures still trace to acquisition (SiLab §10). Spec 004 (fetch and freeze) will reuse the client.

```
pipeline/src/evidence_mapper/acquisition/
  __init__.py          stage docstring (as today)
  regulations_gov.py   HTTP client: key header, throttle, request budget, 429 handling, disk cache
  shortlist.py         discovery, enrichment, ranking; Pydantic models for rows and the run record
  pdf_text.py          text-layer check (PyMuPDF)
  report.py            writes shortlist.jsonl and summary.md
```

### Discovery starts from final rules, not dockets
The `/dockets` endpoint has no comment counts and can only be filtered by last-modified date. That date is a poor proxy for "completed action". Instead, discovery queries `/documents` with `filter[agencyId]=EPA`, `filter[documentType]=Rule` and `filter[postedDate]` within the range, then collects the distinct docket IDs. **This reads FR-2's "date range" as the date the final rule was posted.** Every candidate therefore has a final rule by construction. FR-3 still reports it, from the docket's own document list (phase 3), so AC-2 tests a real check.

- **Paging (changed after T1).** T1 found no 20-page limit: page 21 at size 250 returned rows. EPA posted 1,405 `Rule` documents from 2022 to 2024, so discovery pages through the whole range in one query (about 6 requests) without month windows. It logs a warning if `totalElements` is over 5,000, in case a limit appears later.
- **Subtype exclusions (added after T1).** `Rule` documents have a `subtype`. A document with subtype `Correction` or `Withdrawal` doesn't make its docket a candidate, because these aren't completed actions in the DS-01 sense. A docket still counts if it has another `Rule` document. Each row records the subtypes of its final-rule documents.
- **Title exclusions.** EPA posts many high-volume, low-comment rules, such as state implementation plan approvals and pesticide tolerances. Counting comments for each of them would use most of the request budget. A default, configurable list of title patterns (e.g., `Air Plan Approval`, `Approval and Promulgation of`, `Pesticide Tolerance`) skips them before the counting phase. The report lists the patterns and how many dockets each one excluded, so a person can check whether anything relevant was dropped.

### Phases and request cost
| Phase | Requests | What it records |
|---|---|---|
| 1. Discover | 1 per 250 rules (~6 for 2022–2024) | docket IDs, final-rule document IDs, titles and subtypes |
| 2. Count | 1 per docket left after exclusions (`/comments?filter[docketId]=…&page[size]=5`, reads `meta.totalElements`) | posted comment count |
| 3. Documents | 1+ per docket in the comment range (`/documents?filter[docketId]=…`, 250 per page) | final rule present, RTC candidates |
| 4. Sample | per top candidate: ~1–4 to list comment IDs, 1 per sampled comment (`/comments/{id}?include=attachments`), plus PDF downloads | attachment formats, share with attachments, restricted vs downloadable attachments, summed `duplicateComments`, text-layer share |

**Ranking for the top N:** first dockets with at least one RTC candidate, then dockets whose final rule was posted most recently, with docket ID as the final tiebreak. Every in-range docket appears in the shortlist; only the top N get phase 4.

**Phase 2 volume (measured in T1):** about 1,100 dockets after the title exclusions, a rough estimate scaled from three sample months. That is more than one run's budget. The first run stops at its budget, and a second run about an hour later continues from the cache. The date range stays 2022–2024.

### Defaults
| Option | Default | Note |
|---|---|---|
| `--posted-from` / `--posted-to` | `2022-01-01` / `2024-12-31` | final-rule posted date; v4-era; completed actions |
| `--min-comments` / `--max-comments` | 300 / 1,000 | D-03; raw posted count, not unique submissions |
| `--top` | 10 | confirmed in spec |
| `--sample-comments` | 30 per candidate | seeded random sample from the full comment-ID list |
| `--sample-pdfs` | 5 per candidate | seeded random choice among PDF attachments in the sample |
| `--max-pdf-mb` | 25 | larger PDFs are skipped and counted as skipped |
| `--budget` | 800 API requests per run | under the 1,000/hour default |
| `--min-interval` | 4.0 s between API requests | at most ~900 requests/hour |
| `--rate-limit-reserve` | 25 | stop when `X-RateLimit-Remaining` falls to this |
| `--on-rate-limit` | `stop` | or `wait` (see below) |
| `--seed` | 0 | recorded in the run record |
| `--exclude-title` | built-in list | repeatable; `--no-default-excludes` clears it |

With all 10 candidates sampled, phase 4 costs about 10 × (2 + 30) ≈ 320 API requests plus up to 50 PDF downloads.

### Client behavior (FR-6, FR-7)
- **HTTP library: `httpx`.** It has a built-in `MockTransport`, so tests can count every outgoing request without the network.
- **Key handling.** The key is sent only in the `X-Api-Key` header, and only to `api.regulations.gov`. Attachment downloads (`downloads.regulations.gov`) use a separate client that never carries the key.
- **Cache.** Successful (200) API responses only. Key = SHA-256 of the method, the URL path and the sorted query parameters (the key is not part of it). Stored at `data/cache/regulations_gov/<aa>/<sha>.json` with the body, status, URL (no key) and fetch time. A cache hit makes no request and doesn't count against the budget (AC-4).
- **Budget.** A counter checked before each network request. When it is spent, the client raises `BudgetExhausted`. The command catches it, marks the run `stopped_early`, and writes the report with whatever finished, marking incomplete dockets by phase (AC-5).
- **429 (AC-3).** The response is never cached or parsed as data. With `stop`, the run ends like a spent budget. With `wait`, it sleeps for `Retry-After` (or 60 s if absent), up to 3 times, then stops. The sleep function is injected, so tests don't wait.
- **Other errors.** 5xx and timeouts are retried twice with backoff, then the docket is marked failed with its status code and the run continues. 404 marks the item missing.
- **Downloads** are counted separately from API requests, throttled with the same interval, and reported on their own line.

### Text-layer check (FR-5, D-02, DS-04)
- Each PDF is downloaded to `data/cache/attachments/<docket-id>/<attachment-id>.pdf` and opened with PyMuPDF. A page counts as having a text layer if `page.get_text()` has at least 20 non-whitespace characters. The 20 is an **assumption**: it stops a scanned page with a stamped header from counting as text. The threshold is recorded in the report.
- The result (page count, pages with text, file size, SHA-256) goes into `data/cache/attachments/results.json`. **The PDF is then deleted.** This keeps no attachment copies while DS-07 is Open, and a rerun reads the stored result instead of downloading again.
- Text is only measured, never stored or logged.
- Reported per docket: PDFs checked, PDFs skipped (size or error), pages with text / total pages, and PDFs with ≥80% text pages / PDFs checked (the DS-01 criterion, on a small sample).

### RTC detection (FR-3)
Case-insensitive regular expressions over the titles of all documents in the docket, for example: `response[s]? to (public )?comments?`, `comment response`, `\bRTC\b`, `summary of (public )?comments`. Each match is listed with its document ID, document type and title for a person to confirm. If nothing matches, the report says "none found by title" (AC-2's "absent"), because the response may sit in the final rule's preamble. The patterns and the document types searched are written into the run record.

### Outputs (FR-8)
```
data/manifests/shortlist/<run-id>/      TRACKED (spec answer: commit it)
  shortlist.jsonl   one row per in-range docket
  summary.md        run parameters, request use, ranked table, top-N detail, caveats
  run.json          run ID, date, tool version, git commit, all options, request and download counts,
                    stopped_early and reason, cache hits, exclusion counts, RTC patterns, threshold
data/cache/                              IGNORED: working files, not a freeze; safe to delete
  regulations_gov/                       API response cache (contains comment text)
  attachments/                           temporary PDFs (deleted after measuring) and results.json
```
- **Run ID:** `shortlist-<UTC timestamp>`, for example `shortlist-20261125T153000Z`.
- **Shortlist row fields:** `docket_id`, `docket_title`, `posted_comment_count`, `in_comment_range`, `final_rule` (present, document IDs, posted dates, subtypes), `rtc_candidates` (document ID, type, title, matched pattern), `rank`, `phase_completed`, and for the top N: `sampled_comments`, `share_with_attachments`, `attachment_formats` (format → count), `share_with_download_links` (A-02), `restricted_attachments` and `downloadable_attachments` (counts, A-02), `sampled_duplicate_comments` (sum of `duplicateComments` over the sample), and the text-layer figures.
- **Never in outputs or logs:** comment text, comment titles, submitter names, attachment text, the key. Comment titles are left out because they often contain the commenter's name.
- The summary always states that counts are **posted** comments before campaign collapse, so they aren't DS-01's "unique submissions". It also says that EPA sometimes posts one representative of a mass campaign, so the number of comments received can be higher. The summed `duplicateComments` is shown as a sample figure, not as a count of unique submissions.

## CLI
`evidence-mapper shortlist [options]`, a top-level command:
- Calls `settings.require("regulations_gov_api_key")` first. If the key is unset, it exits 1 with `Missing required setting(s): REGULATIONS_GOV_API_KEY` (AC-8).
- Prints progress by phase and ends with the output paths, the requests used out of the budget, and whether the run stopped early.
- Exit status 0 when it finishes, including a clean early stop. 1 for a missing key or an unexpected error.
- No new environment variables. Everything else is a CLI option, recorded in `run.json`.

## Data layout and docs
- `data/README.md`: add `cache/` (ignored working files) and `manifests/shortlist/` (tracked).
- `.gitignore`: no change needed. `data/*` already ignores `cache/`, and `!data/manifests/` already tracks the new folder. `test_gitignore.py` gains both paths.
- `docs/architecture.md`, `pipeline/README.md`, and `CLAUDE.md` Commands: add the command.

## Dependencies
- **`httpx`** (BSD-3-Clause): HTTP client.
- **`pymupdf`** (AGPL-3.0 or commercial; DS-04): PDF text layer. Fine for internal spike use. See Risks.
  Pinned to `>=1.26,<2` (T2). PyMuPDF 2.x adds `onnxruntime`, `numpy` and a layout model as dependencies (about 200 MB), which a text-layer check doesn't need. 1.28.2 has no dependencies and the same API.

## Security and privacy
- GET only; no writes to Regulations.gov.
- The key is sent in a header only and never put in URLs, cache keys, cache files, outputs or logs. The spec 001 redaction filter is the backstop.
- The response cache holds public comment text, but under `data/`, which is gitignored by default.
- PDFs are deleted after measuring (DS-07 is Open). Only figures and hashes are kept.
- Comment and attachment text is untrusted data. This command only counts and matches titles, and makes no model calls (SP-02 doesn't come into play).
- Logs hold docket and comment IDs, counts, status codes, timings and errors only (SP-01).

## Testing strategy
Fixtures are **hand-made JSON shaped like real responses**, not recordings. Real comment responses contain comment text and submitter names, which must not be committed. T1 checks the fixture shapes against a few live responses, which stay in the ignored cache. Tests build their PDFs with PyMuPDF at run time.

| Acceptance criterion | Test(s) | Type |
|---|---|---|
| AC-1 | `test_shortlist.py::test_ac1_fixture_dockets_produce_expected_table`: three fixture dockets (in range with RTC, in range without, out of range) plus one excluded by title; compares the rows to an expected JSONL | unit |
| AC-2 | `test_shortlist.py::test_ac2_final_rule_and_rtc_detected`; `test_ac2_absent_when_no_rule_or_rtc` | unit |
| AC-3 | `test_regulations_gov.py::test_ac3_429_stop_not_cached`; `test_ac3_429_wait_then_success` (fake sleep, asserts the wait and that the 429 body isn't cached or used) | unit |
| AC-4 | `test_regulations_gov.py::test_ac4_rerun_makes_no_repeat_requests`: first run interrupted by a budget of k, second run with the same cache; the transport counts requests and checks no URL is requested twice | unit |
| AC-5 | `test_shortlist.py::test_ac5_budget_caps_requests_and_reports_it`: budget N less than needed; asserts exactly N requests, `requests_used == N` and `stopped_early` in `run.json` and `summary.md` | unit |
| AC-6 | `test_pdf_text.py::test_ac6_one_text_page_one_without`: a two-page PDF, one page with inserted text and one with only a drawn shape | unit |
| AC-7 | `test_shortlist.py::test_ac7_no_comment_or_attachment_text_or_key_in_outputs`: sentinel strings in fixture comment text, comment titles and PDF text, plus a fake key; checks every output file, stdout, stderr and captured logs | unit |
| AC-8 | `test_cli.py::test_ac8_shortlist_without_key_exits_nonzero_naming_variable` | unit |
| AC-9 | Manual live run (T-last); `run.json` and `summary.md` committed as evidence | manual |

Also: a test that the download client never sends `X-Api-Key`.

## Alternatives considered
- **Discover from `/dockets`:** no comment counts, and only a last-modified filter, so many more requests for a worse match with "completed action".
- **Recorded fixtures (VCR-style):** realistic, but they would commit comment text and names. Hand-made fixtures checked against live shapes avoid that.
- **`requests` + `responses`/`requests-mock`:** works, but `httpx.MockTransport` needs no extra test library.
- **CSV output:** easy to open in a spreadsheet, but attachment formats and RTC candidates are nested. JSONL holds them cleanly, and `summary.md` has the readable table.
- **Keeping sampled PDFs:** saves re-downloading, but DS-07 is Open. Storing the measurement and deleting the file costs nothing on rerun.
- **Comment-count filter by sampling instead of counting:** cheaper, but the count is one request per docket and the range filter needs the exact number.

## Risks
- **API details:** checked live in T1 (see tasks.md, Verification results). The plan was updated for the differences: no 20-page limit, subtypes, restricted attachments, `duplicateComments`.
- **Phase 2 volume:** about 1,100 dockets (T1 estimate), so the live run takes two hourly runs. If the real number is much higher, narrow the date range or add exclusions.
- **Restricted attachments** (`fileFormats: null`) may be common in some dockets. The report counts them, and a docket where most are restricted fails A-02 for the spike.
- **Title exclusions can hide a good docket.** Mitigated by reporting exclusion counts per pattern and making the list configurable.
- **Posted comment counts undercount mass campaigns,** and RTC title matching misses responses inside preambles. Both are stated in the report as caveats, not hidden.
- **PyMuPDF is AGPL-3.0.** Fine for the spike. If it is kept after the gate in a hosted app, the license needs a decision (open the source, buy a commercial license, or switch to pdfplumber or pypdfium2). Worth a note in the register next to DS-04.
- **Comment sample bias.** 30 random comments per docket may contain few attachments, so the ≥80% figure is indicative only. The report shows numerators and denominators.
