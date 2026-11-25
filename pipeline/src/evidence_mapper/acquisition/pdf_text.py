"""Text-layer check for sampled PDF attachments (spec 003, FR-5; D-02, DS-04).

A page counts as having a text layer when PyMuPDF extracts at least `TEXT_MIN_CHARS`
non-whitespace characters from it. The threshold is an assumption (plan 003): it stops a scanned
page with a stamped header from counting as text.

Each PDF is downloaded, measured, and deleted. Only the figures (pages, pages with text, size,
SHA-256) are kept, in `results.json`, so a rerun doesn't download it again. While DS-07 is Open,
no attachment copies are kept. Extracted text is counted, never stored or logged.
"""

import hashlib
import json
import logging
import os
from enum import StrEnum
from pathlib import Path

import pymupdf
from pydantic import BaseModel

from evidence_mapper.acquisition.regulations_gov import (
    DownloadClient,
    DownloadError,
    DownloadTooLarge,
)

logger = logging.getLogger(__name__)

TEXT_MIN_CHARS = 20
EXTRACTOR = f"pymupdf {pymupdf.VersionBind}"


class PdfStatus(StrEnum):
    MEASURED = "measured"
    TOO_LARGE = "too_large"
    DOWNLOAD_FAILED = "download_failed"
    UNREADABLE = "unreadable"
    ENCRYPTED = "encrypted"


# Statuses that won't change on a retry, so they are stored and not downloaded again.
FINAL_STATUSES = frozenset(
    {PdfStatus.MEASURED, PdfStatus.TOO_LARGE, PdfStatus.UNREADABLE, PdfStatus.ENCRYPTED}
)


class PdfTextResult(BaseModel):
    status: PdfStatus
    pages: int = 0
    pages_with_text: int = 0
    size_bytes: int | None = None
    sha256: str | None = None
    min_chars: int = TEXT_MIN_CHARS
    extractor: str = EXTRACTOR

    @property
    def text_share(self) -> float | None:
        """Share of pages with a text layer, or None when nothing was measured."""
        if self.status != PdfStatus.MEASURED or self.pages == 0:
            return None
        return self.pages_with_text / self.pages


def _non_whitespace_chars(text: str) -> int:
    return sum(1 for ch in text if not ch.isspace())


def measure_pdf(path: Path, min_chars: int = TEXT_MIN_CHARS) -> PdfTextResult:
    """Count pages, and pages with at least `min_chars` non-whitespace characters of text."""
    try:
        doc = pymupdf.open(path)
    except Exception as err:  # PyMuPDF raises several types for broken files.
        logger.warning("PDF unreadable: %s", type(err).__name__)
        return PdfTextResult(status=PdfStatus.UNREADABLE, min_chars=min_chars)
    with doc:
        if doc.needs_pass:
            return PdfTextResult(status=PdfStatus.ENCRYPTED, min_chars=min_chars)
        pages = 0
        with_text = 0
        try:
            for page in doc:
                pages += 1
                if _non_whitespace_chars(page.get_text()) >= min_chars:
                    with_text += 1
        except Exception as err:
            logger.warning("PDF unreadable at page %d: %s", pages, type(err).__name__)
            return PdfTextResult(status=PdfStatus.UNREADABLE, min_chars=min_chars)
    return PdfTextResult(
        status=PdfStatus.MEASURED, pages=pages, pages_with_text=with_text, min_chars=min_chars
    )


class TextLayerStore:
    """`results.json`: text-layer results keyed by attachment file URL. Figures only."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._results: dict[str, PdfTextResult] = {}
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._results = {url: PdfTextResult.model_validate(r) for url, r in raw.items()}

    def get(self, url: str) -> PdfTextResult | None:
        return self._results.get(url)

    def put(self, url: str, result: PdfTextResult) -> None:
        self._results[url] = result
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        data = {u: r.model_dump(mode="json") for u, r in sorted(self._results.items())}
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)


def check_attachment(
    url: str,
    docket_id: str,
    downloader: DownloadClient,
    store: TextLayerStore,
    work_dir: Path,
    *,
    max_bytes: int,
    min_chars: int = TEXT_MIN_CHARS,
) -> PdfTextResult:
    """Download, measure and delete one PDF, unless its result is already stored."""
    stored = store.get(url)
    if stored is not None:
        return stored

    name = hashlib.sha256(url.encode()).hexdigest()[:24] + ".pdf"
    dest = work_dir / docket_id / name
    try:
        download = downloader.download(url, dest, max_bytes=max_bytes)
    except DownloadTooLarge:
        result = PdfTextResult(status=PdfStatus.TOO_LARGE, min_chars=min_chars)
    except DownloadError as err:
        logger.warning("download failed for docket %s: %s", docket_id, err)
        result = PdfTextResult(status=PdfStatus.DOWNLOAD_FAILED, min_chars=min_chars)
    else:
        try:
            result = measure_pdf(download.path, min_chars).model_copy(
                update={"size_bytes": download.size, "sha256": download.sha256}
            )
        finally:
            download.path.unlink(missing_ok=True)

    logger.info(
        "text layer for docket %s: status=%s pages=%d with_text=%d",
        docket_id,
        result.status,
        result.pages,
        result.pages_with_text,
    )
    if result.status in FINAL_STATUSES:
        store.put(url, result)
    return result
