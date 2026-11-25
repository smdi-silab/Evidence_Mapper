"""Tests for shortlist phase 4: comment sample, attachments and text layer (spec 003: FR-4,
FR-5). Hand-made fixtures, no network. PDFs are built at run time."""

import json
from pathlib import Path

import httpx
import pymupdf
from fake_api import (
    SENTINEL_COMMENT_TEXT,
    SENTINEL_COMMENT_TITLE,
    SENTINEL_NAME,
    FakeAttachment,
    FakeComment,
    FakeDoc,
    FakeDocket,
    FakeRegulationsGov,
    pdf_format,
    standard_dockets,
)

from evidence_mapper.acquisition.pdf_text import TextLayerStore
from evidence_mapper.acquisition.regulations_gov import (
    DownloadClient,
    RegulationsGovClient,
    RequestBudget,
    ResponseCache,
    Throttle,
)
from evidence_mapper.acquisition.shortlist import (
    Phase,
    ShortlistOptions,
    ShortlistState,
    run_shortlist,
)

FAKE_KEY = "FAKE-KEY-sample-0001"
PDF_SENTINEL = "SENTINEL-ATTACHMENT-TEXT-c2d8 the commenter supplies data showing"
SMALL = "EPA-HQ-OAR-2099-0010"


def pdf_bytes(pages: list[str | None]) -> bytes:
    doc = pymupdf.open()
    for content in pages:
        page = doc.new_page()
        if content is None:
            page.draw_rect(pymupdf.Rect(50, 50, 300, 300), color=(0, 0, 0), fill=(0.5, 0.5, 0.5))
        else:
            page.insert_text((72, 72), content)
    data = doc.tobytes()
    doc.close()
    return data


class FakeDownloads:
    """Serves PDFs by URL and records every request."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = files
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        body = self.files.get(str(request.url))
        if body is None:
            return httpx.Response(404)
        return httpx.Response(200, content=body)


def small_docket() -> tuple[FakeDocket, dict[str, bytes]]:
    """Six comments, all sampled with `sample_comments=6`:

    1. a PDF with two text pages, also offered as DOCX
    2. a scanned PDF (one page, no text)
    3. a restricted attachment with no file formats (as seen in T1)
    4. no attachments, 40 duplicate comments
    5. a PDF whose declared size is over the cap
    6. served as HTTP 500 by the test handler (fails after retries)
    """
    d = SMALL
    text_pdf = pdf_format(d, 1, 1)
    docx = {**pdf_format(d, 1, 1), "format": "docx"}
    docx["fileUrl"] = docx["fileUrl"].removesuffix(".pdf") + ".docx"
    scanned_pdf = pdf_format(d, 2, 1)
    big_pdf = pdf_format(d, 5, 1, size=30 * 1024 * 1024)
    comments = {
        f"{d}-0001": FakeComment(f"{d}-0001", [FakeAttachment([text_pdf, docx])]),
        f"{d}-0002": FakeComment(f"{d}-0002", [FakeAttachment([scanned_pdf])]),
        f"{d}-0003": FakeComment(f"{d}-0003", [FakeAttachment(None, restricted=True)]),
        f"{d}-0004": FakeComment(f"{d}-0004", duplicate_comments=40),
        f"{d}-0005": FakeComment(f"{d}-0005", [FakeAttachment([big_pdf])]),
    }
    docket = FakeDocket(
        id=d,
        title="Fake Small Docket",
        comment_count=6,
        comments=comments,
        documents=[
            FakeDoc(f"{d}-0100", "Rule", "Fake Small Rule; Final Rule", "2023-03-03T05:00:00Z"),
        ],
    )
    files = {
        text_pdf["fileUrl"]: pdf_bytes([PDF_SENTINEL, PDF_SENTINEL]),
        scanned_pdf["fileUrl"]: pdf_bytes([None]),
        big_pdf["fileUrl"]: pdf_bytes([PDF_SENTINEL]),
    }
    return docket, files


class Env:
    """Clients, cache and store for one run. A second `Env` on the same `tmp_path` is a rerun."""

    def __init__(
        self,
        tmp_path: Path,
        api: FakeRegulationsGov,
        downloads: FakeDownloads,
        *,
        budget: int = 1_000,
        fail_comment: str | None = None,
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if fail_comment and request.url.path.endswith(f"/comments/{fail_comment}"):
                api.requests.append(request)
                return httpx.Response(500)
            return api(request)

        self.client = RegulationsGovClient(
            FAKE_KEY,
            ResponseCache(tmp_path / "cache"),
            RequestBudget(budget),
            Throttle(0.0, sleep=lambda s: None),
            transport=httpx.MockTransport(handler),
            retry_backoff=0.0,
        )
        self.downloader = DownloadClient(
            Throttle(0.0, sleep=lambda s: None), transport=httpx.MockTransport(downloads)
        )
        self.store = TextLayerStore(tmp_path / "attachments" / "results.json")
        self.work_dir = tmp_path / "attachments"

    def run(self, **opts: object) -> ShortlistState:
        state = ShortlistState(options=ShortlistOptions(**opts))  # type: ignore[arg-type]
        run_shortlist(self.client, self.downloader, self.store, self.work_dir, state)
        return state


SMALL_OPTS: dict[str, object] = {"min_comments": 1, "max_comments": 10, "sample_comments": 6}


def test_small_docket_figures(tmp_path: Path) -> None:
    docket, files = small_docket()
    env = Env(
        tmp_path, FakeRegulationsGov([docket]), FakeDownloads(files), fail_comment=f"{SMALL}-0006"
    )
    state = env.run(**SMALL_OPTS)
    row = state.rows[SMALL]
    assert row.phase_completed == Phase.SAMPLED
    s = row.sample
    assert s is not None
    assert s.comment_ids_listed == 6
    assert s.sampled_comments == 6
    assert s.comments_fetched == 5
    assert s.comments_failed == 1
    assert s.comments_with_attachments == 4
    assert s.share_with_attachments == 0.8
    assert s.comments_with_download_links == 3
    assert s.share_with_download_links == 0.6
    assert s.attachments == 4
    assert s.attachment_formats == {"docx": 1, "pdf": 3}
    assert s.restricted_attachments == 1
    assert s.downloadable_attachments == 3
    assert s.sampled_duplicate_comments == 40

    tl = s.text_layer
    assert tl.pdf_attachments == 3
    assert tl.pdfs_over_size_cap == 1
    assert tl.pdfs_selected == 2
    assert tl.pdfs_measured == 2
    assert tl.pdfs_not_measured == {}
    assert (tl.pages_with_text, tl.pages) == (2, 3)
    assert tl.pdfs_mostly_text == 1
    assert tl.pdfs_mostly_text_share == 0.5
    assert tl.text_min_chars == 20
    assert state.stop_reason is None


def test_downloads_never_send_key_and_pdfs_are_deleted(tmp_path: Path) -> None:
    docket, files = small_docket()
    downloads = FakeDownloads(files)
    Env(tmp_path, FakeRegulationsGov([docket]), downloads).run(**SMALL_OPTS)
    assert len(downloads.requests) == 2  # the over-cap PDF is never downloaded
    assert all("x-api-key" not in r.headers for r in downloads.requests)
    assert list((tmp_path / "attachments").rglob("*.pdf")) == []
    assert len(json.loads((tmp_path / "attachments" / "results.json").read_text())) == 2


def test_pdf_size_cap_is_configurable(tmp_path: Path) -> None:
    docket, files = small_docket()
    state = Env(tmp_path, FakeRegulationsGov([docket]), FakeDownloads(files)).run(
        **SMALL_OPTS, max_pdf_mb=40
    )
    tl = state.rows[SMALL].sample.text_layer  # type: ignore[union-attr]
    assert tl.pdfs_over_size_cap == 0
    assert tl.pdfs_measured == 3


def test_sample_pdfs_limits_downloads(tmp_path: Path) -> None:
    docket, files = small_docket()
    downloads = FakeDownloads(files)
    state = Env(tmp_path, FakeRegulationsGov([docket]), downloads).run(**SMALL_OPTS, sample_pdfs=1)
    assert state.rows[SMALL].sample.text_layer.pdfs_selected == 1  # type: ignore[union-attr]
    assert len(downloads.requests) == 1


def test_failed_download_is_reported_not_measured(tmp_path: Path) -> None:
    docket, files = small_docket()
    files.pop(pdf_format(SMALL, 2, 1)["fileUrl"])  # the scanned PDF now returns 404
    state = Env(tmp_path, FakeRegulationsGov([docket]), FakeDownloads(files)).run(**SMALL_OPTS)
    tl = state.rows[SMALL].sample.text_layer  # type: ignore[union-attr]
    assert tl.pdfs_measured == 1
    assert tl.pdfs_not_measured == {"download_failed": 1}


def test_rerun_makes_no_repeat_requests_or_downloads(tmp_path: Path) -> None:
    docket, files = small_docket()
    api, downloads = FakeRegulationsGov([docket]), FakeDownloads(files)
    first = Env(tmp_path, api, downloads).run(**SMALL_OPTS)
    n_api, n_dl = len(api.requests), len(downloads.requests)
    second = Env(tmp_path, api, downloads).run(**SMALL_OPTS)
    assert (len(api.requests), len(downloads.requests)) == (n_api, n_dl)
    assert second.rows[SMALL].sample == first.rows[SMALL].sample


def test_only_top_n_are_sampled_with_seeded_sample(tmp_path: Path) -> None:
    api = FakeRegulationsGov(standard_dockets())
    state = Env(tmp_path / "a", api, FakeDownloads({})).run(top=1)
    top = state.rows["EPA-HQ-OAR-2099-0001"]
    assert top.phase_completed == Phase.SAMPLED
    assert state.rows["EPA-HQ-OW-2099-0002"].phase_completed == Phase.DOCUMENTS
    assert state.rows["EPA-HQ-OW-2099-0002"].sample is None
    assert top.sample is not None
    ids = top.sample.sampled_comment_ids
    assert len(ids) == 30 and len(set(ids)) == 30
    assert top.sample.comment_ids_listed == 450
    assert all(i.startswith("EPA-HQ-OAR-2099-0001-") for i in ids)
    # Comment listing at 250 per page: 2 pages, then one request per sampled comment.
    comment_requests = [r for r in api.requests if r.url.path.startswith("/v4/comments/")]
    assert len(comment_requests) == 30

    same = Env(tmp_path / "b", FakeRegulationsGov(standard_dockets()), FakeDownloads({})).run(top=1)
    other = Env(tmp_path / "c", FakeRegulationsGov(standard_dockets()), FakeDownloads({})).run(
        top=1, seed=7
    )
    assert same.rows["EPA-HQ-OAR-2099-0001"].sample.sampled_comment_ids == ids  # type: ignore[union-attr]
    assert other.rows["EPA-HQ-OAR-2099-0001"].sample.sampled_comment_ids != ids  # type: ignore[union-attr]


def test_budget_stop_in_phase_4_records_nothing_then_resumes(tmp_path: Path) -> None:
    docket, files = small_docket()
    api = FakeRegulationsGov([docket])
    # Phases 1-3: 1 discovery + 1 count + 2 documents = 4; phase 4: 1 listing + 6 comments.
    first = Env(tmp_path, api, FakeDownloads(files), budget=7).run(**SMALL_OPTS)
    assert first.stop_reason == "request budget spent"
    assert first.rows[SMALL].phase_completed == Phase.DOCUMENTS
    assert first.rows[SMALL].sample is None
    assert len(api.requests) == 7

    second = Env(tmp_path, api, FakeDownloads(files)).run(**SMALL_OPTS)
    assert second.rows[SMALL].phase_completed == Phase.SAMPLED
    urls = [str(r.url) for r in api.requests]
    assert len(urls) == len(set(urls)) == 11


def test_phase_4_skipped_when_phases_1_to_3_stop_early(tmp_path: Path) -> None:
    docket, files = small_docket()
    api = FakeRegulationsGov([docket])
    state = Env(tmp_path, api, FakeDownloads(files), budget=3).run(**SMALL_OPTS)
    assert state.stopped_early
    assert len(api.requests) == 3
    assert not any(r.url.path.startswith("/v4/comments/") for r in api.requests)


def test_sample_holds_no_comment_text_titles_or_names(tmp_path: Path) -> None:
    docket, files = small_docket()
    state = Env(tmp_path, FakeRegulationsGov([docket]), FakeDownloads(files)).run(**SMALL_OPTS)
    dumped = state.rows[SMALL].model_dump_json()
    for sentinel in (SENTINEL_COMMENT_TEXT, SENTINEL_COMMENT_TITLE, SENTINEL_NAME, PDF_SENTINEL):
        assert sentinel not in dumped
    assert "share_with_attachments" in dumped  # computed fields are serialized
