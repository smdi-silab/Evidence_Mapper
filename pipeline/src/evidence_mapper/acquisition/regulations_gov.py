"""Read-only Regulations.gov v4 API client (spec 003, FR-6, FR-7).

- GET only. The API key goes in the `X-Api-Key` header, only to the API host, never in a URL.
- Every successful (200) response is cached on disk. A cache hit makes no request and does not
  count against the request budget, so a rerun replays finished work for free (AC-4).
- A request budget caps network requests per run. When it is spent, `BudgetExhausted` is raised
  before anything is sent (AC-5).
- HTTP 429 is never cached or returned as data. Depending on configuration the client stops
  (`RateLimitStop`) or waits for `Retry-After` and tries again (AC-3).
- When `X-Ratelimit-Remaining` falls to the reserve, the next network request stops the run.
- Attachment downloads use `DownloadClient`, which never carries the API key.

Logs hold paths (IDs only), status codes, timings and counts (SP-01). Response bodies, which can
contain comment text and personal data, are never logged.
"""

import hashlib
import json
import logging
import os
import time
import urllib.parse
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import httpx

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.regulations.gov/v4"
DOWNLOAD_HOSTS: frozenset[str] = frozenset({"downloads.regulations.gov"})

Params = dict[str, str]
Clock = Callable[[], float]
Sleep = Callable[[float], None]
OnRateLimit = Literal["stop", "wait"]


class ApiStop(Exception):
    """The run must stop cleanly. Results so far are kept; a rerun continues from the cache."""

    reason = "stopped"


class BudgetExhausted(ApiStop):
    reason = "request budget spent"


class RateLimitStop(ApiStop):
    reason = "rate limited (HTTP 429)"


class RateLimitReserveReached(ApiStop):
    reason = "X-Ratelimit-Remaining reached the reserve"


class ApiError(Exception):
    """A request failed in a way that affects one item, not the whole run."""

    def __init__(self, status: int | None, path: str) -> None:
        self.status = status
        self.path = path
        super().__init__(f"request failed: status={status} path={path}")


class NotFoundError(ApiError):
    pass


class DownloadError(Exception):
    """A download was refused or failed. The message holds no URL query or content."""


class DownloadTooLarge(DownloadError):
    pass


@dataclass
class RequestBudget:
    """Counts network requests and refuses to exceed `limit`."""

    limit: int
    used: int = 0

    def take(self) -> None:
        if self.used >= self.limit:
            raise BudgetExhausted()
        self.used += 1

    @property
    def remaining(self) -> int:
        return self.limit - self.used


@dataclass
class Throttle:
    """Keeps at least `min_interval` seconds between the starts of consecutive requests."""

    min_interval: float
    clock: Clock = time.monotonic
    sleep: Sleep = time.sleep
    _last: float | None = None

    def wait(self) -> None:
        if self._last is not None:
            delay = self.min_interval - (self.clock() - self._last)
            if delay > 0:
                self.sleep(delay)
        self._last = self.clock()


def _query_string(params: Params) -> str:
    return urllib.parse.urlencode(sorted(params.items()))


class ResponseCache:
    """Disk cache of successful API responses, keyed by path and sorted query parameters.

    The key never includes the API key. Files are written atomically, so an interrupted run
    can't leave a half-written entry.
    """

    def __init__(self, root: Path) -> None:
        self.root = root

    @staticmethod
    def key(path: str, params: Params) -> str:
        return hashlib.sha256(f"GET {path}?{_query_string(params)}".encode()).hexdigest()

    def _file(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    def get(self, path: str, params: Params) -> dict[str, Any] | None:
        file = self._file(self.key(path, params))
        if not file.exists():
            return None
        entry = json.loads(file.read_text(encoding="utf-8"))
        return entry["body"]

    def put(self, path: str, params: Params, body: dict[str, Any]) -> None:
        file = self._file(self.key(path, params))
        file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "request": f"GET {path}?{_query_string(params)}",
            "status": 200,
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "body": body,
        }
        tmp = file.with_suffix(".tmp")
        tmp.write_text(json.dumps(entry), encoding="utf-8")
        os.replace(tmp, file)


@dataclass
class ClientStats:
    requests: int = 0
    cache_hits: int = 0
    status_counts: Counter[int] = field(default_factory=Counter)
    rate_limit_waits: int = 0
    retries: int = 0
    rate_limit_remaining: int | None = None


class RegulationsGovClient:
    """GET-only client for the Regulations.gov v4 API with cache, budget and throttle."""

    def __init__(
        self,
        api_key: str,
        cache: ResponseCache,
        budget: RequestBudget,
        throttle: Throttle,
        *,
        on_rate_limit: OnRateLimit = "stop",
        rate_limit_reserve: int = 25,
        max_rate_limit_waits: int = 3,
        default_retry_after: float = 60.0,
        max_retries: int = 2,
        retry_backoff: float = 5.0,
        timeout: float = 60.0,
        base_url: str = API_BASE_URL,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is empty")
        self.cache = cache
        self.budget = budget
        self.throttle = throttle
        self.on_rate_limit = on_rate_limit
        self.rate_limit_reserve = rate_limit_reserve
        self.max_rate_limit_waits = max_rate_limit_waits
        self.default_retry_after = default_retry_after
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.stats = ClientStats()
        self._http = httpx.Client(
            base_url=base_url,
            headers={"X-Api-Key": api_key, "Accept": "application/vnd.api+json"},
            timeout=timeout,
            transport=transport,
            follow_redirects=False,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "RegulationsGovClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def get_json(self, path: str, params: Params | None = None) -> dict[str, Any]:
        """Return the JSON body for GET `path`, from the cache if present."""
        params = dict(params or {})
        cached = self.cache.get(path, params)
        if cached is not None:
            self.stats.cache_hits += 1
            return cached

        rate_limit_waits = 0
        failures = 0
        while True:
            self._check_reserve()
            self.budget.take()
            self.throttle.wait()
            start = time.monotonic()
            try:
                response = self._http.get(path, params=params)
            except httpx.TransportError as err:
                self.stats.requests += 1
                logger.warning("GET %s failed: %s", path, type(err).__name__)
                failures += 1
                if failures > self.max_retries:
                    raise ApiError(None, path) from None
                self.stats.retries += 1
                self.throttle.sleep(self.retry_backoff * failures)
                continue

            self.stats.requests += 1
            self.stats.status_counts[response.status_code] += 1
            self._read_remaining(response)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info("GET %s -> %d in %d ms", path, response.status_code, elapsed_ms)

            status = response.status_code
            if status == 200:
                body = response.json()
                self.cache.put(path, params, body)
                return body
            if status == 429:
                if self.on_rate_limit == "wait" and rate_limit_waits < self.max_rate_limit_waits:
                    rate_limit_waits += 1
                    self.stats.rate_limit_waits += 1
                    wait = self._retry_after(response)
                    logger.warning("rate limited; waiting %.0f s", wait)
                    self.throttle.sleep(wait)
                    continue
                raise RateLimitStop()
            if status == 404:
                raise NotFoundError(status, path)
            if status >= 500:
                failures += 1
                if failures > self.max_retries:
                    raise ApiError(status, path)
                self.stats.retries += 1
                self.throttle.sleep(self.retry_backoff * failures)
                continue
            raise ApiError(status, path)

    def _check_reserve(self) -> None:
        remaining = self.stats.rate_limit_remaining
        if remaining is not None and remaining <= self.rate_limit_reserve:
            raise RateLimitReserveReached()

    def _read_remaining(self, response: httpx.Response) -> None:
        value = response.headers.get("X-Ratelimit-Remaining")
        if value is not None and value.strip().isdigit():
            self.stats.rate_limit_remaining = int(value)

    def _retry_after(self, response: httpx.Response) -> float:
        value = response.headers.get("Retry-After", "")
        try:
            return max(0.0, float(value))
        except ValueError:
            return self.default_retry_after


@dataclass(frozen=True)
class Download:
    path: Path
    size: int
    sha256: str


class DownloadClient:
    """Downloads attachment files. Never sends the API key; only allows `DOWNLOAD_HOSTS`."""

    def __init__(
        self,
        throttle: Throttle,
        *,
        allowed_hosts: frozenset[str] = DOWNLOAD_HOSTS,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.throttle = throttle
        self.allowed_hosts = allowed_hosts
        self.count = 0
        self._http = httpx.Client(timeout=timeout, transport=transport, follow_redirects=False)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "DownloadClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def download(self, url: str, dest: Path, max_bytes: int) -> Download:
        """Stream `url` to `dest`. Raise `DownloadTooLarge` past `max_bytes`."""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise DownloadError(f"host not allowed: {parsed.hostname}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        self.throttle.wait()
        self.count += 1
        digest = hashlib.sha256()
        size = 0
        try:
            with self._http.stream("GET", url) as response:
                logger.info("download %s -> %d", parsed.path, response.status_code)
                if response.status_code != 200:
                    raise DownloadError(f"status {response.status_code}")
                declared = response.headers.get("Content-Length")
                if declared and declared.isdigit() and int(declared) > max_bytes:
                    raise DownloadTooLarge(f"declared size {declared} > {max_bytes}")
                with tmp.open("wb") as out:
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > max_bytes:
                            raise DownloadTooLarge(f"size > {max_bytes}")
                        digest.update(chunk)
                        out.write(chunk)
        except httpx.TransportError as err:
            tmp.unlink(missing_ok=True)
            raise DownloadError(type(err).__name__) from None
        except DownloadError:
            tmp.unlink(missing_ok=True)
            raise
        os.replace(tmp, dest)
        return Download(path=dest, size=size, sha256=digest.hexdigest())
