"""Docket shortlist: discovery, enrichment and ranking (spec 003, FR-2 to FR-4).

Phases (plan 003):
1. Discover: EPA `Rule` documents posted in the date range -> candidate dockets, after title and
   subtype exclusions.
2. Count: posted comment count per candidate docket.
3. Documents: for dockets in the comment range, the docket title, whether a final rule is
   present, and documents whose titles look like a response to comments (RTC).
4. Sample (T6): attachment formats and text layer for the top N.

Phases record results on `ShortlistState` as they go. If the client stops the run (budget or
rate limit), what finished is kept, and each docket says which phase it completed.

Outputs hold metadata only: IDs, public document and docket titles, counts, formats. Never
comment text, comment titles or submitter details.
"""

import logging
import re
from datetime import date
from enum import IntEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from evidence_mapper.acquisition.regulations_gov import (
    ApiError,
    ApiStop,
    RegulationsGovClient,
)

logger = logging.getLogger(__name__)

PAGE_SIZE = 250
DISCOVERY_WARN_ABOVE = 5_000

DEFAULT_TITLE_EXCLUDES: tuple[str, ...] = (
    r"Air Plan Approval",
    r"Approval and Promulgation of",
    r"Pesticide Tolerances?",
)
DEFAULT_SUBTYPE_EXCLUDES: tuple[str, ...] = ("Correction", "Withdrawal")
DEFAULT_RTC_PATTERNS: tuple[str, ...] = (
    r"responses?\s+to\s+(?:the\s+)?(?:public\s+)?comments?",
    r"comments?\s+(?:and|&)\s+responses?",
    r"comment\s+responses?",
    r"summary\s+of\s+(?:the\s+)?(?:public\s+)?comments?",
    r"\bRTC\b",
)


class ShortlistOptions(BaseModel):
    """Every option of a shortlist run. Recorded in run.json."""

    posted_from: date = date(2022, 1, 1)
    posted_to: date = date(2024, 12, 31)
    min_comments: int = Field(300, ge=0)
    max_comments: int = Field(1_000, ge=0)
    top: int = Field(10, ge=0)
    sample_comments: int = Field(30, ge=0)
    sample_pdfs: int = Field(5, ge=0)
    max_pdf_mb: float = Field(25, gt=0)
    seed: int = 0
    budget: int = Field(800, ge=0)
    min_interval: float = Field(4.0, ge=0)
    rate_limit_reserve: int = Field(25, ge=0)
    on_rate_limit: Literal["stop", "wait"] = "stop"
    exclude_title_patterns: list[str] = Field(default_factory=lambda: list(DEFAULT_TITLE_EXCLUDES))
    exclude_subtypes: list[str] = Field(default_factory=lambda: list(DEFAULT_SUBTYPE_EXCLUDES))
    rtc_patterns: list[str] = Field(default_factory=lambda: list(DEFAULT_RTC_PATTERNS))
    text_min_chars: int = Field(20, ge=1)


class Phase(IntEnum):
    """The last phase a docket completed. Ordered, so later phases compare greater."""

    DISCOVERED = 1
    COUNTED = 2
    DOCUMENTS = 3
    SAMPLED = 4


class FinalRuleDoc(BaseModel):
    document_id: str
    title: str | None = None
    posted_date: str | None = None
    subtype: str | None = None


class RtcCandidate(BaseModel):
    document_id: str
    document_type: str | None = None
    title: str
    matched_pattern: str


class DocketRow(BaseModel):
    """One candidate docket. Metadata only."""

    docket_id: str
    docket_title: str | None = None
    final_rules: list[FinalRuleDoc] = Field(default_factory=list)
    posted_comment_count: int | None = None
    in_comment_range: bool | None = None
    document_count: int | None = None
    final_rule_present: bool | None = None
    rtc_candidates: list[RtcCandidate] = Field(default_factory=list)
    rank: int | None = None
    phase_completed: Phase = Phase.DISCOVERED
    error: str | None = None
    sample: Any = None  # SampleSummary, filled in phase 4 (T6)

    @property
    def latest_final_rule_date(self) -> str:
        return max((r.posted_date or "" for r in self.final_rules), default="")


class Exclusions(BaseModel):
    """How many dockets the title and subtype exclusions removed, per pattern or subtype.

    A docket is excluded when none of its `Rule` documents survive. It is counted under every
    pattern or subtype that matched one of its documents.
    """

    dockets_excluded: int = 0
    by_title_pattern: dict[str, int] = Field(default_factory=dict)
    by_subtype: dict[str, int] = Field(default_factory=dict)


class DiscoveryStats(BaseModel):
    rule_documents: int = 0
    total_elements: int | None = None
    pages: int = 0
    dockets_found: int = 0
    dockets_kept: int = 0
    complete: bool = False


class ShortlistState(BaseModel):
    options: ShortlistOptions
    rows: dict[str, DocketRow] = Field(default_factory=dict)
    discovery: DiscoveryStats = Field(default_factory=DiscoveryStats)
    exclusions: Exclusions = Field(default_factory=Exclusions)
    stop_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)

    @property
    def stopped_early(self) -> bool:
        return self.stop_reason is not None

    def ranked(self) -> list[DocketRow]:
        return sorted((r for r in self.rows.values() if r.rank is not None), key=_rank_of)

    def top_rows(self) -> list[DocketRow]:
        return [r for r in self.ranked() if r.rank is not None and r.rank <= self.options.top]


def _rank_of(row: DocketRow) -> int:
    assert row.rank is not None
    return row.rank


def _data(body: dict[str, Any]) -> list[dict[str, Any]]:
    data = body.get("data")
    return data if isinstance(data, list) else []


def _meta(body: dict[str, Any]) -> dict[str, Any]:
    meta = body.get("meta")
    return meta if isinstance(meta, dict) else {}


def _attrs(item: dict[str, Any]) -> dict[str, Any]:
    attrs = item.get("attributes")
    return attrs if isinstance(attrs, dict) else {}


def _paged(
    client: RegulationsGovClient, path: str, params: dict[str, str], page_size: int
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    """All items of a paged list endpoint, the first page's meta, and the number of pages."""
    items: list[dict[str, Any]] = []
    first_meta: dict[str, Any] = {}
    page = 1
    while True:
        body = client.get_json(
            path, {**params, "page[size]": str(page_size), "page[number]": str(page)}
        )
        meta = _meta(body)
        if page == 1:
            first_meta = meta
        rows = _data(body)
        items.extend(rows)
        total_pages = meta.get("totalPages")
        if not rows or not meta.get("hasNextPage"):
            break
        if isinstance(total_pages, int) and page >= total_pages:
            break
        page += 1
    return items, first_meta, page


# Phase 1: discover


def discover(
    client: RegulationsGovClient, state: ShortlistState, page_size: int = PAGE_SIZE
) -> None:
    """Find EPA `Rule` documents in the date range and turn them into candidate dockets."""
    opts = state.options
    params = {
        "filter[agencyId]": "EPA",
        "filter[documentType]": "Rule",
        "filter[postedDate][ge]": opts.posted_from.isoformat(),
        "filter[postedDate][le]": opts.posted_to.isoformat(),
    }
    items, meta, pages = _paged(client, "/documents", params, page_size)
    total = meta.get("totalElements")
    state.discovery.total_elements = total if isinstance(total, int) else None
    state.discovery.pages = pages
    state.discovery.rule_documents = len(items)
    if isinstance(total, int) and total > DISCOVERY_WARN_ABOVE:
        state.warnings.append(
            f"discovery query reported {total} results (> {DISCOVERY_WARN_ABOVE}); "
            "check that every page was returned"
        )
    if isinstance(total, int) and len(items) < total:
        state.warnings.append(f"discovery returned {len(items)} of {total} documents")

    title_res = [(p, re.compile(p, re.IGNORECASE)) for p in opts.exclude_title_patterns]
    subtypes = set(opts.exclude_subtypes)
    kept: dict[str, list[FinalRuleDoc]] = {}
    matched: dict[str, tuple[set[str], set[str]]] = {}
    seen_docs: set[str] = set()
    for item in items:
        attrs = _attrs(item)
        docket_id = attrs.get("docketId")
        doc_id = item.get("id")
        if not isinstance(docket_id, str) or not isinstance(doc_id, str) or doc_id in seen_docs:
            continue
        seen_docs.add(doc_id)
        doc = FinalRuleDoc(
            document_id=doc_id,
            title=attrs.get("title"),
            posted_date=attrs.get("postedDate"),
            subtype=attrs.get("subtype"),
        )
        title_hits = {p for p, rx in title_res if rx.search(doc.title or "")}
        subtype_hit = doc.subtype if doc.subtype in subtypes else None
        if title_hits or subtype_hit:
            pats, subs = matched.setdefault(docket_id, (set(), set()))
            pats.update(title_hits)
            if subtype_hit:
                subs.add(subtype_hit)
            continue
        kept.setdefault(docket_id, []).append(doc)

    excluded = set(matched) - set(kept)
    state.exclusions = Exclusions(
        dockets_excluded=len(excluded),
        by_title_pattern={
            p: sum(1 for d in excluded if p in matched[d][0]) for p in opts.exclude_title_patterns
        },
        by_subtype={
            s: sum(1 for d in excluded if s in matched[d][1]) for s in opts.exclude_subtypes
        },
    )
    for docket_id in sorted(kept):
        row = state.rows.setdefault(docket_id, DocketRow(docket_id=docket_id))
        row.final_rules = sorted(
            kept[docket_id], key=lambda d: (d.posted_date or "", d.document_id)
        )
    state.discovery.dockets_found = len(set(kept) | excluded)
    state.discovery.dockets_kept = len(kept)
    state.discovery.complete = True
    logger.info(
        "discovery: %d rule documents, %d dockets, %d kept, %d excluded",
        len(items),
        state.discovery.dockets_found,
        len(kept),
        len(excluded),
    )


# Phase 2: count


def count_comments(client: RegulationsGovClient, state: ShortlistState) -> None:
    """Posted comment count for every docket that hasn't been counted yet."""
    opts = state.options
    for docket_id in sorted(state.rows):
        row = state.rows[docket_id]
        if row.phase_completed >= Phase.COUNTED or row.error:
            continue
        try:
            body = client.get_json("/comments", {"filter[docketId]": docket_id, "page[size]": "5"})
        except ApiError as err:
            row.error = f"count failed: status={err.status}"
            logger.warning("count failed for %s: status=%s", docket_id, err.status)
            continue
        total = _meta(body).get("totalElements")
        if not isinstance(total, int):
            row.error = "count failed: no totalElements"
            continue
        row.posted_comment_count = total
        row.in_comment_range = opts.min_comments <= total <= opts.max_comments
        row.phase_completed = Phase.COUNTED
    in_range = sum(1 for r in state.rows.values() if r.in_comment_range)
    logger.info("count: %d dockets, %d in comment range", len(state.rows), in_range)


# Phase 3: documents


def analyze_documents(
    documents: list[dict[str, Any]], options: ShortlistOptions
) -> tuple[bool, list[RtcCandidate]]:
    """Whether a final rule is present, and RTC candidates by title (FR-3, AC-2).

    A final rule is a `Rule` document whose subtype is not excluded (e.g. not a Correction).
    RTC candidates are documents of any type whose title matches an RTC pattern. They are
    candidates for a person to confirm, not confirmed RTC documents.
    """
    subtypes = set(options.exclude_subtypes)
    rtc_res = [(p, re.compile(p, re.IGNORECASE)) for p in options.rtc_patterns]
    final_rule = False
    candidates: list[RtcCandidate] = []
    for item in documents:
        attrs = _attrs(item)
        doc_id = item.get("id")
        if not isinstance(doc_id, str):
            continue
        if attrs.get("documentType") == "Rule" and attrs.get("subtype") not in subtypes:
            final_rule = True
        title = attrs.get("title") or ""
        for pattern, rx in rtc_res:
            if rx.search(title):
                candidates.append(
                    RtcCandidate(
                        document_id=doc_id,
                        document_type=attrs.get("documentType"),
                        title=title,
                        matched_pattern=pattern,
                    )
                )
                break
    candidates.sort(key=lambda c: c.document_id)
    return final_rule, candidates


def list_documents(
    client: RegulationsGovClient, state: ShortlistState, page_size: int = PAGE_SIZE
) -> None:
    """Docket title, final-rule presence and RTC candidates for dockets in the comment range."""
    for docket_id in sorted(state.rows):
        row = state.rows[docket_id]
        if not row.in_comment_range or row.phase_completed >= Phase.DOCUMENTS or row.error:
            continue
        try:
            docket = client.get_json(f"/dockets/{docket_id}")
            documents, meta, _ = _paged(
                client, "/documents", {"filter[docketId]": docket_id}, page_size
            )
        except ApiError as err:
            row.error = f"documents failed: status={err.status}"
            logger.warning("documents failed for %s: status=%s", docket_id, err.status)
            continue
        data = docket.get("data")
        row.docket_title = _attrs(data).get("title") if isinstance(data, dict) else None
        row.document_count = len(documents)
        row.final_rule_present, row.rtc_candidates = analyze_documents(documents, state.options)
        row.phase_completed = Phase.DOCUMENTS
        logger.info(
            "documents for %s: %d documents, final rule %s, %d RTC candidates",
            docket_id,
            len(documents),
            row.final_rule_present,
            len(row.rtc_candidates),
        )


# Ranking


def rank(state: ShortlistState) -> None:
    """Rank dockets that completed phase 3 and are in range.

    Order: RTC candidate present first, then most recent final rule, then docket ID.
    """
    eligible = [
        r
        for r in state.rows.values()
        if r.in_comment_range and r.phase_completed >= Phase.DOCUMENTS and not r.error
    ]
    for row in state.rows.values():
        row.rank = None
    eligible.sort(key=lambda r: r.docket_id)
    eligible.sort(key=lambda r: r.latest_final_rule_date, reverse=True)
    eligible.sort(key=lambda r: not r.rtc_candidates)
    for i, row in enumerate(eligible, start=1):
        row.rank = i


def run_phases_1_to_3(
    client: RegulationsGovClient, state: ShortlistState, page_size: int = PAGE_SIZE
) -> None:
    """Run discovery, counting and documents, then rank. Stops cleanly on `ApiStop`."""
    try:
        if not state.discovery.complete:
            discover(client, state, page_size)
        count_comments(client, state)
        list_documents(client, state, page_size)
    except ApiStop as stop:
        state.stop_reason = stop.reason
        logger.warning("run stopped: %s", stop.reason)
    rank(state)
