"""Tests for the text-layer check (spec 003: FR-5, AC-6). PDFs are built at run time."""

from pathlib import Path

import httpx
import pymupdf
import pytest

from evidence_mapper.acquisition.pdf_text import (
    PdfStatus,
    TextLayerStore,
    check_attachment,
    measure_pdf,
)
from evidence_mapper.acquisition.regulations_gov import DownloadClient, Throttle

SENTINEL = "SENTINEL-ATTACHMENT-TEXT-7f3a9c the commenter argues that emissions will rise"
URL = "https://downloads.regulations.gov/EPA-HQ-OAR-2099-0001-0002/attachment_1.pdf"


def pdf_bytes(pages: list[str | None]) -> bytes:
    """One page per item: a string is inserted as text; None draws a shape with no text."""
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


def write_pdf(path: Path, pages: list[str | None]) -> Path:
    path.write_bytes(pdf_bytes(pages))
    return path


def test_ac6_one_text_page_one_without(tmp_path: Path) -> None:
    """AC-6: a PDF with one text page and one image-only page reports 1 of 2 with text."""
    result = measure_pdf(write_pdf(tmp_path / "mixed.pdf", [SENTINEL, None]))
    assert result.status == PdfStatus.MEASURED
    assert result.pages == 2
    assert result.pages_with_text == 1
    assert result.text_share == 0.5


def test_short_text_below_threshold_counts_as_no_text(tmp_path: Path) -> None:
    result = measure_pdf(write_pdf(tmp_path / "stamp.pdf", ["RECEIVED", SENTINEL]), min_chars=20)
    assert result.pages_with_text == 1
    assert result.min_chars == 20


def test_unreadable_file(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"this is not a pdf")
    assert measure_pdf(path).status == PdfStatus.UNREADABLE


def test_encrypted_pdf(tmp_path: Path) -> None:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), SENTINEL)
    path = tmp_path / "locked.pdf"
    doc.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="u", owner_pw="o")
    doc.close()
    assert measure_pdf(path).status == PdfStatus.ENCRYPTED


def make_downloader(content: bytes, status: int = 200) -> tuple[DownloadClient, list[str]]:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(status, content=content)

    throttle = Throttle(0.0, sleep=lambda s: None)
    return DownloadClient(throttle, transport=httpx.MockTransport(handler)), seen


def test_check_attachment_measures_deletes_and_stores(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("DEBUG")
    downloader, seen = make_downloader(pdf_bytes([SENTINEL, None, SENTINEL]))
    store = TextLayerStore(tmp_path / "attachments" / "results.json")
    work = tmp_path / "attachments"

    result = check_attachment(URL, "EPA-HQ-OAR-2099-0001", downloader, store, work, max_bytes=10**7)

    assert (result.pages, result.pages_with_text) == (3, 2)
    assert result.sha256 and result.size_bytes
    assert list(work.rglob("*.pdf")) == [], "PDF must be deleted after measuring"
    results_text = (work / "results.json").read_text()
    assert URL in results_text
    assert "SENTINEL" not in results_text
    assert "SENTINEL" not in caplog.text

    # A rerun with a fresh store reads the stored result and downloads nothing.
    again = check_attachment(
        URL,
        "EPA-HQ-OAR-2099-0001",
        downloader,
        TextLayerStore(work / "results.json"),
        work,
        max_bytes=10**7,
    )
    assert again == result
    assert len(seen) == 1


def test_too_large_is_stored_and_not_retried(tmp_path: Path) -> None:
    downloader, seen = make_downloader(pdf_bytes([SENTINEL]))
    store = TextLayerStore(tmp_path / "results.json")
    for _ in range(2):
        result = check_attachment(URL, "EPA-1", downloader, store, tmp_path, max_bytes=10)
        assert result.status == PdfStatus.TOO_LARGE
        assert result.text_share is None
    assert len(seen) == 1


def test_download_failure_not_stored(tmp_path: Path) -> None:
    downloader, seen = make_downloader(b"", status=503)
    store = TextLayerStore(tmp_path / "results.json")
    result = check_attachment(URL, "EPA-1", downloader, store, tmp_path, max_bytes=10**7)
    assert result.status == PdfStatus.DOWNLOAD_FAILED
    assert store.get(URL) is None
