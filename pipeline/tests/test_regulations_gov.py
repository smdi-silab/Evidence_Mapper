"""Tests for the Regulations.gov client (spec 003: FR-6, FR-7, AC-3, AC-4). No network."""

import hashlib
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from evidence_mapper.acquisition.regulations_gov import (
    ApiError,
    BudgetExhausted,
    DownloadClient,
    DownloadError,
    DownloadTooLarge,
    NotFoundError,
    RateLimitReserveReached,
    RateLimitStop,
    RegulationsGovClient,
    RequestBudget,
    ResponseCache,
    Throttle,
)

FAKE_KEY = "FAKE-KEY-0123456789abcdef"
Handler = Callable[[httpx.Request], httpx.Response]


class FakeClock:
    """Monotonic clock whose sleep advances time instead of waiting."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class Recorder:
    """MockTransport handler that records every outgoing request."""

    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.handler(request)

    @property
    def urls(self) -> list[str]:
        return [str(r.url) for r in self.requests]


def ok(body: dict | None = None, remaining: int = 900) -> httpx.Response:
    return httpx.Response(
        200, json=body or {"data": []}, headers={"X-Ratelimit-Remaining": str(remaining)}
    )


def make_client(
    tmp_path: Path,
    handler: Handler,
    *,
    budget: int = 100,
    clock: FakeClock | None = None,
    **kwargs: object,
) -> tuple[RegulationsGovClient, Recorder, FakeClock]:
    clock = clock or FakeClock()
    recorder = handler if isinstance(handler, Recorder) else Recorder(handler)
    client = RegulationsGovClient(
        FAKE_KEY,
        ResponseCache(tmp_path / "cache"),
        RequestBudget(budget),
        Throttle(4.0, clock=clock.clock, sleep=clock.sleep),
        transport=httpx.MockTransport(recorder),
        **kwargs,  # type: ignore[arg-type]
    )
    return client, recorder, clock


def cache_files(tmp_path: Path) -> list[Path]:
    return list((tmp_path / "cache").rglob("*.json")) if (tmp_path / "cache").exists() else []


def test_key_sent_in_header_never_in_url(tmp_path: Path) -> None:
    client, rec, _ = make_client(tmp_path, lambda r: ok())
    client.get_json("/documents", {"filter[agencyId]": "EPA"})
    request = rec.requests[0]
    assert request.method == "GET"
    assert request.headers["X-Api-Key"] == FAKE_KEY
    assert FAKE_KEY not in str(request.url)
    assert request.url.host == "api.regulations.gov"


def test_key_not_written_to_cache(tmp_path: Path) -> None:
    client, _, _ = make_client(tmp_path, lambda r: ok({"data": [{"id": "X"}]}))
    client.get_json("/documents", {"filter[docketId]": "EPA-1"})
    for file in cache_files(tmp_path):
        assert FAKE_KEY not in file.read_text()


def test_throttle_spaces_requests(tmp_path: Path) -> None:
    client, _, clock = make_client(tmp_path, lambda r: ok())
    client.get_json("/a")
    client.get_json("/b")
    assert clock.sleeps == [4.0]


def test_cache_key_ignores_param_order() -> None:
    assert ResponseCache.key("/c", {"a": "1", "b": "2"}) == ResponseCache.key(
        "/c", {"b": "2", "a": "1"}
    )


def test_cache_hit_makes_no_request_and_costs_no_budget(tmp_path: Path) -> None:
    client, rec, _ = make_client(tmp_path, lambda r: ok({"data": [1]}), budget=1)
    first = client.get_json("/a", {"x": "1"})
    second = client.get_json("/a", {"x": "1"})
    assert first == second == {"data": [1]}
    assert len(rec.requests) == 1
    assert client.budget.used == 1
    assert client.stats.cache_hits == 1


def test_ac3_429_stop_not_cached(tmp_path: Path) -> None:
    """AC-3: with on_rate_limit=stop, a 429 stops the run and is never cached or returned."""
    client, rec, _ = make_client(
        tmp_path, lambda r: httpx.Response(429, json={"error": "OVER_RATE_LIMIT"})
    )
    with pytest.raises(RateLimitStop):
        client.get_json("/documents")
    assert len(rec.requests) == 1
    assert cache_files(tmp_path) == []
    assert client.stats.status_counts[429] == 1


def test_ac3_429_wait_then_success(tmp_path: Path) -> None:
    """AC-3: with on_rate_limit=wait, the client waits Retry-After and uses only the 200."""
    responses = iter(
        [
            httpx.Response(429, json={"error": "OVER_RATE_LIMIT"}, headers={"Retry-After": "7"}),
            ok({"data": ["good"]}),
        ]
    )
    client, rec, clock = make_client(tmp_path, lambda r: next(responses), on_rate_limit="wait")
    body = client.get_json("/documents")
    assert body == {"data": ["good"]}
    assert 7.0 in clock.sleeps
    assert len(rec.requests) == 2
    assert client.stats.rate_limit_waits == 1
    cached = cache_files(tmp_path)
    assert len(cached) == 1
    assert "OVER_RATE_LIMIT" not in cached[0].read_text()


def test_ac3_429_wait_gives_up_after_max_waits(tmp_path: Path) -> None:
    client, rec, _ = make_client(
        tmp_path,
        lambda r: httpx.Response(429),
        on_rate_limit="wait",
        max_rate_limit_waits=2,
        default_retry_after=30.0,
    )
    with pytest.raises(RateLimitStop):
        client.get_json("/documents")
    assert len(rec.requests) == 3
    assert cache_files(tmp_path) == []


def test_ac4_rerun_makes_no_repeat_requests(tmp_path: Path) -> None:
    """AC-4: a run interrupted part-way, when rerun, repeats no request already cached."""
    paths = ["/a", "/b", "/c", "/d"]
    rec = Recorder(lambda r: ok({"path": r.url.path}))

    first, _, _ = make_client(tmp_path, rec, budget=2)
    with pytest.raises(BudgetExhausted):
        for path in paths:
            first.get_json(path, {"page[size]": "250"})
    assert len(rec.requests) == 2

    second, _, _ = make_client(tmp_path, rec, budget=100)
    results = [second.get_json(path, {"page[size]": "250"}) for path in paths]

    assert len(rec.requests) == 4
    assert len(set(rec.urls)) == len(rec.urls), "a request was repeated"
    assert second.stats.cache_hits == 2
    assert second.stats.requests == 2
    assert [r["path"] for r in results] == ["/v4/a", "/v4/b", "/v4/c", "/v4/d"]


def test_budget_caps_network_requests_including_retries(tmp_path: Path) -> None:
    client, rec, _ = make_client(tmp_path, lambda r: httpx.Response(503), budget=2)
    with pytest.raises(BudgetExhausted):
        client.get_json("/a")
    assert len(rec.requests) == 2
    assert client.budget.used == 2


def test_5xx_retried_then_api_error(tmp_path: Path) -> None:
    client, rec, _ = make_client(tmp_path, lambda r: httpx.Response(502), max_retries=2)
    with pytest.raises(ApiError) as err:
        client.get_json("/a")
    assert err.value.status == 502
    assert len(rec.requests) == 3


def test_5xx_then_success(tmp_path: Path) -> None:
    responses = iter([httpx.Response(500), ok({"data": ["x"]})])
    client, rec, _ = make_client(tmp_path, lambda r: next(responses))
    assert client.get_json("/a") == {"data": ["x"]}
    assert client.stats.retries == 1


def test_transport_error_retried(tmp_path: Path) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectTimeout("timeout", request=request)
        return ok({"data": ["x"]})

    client, _, _ = make_client(tmp_path, handler)
    assert client.get_json("/a") == {"data": ["x"]}
    assert client.budget.used == 2


def test_404_raises_not_found(tmp_path: Path) -> None:
    client, _, _ = make_client(tmp_path, lambda r: httpx.Response(404))
    with pytest.raises(NotFoundError):
        client.get_json("/comments/X")


def test_other_4xx_raises_without_retry(tmp_path: Path) -> None:
    client, rec, _ = make_client(tmp_path, lambda r: httpx.Response(400))
    with pytest.raises(ApiError):
        client.get_json("/a")
    assert len(rec.requests) == 1


def test_rate_limit_reserve_stops_before_next_request(tmp_path: Path) -> None:
    client, rec, _ = make_client(tmp_path, lambda r: ok(remaining=25), rate_limit_reserve=25)
    client.get_json("/a")
    with pytest.raises(RateLimitReserveReached):
        client.get_json("/b")
    assert len(rec.requests) == 1
    # Cached data is still served after the reserve is reached.
    assert client.get_json("/a") == {"data": []}


def test_secret_key_not_in_logs(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("DEBUG")
    client, _, _ = make_client(tmp_path, lambda r: ok())
    client.get_json("/documents", {"filter[docketId]": "EPA-1"})
    assert caplog.records
    assert FAKE_KEY not in caplog.text


# Download client


def make_downloader(handler: Handler) -> tuple[DownloadClient, Recorder]:
    clock = FakeClock()
    recorder = Recorder(handler)
    client = DownloadClient(
        Throttle(4.0, clock=clock.clock, sleep=clock.sleep),
        transport=httpx.MockTransport(recorder),
    )
    return client, recorder


PDF_URL = "https://downloads.regulations.gov/EPA-1-0001/attachment_1.pdf"


def test_download_client_sends_no_api_key(tmp_path: Path) -> None:
    content = b"%PDF-1.7 fake"
    downloader, rec = make_downloader(lambda r: httpx.Response(200, content=content))
    result = downloader.download(PDF_URL, tmp_path / "a.pdf", max_bytes=1_000)
    request = rec.requests[0]
    assert "x-api-key" not in {k.lower() for k in request.headers}
    assert FAKE_KEY not in str(request.url)
    assert result.size == len(content)
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert (tmp_path / "a.pdf").read_bytes() == content
    assert downloader.count == 1


def test_download_refuses_other_hosts(tmp_path: Path) -> None:
    downloader, rec = make_downloader(lambda r: httpx.Response(200, content=b"x"))
    for url in ["https://example.com/a.pdf", "http://downloads.regulations.gov/a.pdf"]:
        with pytest.raises(DownloadError):
            downloader.download(url, tmp_path / "a.pdf", max_bytes=1_000)
    assert rec.requests == []


def test_download_too_large_leaves_no_file(tmp_path: Path) -> None:
    downloader, _ = make_downloader(lambda r: httpx.Response(200, content=b"x" * 2_000))
    with pytest.raises(DownloadTooLarge):
        downloader.download(PDF_URL, tmp_path / "a.pdf", max_bytes=1_000)
    assert list(tmp_path.iterdir()) == []


def test_download_error_status(tmp_path: Path) -> None:
    downloader, _ = make_downloader(lambda r: httpx.Response(403))
    with pytest.raises(DownloadError):
        downloader.download(PDF_URL, tmp_path / "a.pdf", max_bytes=1_000)
    assert list(tmp_path.iterdir()) == []
