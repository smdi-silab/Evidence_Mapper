# Spec 003: Docket shortlist

- **Status:** Draft
- **Owner:** Tony Lizza
- **Created:** 2026-11-25
- **Branch:** feat/003-docket-shortlist

## Problem
The spike needs one primary EPA docket and one backup (DS-01, D-03). The register says the choice must come from an API query, not from memory, because the main data risk is picking a docket whose substantive comments turn out to be scanned, dominated by campaigns, or lacking a response-to-comments (RTC) document (A-01, A-02). We need a read-only command that queries Regulations.gov and produces a shortlist with the facts needed to choose. This is pre-development task 5 in the register.

## Users and context
- The project lead, who makes the DS-01 decision.
- Claude (chat), which reviews the shortlist and recommends a primary and a backup (register task 7, D-04).
- Claude Code, which builds and runs the command.

There is no api.data.gov key yet (register task 3). The command must be buildable and testable without one; only the live run needs it.

## Goals
- List candidate EPA rulemaking dockets with the facts DS-01 asks for: comment count, whether a final rule exists, whether an RTC document is likely present, and what kinds of attachments the comments carry.
- Check, on a small sample, whether attachments have a text layer (D-02, the ≥80% criterion in DS-01).
- Stay within the API's published rate limits and resume after interruption without repeating requests.
- Produce a report the lead and Claude (chat) can read to choose a primary and a backup.

## Non-goals
- Choosing the docket. The command reports facts; the people decide (DS-01 stays Open until then).
- Fetching and freezing the chosen docket (spec 004). Nothing this command downloads is a frozen dataset.
- Near-duplicate detection. The "unique submissions after campaign collapse" count in DS-01 needs the full comment set, so the shortlist reports raw counts and flags the gap.
- DOT dockets (the D-03 backup option). Can be added later by configuration if EPA yields no good candidate.
- Any model calls or AWS resources.

## User stories
- As the project lead, I want a table of candidate EPA dockets with comment counts, final-rule and RTC status, and attachment text-extractability, so I can choose a primary and a backup with evidence.
- As a developer without an API key yet, I want to build and test the command against recorded responses, so the work isn't blocked on the key.

## Functional requirements
- **FR-1:** An `evidence-mapper shortlist` command (in the `acquisition` module) that queries the Regulations.gov v4 API read-only (GET only), using the API key from the environment (spec 001, FR-4).
- **FR-2:** Candidate discovery: list EPA rulemaking dockets, filtered by configurable criteria (at least a date range and a comment-count range defaulting to 300–1,000, per D-03).
- **FR-3:** For each candidate, report: docket ID, title, total comment count, whether a final rule document exists, whether a document that looks like an RTC exists (with its document ID and title so a person can confirm), and how the matching was done.
- **FR-4:** For the top candidates (a configurable number), sample a configurable number of comments and report attachment counts by file format and the share of comments that have attachments.
- **FR-5:** For the same sample, download a small number of PDF attachments to a temporary cache outside the frozen data and report the share of pages with a text layer (PyMuPDF, per DS-04). Attachment content and extracted text are never written to the report or logs.
- **FR-6:** Rate limiting: the client throttles to a configurable request budget, honors HTTP 429 and the `X-RateLimit-Remaining` header, and stops cleanly (not crashes) when the budget is spent.
- **FR-7:** Response cache: every API response is cached on disk (gitignored), so a rerun or a resumed run makes no repeat requests for data it already has.
- **FR-8:** Output: a machine-readable shortlist (CSV or JSONL) and a short Markdown summary, both containing metadata only (IDs, titles, counts, formats, rates), written to a location the plan defines. Each output records the run date, the query parameters, and the number of API requests used.
- **FR-9:** The command is tested against recorded or hand-made API fixtures, with no network access in the test suite.

## Acceptance criteria
- **AC-1:** Given recorded API fixtures and no API key or network, when the test suite runs, then the shortlist logic produces the expected table for the fixture dockets.
- **AC-2:** Given a docket fixture containing a final rule and a document titled like a response to comments, then the report marks the final rule as present and lists the RTC candidate with its document ID and title; given a docket without them, it marks them absent.
- **AC-3:** Given a fixture where the API returns HTTP 429, then the client waits or stops as configured, and doesn't count the failed request as data.
- **AC-4:** Given a run interrupted part-way, when it is rerun, then requests already in the cache are not repeated (test counts outgoing requests).
- **AC-5:** Given a request budget of N, then the command makes at most N API requests and the report states how many it used and whether it stopped early.
- **AC-6:** Given a sample PDF with a text layer and one without, then the text-extractability check reports one page with text and one without.
- **AC-7:** The report and the logs contain no comment text or attachment text, and no API key (test checks the outputs against fixture text and a fake key).
- **AC-8:** Given the API key is not set, when `evidence-mapper shortlist` runs, then it exits with a non-zero status and a message naming the missing variable.
- **AC-9 (manual):** Once a key exists, a live run produces a shortlist with at least one candidate, or states that no EPA docket met the criteria (which reopens A-01).

## Non-functional requirements
- **Rate limits:** api.data.gov's default is 1,000 requests per hour per key ("may vary by service"); `DEMO_KEY` allows only 30 per hour and 50 per day per IP, too few for a real run. The default request budget stays well under the hourly limit.
- **Logging (SP-01):** IDs, counts, timings, HTTP status codes and errors only.
- **Secrets (SP-04):** the key is sent in the `X-Api-Key` header, never in a URL that could be logged.
- **Frozen data (ADR 0007):** the cache and the sampled attachments are working files, not a freeze. Spec 004 fetches the chosen docket from scratch into a versioned freeze.
- **Cost:** no AWS cost. API use is free.

## Data
Public Regulations.gov metadata: dockets, documents (type, title, dates), comment counts, and comment attachment metadata. A small sample of public PDF attachments is downloaded temporarily, only to test for a text layer. No comment text is stored in outputs.

## Open questions
- [x] **API key.** Get a personal api.data.gov key now to unblock the live run, or wait for the organizational key DS-06 recommends? Building and testing don't need either.
- [x] **RTC detection.** Title matching (e.g., "response to comments", "RTC") on the docket's supporting documents is a heuristic. Is a list of candidates for a person to confirm acceptable? (Assumed yes in FR-3.)
- [x] **Sample sizes and budget.** Defaults proposed in the plan (e.g., top 10 candidates, 30 comments and 5 PDFs each). Fine to set in the plan?
- [x] **Where the report lives.** It holds only public metadata, so committing it (e.g., under `data/manifests/shortlist/`) would make the DS-01 decision traceable. Commit it, or keep it gitignored?
- [x] **Downloading attachments before DS-07.** FR-5 keeps a few public PDFs in a temporary, gitignored cache. DS-07 (whether attachment copies may be kept) is still Open. Is a temporary cache acceptable?

## Related
- Register: DS-01, DS-04, DS-06, DS-07, D-02, D-03, A-01, A-02; pre-development task 5.
- ADR 0007 (fetch once and freeze, proposed), ADR 0011 (data handling).
- Spec 001 (settings, logging), spec 004 (fetch and freeze, planned).
- SiLab §7.4.
