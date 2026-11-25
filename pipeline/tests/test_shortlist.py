"""Tests for the shortlist phases (spec 003: FR-2, FR-3, AC-2). No network."""

from pathlib import Path

import httpx
import pytest
from fake_api import FakeDoc, FakeRegulationsGov, standard_dockets

from evidence_mapper.acquisition.regulations_gov import (
    RegulationsGovClient,
    RequestBudget,
    ResponseCache,
    Throttle,
)
from evidence_mapper.acquisition.shortlist import (
    Phase,
    ShortlistOptions,
    ShortlistState,
    analyze_documents,
    run_phases_1_to_3,
)

FAKE_KEY = "FAKE-KEY-shortlist-0001"


def make_client(
    tmp_path: Path, handler: httpx.MockTransport | FakeRegulationsGov, budget: int = 1_000
) -> RegulationsGovClient:
    transport = handler.transport if isinstance(handler, FakeRegulationsGov) else handler
    return RegulationsGovClient(
        FAKE_KEY,
        ResponseCache(tmp_path / "cache"),
        RequestBudget(budget),
        Throttle(0.0, sleep=lambda s: None),
        transport=transport,
        retry_backoff=0.0,
    )


def run(
    tmp_path: Path, api: FakeRegulationsGov, page_size: int = 250, **opts: object
) -> ShortlistState:
    state = ShortlistState(options=ShortlistOptions(**opts))  # type: ignore[arg-type]
    run_phases_1_to_3(make_client(tmp_path, api), state, page_size=page_size)
    return state


def doc(doc_id: str, doc_type: str, title: str, subtype: str | None = None) -> dict:
    return {
        "id": doc_id,
        "attributes": {"documentType": doc_type, "title": title, "subtype": subtype},
    }


# AC-2


def test_ac2_final_rule_and_rtc_detected(tmp_path: Path) -> None:
    """AC-2: a docket with a final rule and an RTC-titled document is marked and listed."""
    state = run(tmp_path, FakeRegulationsGov(standard_dockets()))
    row = state.rows["EPA-HQ-OAR-2099-0001"]
    assert row.final_rule_present is True
    assert [(c.document_id, c.title) for c in row.rtc_candidates] == [
        ("EPA-HQ-OAR-2099-0001-0901", "Response to Comments Document for the Final Rule")
    ]
    assert row.rtc_candidates[0].document_type == "Supporting & Related Material"
    assert row.rtc_candidates[0].matched_pattern  # how the match was made (FR-3)


def test_ac2_absent_when_no_rule_or_rtc() -> None:
    """AC-2: a docket without a final rule or an RTC-titled document is marked absent."""
    documents = [
        doc("D-1", "Proposed Rule", "Fake Standards; Proposed Rule"),
        doc("D-2", "Supporting & Related Material", "Regulatory Impact Analysis"),
        doc("D-3", "Rule", "Fake Standards; Correction", subtype="Correction"),
    ]
    present, candidates = analyze_documents(documents, ShortlistOptions())
    assert present is False
    assert candidates == []


def test_ac2_rtc_absent_in_fixture_docket(tmp_path: Path) -> None:
    state = run(tmp_path, FakeRegulationsGov(standard_dockets()))
    row = state.rows["EPA-HQ-OW-2099-0002"]
    assert row.final_rule_present is True
    assert row.rtc_candidates == []


@pytest.mark.parametrize(
    "title",
    [
        "Response to Comments Document",
        "Responses to Public Comments on the Proposed Rule",
        "EPA Response to the Comments",
        "Summary of Public Comments and EPA Responses",
        "Comments and Responses",
        "Comment Response Document",
        "RTC for the Final Rule",
    ],
)
def test_rtc_title_patterns_match(title: str) -> None:
    _, candidates = analyze_documents(
        [doc("D-1", "Supporting & Related Material", title)], ShortlistOptions()
    )
    assert len(candidates) == 1


@pytest.mark.parametrize(
    "title",
    [
        "Regulatory Impact Analysis",
        "Comment period extension",
        "Earth Science Report",
        "Ratchet study",
    ],
)
def test_rtc_title_patterns_do_not_match(title: str) -> None:
    _, candidates = analyze_documents(
        [doc("D-1", "Supporting & Related Material", title)], ShortlistOptions()
    )
    assert candidates == []


# Phases 1-3 and ranking


def test_discovery_exclusions_and_date_range(tmp_path: Path) -> None:
    state = run(tmp_path, FakeRegulationsGov(standard_dockets()))
    assert set(state.rows) == {
        "EPA-HQ-OAR-2099-0001",
        "EPA-HQ-OW-2099-0002",
        "EPA-HQ-OLEM-2099-0003",
    }
    assert state.exclusions.dockets_excluded == 2
    assert state.exclusions.by_title_pattern["Air Plan Approval"] == 1
    assert state.exclusions.by_subtype == {"Correction": 1, "Withdrawal": 0}
    assert state.discovery.rule_documents == 5  # 0006 is outside the date range
    assert state.discovery.dockets_found == 5
    assert state.discovery.dockets_kept == 3
    assert state.discovery.complete


def test_docket_with_kept_and_excluded_rules_is_kept(tmp_path: Path) -> None:
    dockets = standard_dockets()
    dockets[0].documents.append(
        FakeDoc(
            "EPA-HQ-OAR-2099-0001-0950",
            "Rule",
            "Fake Standards; Correction",
            "2024-01-01T05:00:00Z",
            "Correction",
        )
    )
    state = run(tmp_path, FakeRegulationsGov(dockets))
    assert "EPA-HQ-OAR-2099-0001" in state.rows
    assert state.exclusions.dockets_excluded == 2


def test_counts_range_and_ranking(tmp_path: Path) -> None:
    state = run(tmp_path, FakeRegulationsGov(standard_dockets()))
    rows = state.rows
    assert rows["EPA-HQ-OAR-2099-0001"].posted_comment_count == 450
    assert rows["EPA-HQ-OLEM-2099-0003"].in_comment_range is False
    assert rows["EPA-HQ-OLEM-2099-0003"].phase_completed == Phase.COUNTED
    assert rows["EPA-HQ-OLEM-2099-0003"].rank is None
    # The RTC docket ranks first even though the other final rule is more recent.
    assert [r.docket_id for r in state.ranked()] == ["EPA-HQ-OAR-2099-0001", "EPA-HQ-OW-2099-0002"]
    assert (
        rows["EPA-HQ-OAR-2099-0001"].docket_title
        == "Fake Emission Standards for Widget Manufacturing"
    )
    assert rows["EPA-HQ-OAR-2099-0001"].document_count == 4
    assert rows["EPA-HQ-OAR-2099-0001"].final_rules[0].subtype == "Final Rule"
    assert state.stop_reason is None


def test_ranking_without_rtc_prefers_recent_final_rule(tmp_path: Path) -> None:
    dockets = standard_dockets()
    dockets[0].documents = [d for d in dockets[0].documents if "Response" not in d.title]
    state = run(tmp_path, FakeRegulationsGov(dockets))
    assert [r.docket_id for r in state.ranked()] == ["EPA-HQ-OW-2099-0002", "EPA-HQ-OAR-2099-0001"]


def test_pagination_covers_all_pages(tmp_path: Path) -> None:
    state = run(tmp_path, FakeRegulationsGov(standard_dockets()), page_size=2)
    assert state.discovery.rule_documents == 5  # 0006 is outside the date range
    assert state.discovery.pages == 3
    assert state.rows["EPA-HQ-OAR-2099-0001"].document_count == 4


def test_comment_range_is_configurable(tmp_path: Path) -> None:
    state = run(
        tmp_path, FakeRegulationsGov(standard_dockets()), min_comments=100, max_comments=500
    )
    assert [r.docket_id for r in state.ranked()] == [
        "EPA-HQ-OAR-2099-0001",
        "EPA-HQ-OLEM-2099-0003",
    ]


def test_api_error_on_one_docket_does_not_stop_the_run(tmp_path: Path) -> None:
    api = FakeRegulationsGov(standard_dockets())

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("filter[docketId]") == "EPA-HQ-OW-2099-0002":
            return httpx.Response(400)
        return api(request)

    state = ShortlistState(options=ShortlistOptions())
    run_phases_1_to_3(make_client(tmp_path, httpx.MockTransport(handler)), state)
    assert state.rows["EPA-HQ-OW-2099-0002"].error == "count failed: status=400"
    assert state.rows["EPA-HQ-OW-2099-0002"].rank is None
    assert state.rows["EPA-HQ-OAR-2099-0001"].rank == 1
    assert state.stop_reason is None


def test_budget_stop_keeps_partial_results(tmp_path: Path) -> None:
    api = FakeRegulationsGov(standard_dockets())
    state = ShortlistState(options=ShortlistOptions())
    # 1 discovery page + 2 counts, then the budget is spent.
    run_phases_1_to_3(make_client(tmp_path, api, budget=3), state)
    assert state.stop_reason == "request budget spent"
    assert state.stopped_early
    phases = {d: r.phase_completed for d, r in state.rows.items()}
    assert phases == {
        "EPA-HQ-OAR-2099-0001": Phase.COUNTED,
        "EPA-HQ-OLEM-2099-0003": Phase.COUNTED,
        "EPA-HQ-OW-2099-0002": Phase.DISCOVERED,
    }
    assert state.ranked() == []
    assert len(api.requests) == 3
