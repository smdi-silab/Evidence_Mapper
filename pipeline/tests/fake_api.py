"""Hand-made fake of the Regulations.gov v4 API for spec 003 tests.

Responses follow the shapes confirmed live in T1 (tasks.md, Verification results): `data`
items with `id` and `attributes`, and `meta` with `totalElements`, `totalPages`, `hasNextPage`,
`pageNumber`, `numberOfElements`. Real responses aren't recorded, because comment responses
carry comment text and personal data that must not be committed.

All docket IDs use the year 2099 so they can't be confused with real dockets. Comment text,
comment titles, submitter names and PDF text contain SENTINEL strings, so tests can check that
none of them leak into outputs or logs.
"""

import math
from dataclasses import dataclass, field
from typing import Any

import httpx

SENTINEL_COMMENT_TEXT = "SENTINEL-COMMENT-TEXT-b41e we oppose this rule because"
SENTINEL_COMMENT_TITLE = "SENTINEL-COMMENT-TITLE Comment from Jane Sentineldoe"
SENTINEL_NAME = "Sentineldoe"


@dataclass
class FakeDoc:
    id: str
    document_type: str
    title: str
    posted_date: str = "2023-05-01T04:00:00Z"
    subtype: str | None = None


@dataclass
class FakeAttachment:
    file_formats: list[dict[str, Any]] | None
    restricted: bool = False


@dataclass
class FakeComment:
    id: str
    attachments: list[FakeAttachment] = field(default_factory=list)
    duplicate_comments: int = 0


@dataclass
class FakeDocket:
    id: str
    title: str
    documents: list[FakeDoc]
    comment_count: int
    comments: dict[str, FakeComment] = field(default_factory=dict)

    def comment_ids(self) -> list[str]:
        return [f"{self.id}-{n:04d}" for n in range(1, self.comment_count + 1)]


def _page(items: list[dict[str, Any]], size: int, number: int) -> dict[str, Any]:
    total = len(items)
    pages = max(1, math.ceil(total / size)) if size else 1
    chunk = items[(number - 1) * size : number * size]
    return {
        "data": chunk,
        "meta": {
            "totalElements": total,
            "totalPages": pages,
            "pageNumber": number,
            "pageSize": size,
            "numberOfElements": len(chunk),
            "hasNextPage": number < pages,
            "hasPreviousPage": number > 1,
            "firstPage": number == 1,
            "lastPage": number >= pages,
        },
    }


def _doc_json(docket_id: str, doc: FakeDoc) -> dict[str, Any]:
    return {
        "id": doc.id,
        "type": "documents",
        "attributes": {
            "agencyId": "EPA",
            "docketId": docket_id,
            "documentType": doc.document_type,
            "title": doc.title,
            "postedDate": doc.posted_date,
            "subtype": doc.subtype,
            "withdrawn": False,
        },
    }


class FakeRegulationsGov:
    """An `httpx` handler that serves the fake dockets and records every request."""

    def __init__(self, dockets: list[FakeDocket]) -> None:
        self.dockets = {d.id: d for d in dockets}
        self.requests: list[httpx.Request] = []

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.removeprefix("/v4")
        q = request.url.params
        size = int(q.get("page[size]", "25"))
        number = int(q.get("page[number]", "1"))
        headers = {"X-Ratelimit-Limit": "1000", "X-Ratelimit-Remaining": "900"}

        if path == "/documents" and "filter[docketId]" in q:
            docket = self.dockets.get(q["filter[docketId]"])
            docs = [_doc_json(docket.id, d) for d in docket.documents] if docket else []
            return httpx.Response(200, json=_page(docs, size, number), headers=headers)

        if path == "/documents":
            assert q.get("filter[agencyId]") == "EPA"
            assert q.get("filter[documentType]") == "Rule"
            lo, hi = q["filter[postedDate][ge]"], q["filter[postedDate][le]"]
            rules = [
                _doc_json(d.id, doc)
                for d in self.dockets.values()
                for doc in d.documents
                if doc.document_type == "Rule" and lo <= doc.posted_date[:10] <= hi
            ]
            rules.sort(key=lambda r: r["id"])
            return httpx.Response(200, json=_page(rules, size, number), headers=headers)

        if path == "/comments":
            docket = self.dockets.get(q["filter[docketId]"])
            ids = docket.comment_ids() if docket else []
            items = [
                {
                    "id": cid,
                    "type": "comments",
                    "attributes": {
                        "title": SENTINEL_COMMENT_TITLE,
                        "documentType": "Public Submission",
                    },
                }
                for cid in ids
            ]
            return httpx.Response(200, json=_page(items, size, number), headers=headers)

        if path.startswith("/comments/"):
            return self._comment(path.removeprefix("/comments/"), headers)

        if path.startswith("/dockets/"):
            docket = self.dockets.get(path.removeprefix("/dockets/"))
            if docket is None:
                return httpx.Response(404, json={"errors": [{"status": "404"}]})
            body = {
                "data": {"id": docket.id, "type": "dockets", "attributes": {"title": docket.title}}
            }
            return httpx.Response(200, json=body, headers=headers)

        return httpx.Response(404, json={"errors": [{"status": "404"}]})

    def _comment(self, comment_id: str, headers: dict[str, str]) -> httpx.Response:
        docket_id = comment_id.rsplit("-", 1)[0]
        docket = self.dockets.get(docket_id)
        if docket is None or comment_id not in docket.comment_ids():
            return httpx.Response(404, json={"errors": [{"status": "404"}]})
        comment = docket.comments.get(comment_id, FakeComment(comment_id))
        included = []
        for n, att in enumerate(comment.attachments, start=1):
            included.append(
                {
                    "id": f"{comment_id}-A{n}",
                    "type": "attachments",
                    "attributes": {
                        "title": f"{SENTINEL_COMMENT_TITLE} attachment {n}",
                        "fileFormats": att.file_formats,
                        "restrictReasonType": "Other" if att.restricted else None,
                    },
                }
            )
        body = {
            "data": {
                "id": comment_id,
                "type": "comments",
                "attributes": {
                    "docketId": docket_id,
                    "comment": SENTINEL_COMMENT_TEXT,
                    "title": SENTINEL_COMMENT_TITLE,
                    "firstName": "Jane",
                    "lastName": SENTINEL_NAME,
                    "email": "jane@sentinel.example",
                    "duplicateComments": comment.duplicate_comments,
                    "fileFormats": [],
                },
                "relationships": {"attachments": {"data": []}},
            },
            "included": included,
        }
        return httpx.Response(200, json=body, headers=headers)


def pdf_format(docket_id: str, comment_n: int, att_n: int, size: int = 50_000) -> dict[str, Any]:
    return {
        "fileUrl": f"https://downloads.regulations.gov/{docket_id}-{comment_n:04d}/attachment_{att_n}.pdf",
        "format": "pdf",
        "size": size,
    }


def standard_dockets() -> list[FakeDocket]:
    """Fixture dockets for the shortlist tests (AC-1, AC-2, AC-5, AC-7).

    - OAR-0001: 450 comments, final rule, RTC document -> rank 1.
    - OW-0002: 620 comments, final rule, no RTC -> rank 2.
    - OLEM-0003: 120 comments -> out of range.
    - R05-0004: "Air Plan Approval" title -> excluded by title.
    - OPP-0005: only a Correction -> excluded by subtype.
    - OAR-0006: final rule posted outside the date range -> never discovered.
    """
    return [
        FakeDocket(
            id="EPA-HQ-OAR-2099-0001",
            title="Fake Emission Standards for Widget Manufacturing",
            comment_count=450,
            documents=[
                FakeDoc(
                    "EPA-HQ-OAR-2099-0001-0001",
                    "Proposed Rule",
                    "Fake Emission Standards; Proposed Rule",
                    "2022-03-01T05:00:00Z",
                ),
                FakeDoc(
                    "EPA-HQ-OAR-2099-0001-0900",
                    "Rule",
                    "Fake Emission Standards; Final Rule",
                    "2023-09-15T04:00:00Z",
                    "Final Rule",
                ),
                FakeDoc(
                    "EPA-HQ-OAR-2099-0001-0901",
                    "Supporting & Related Material",
                    "Response to Comments Document for the Final Rule",
                    "2023-09-15T04:00:00Z",
                ),
                FakeDoc(
                    "EPA-HQ-OAR-2099-0001-0902",
                    "Supporting & Related Material",
                    "Regulatory Impact Analysis",
                    "2023-09-15T04:00:00Z",
                ),
            ],
        ),
        FakeDocket(
            id="EPA-HQ-OW-2099-0002",
            title="Fake Effluent Guidelines for Gadget Plants",
            comment_count=620,
            documents=[
                FakeDoc(
                    "EPA-HQ-OW-2099-0002-0001",
                    "Proposed Rule",
                    "Fake Effluent Guidelines; Proposed Rule",
                    "2022-06-01T04:00:00Z",
                ),
                FakeDoc(
                    "EPA-HQ-OW-2099-0002-0700",
                    "Rule",
                    "Fake Effluent Guidelines; Final Rule",
                    "2024-02-20T05:00:00Z",
                    "Final Rule",
                ),
                FakeDoc(
                    "EPA-HQ-OW-2099-0002-0701",
                    "Supporting & Related Material",
                    "Technical Development Document",
                    "2024-02-20T05:00:00Z",
                ),
            ],
        ),
        FakeDocket(
            id="EPA-HQ-OLEM-2099-0003",
            title="Fake Waste Rule With Few Comments",
            comment_count=120,
            documents=[
                FakeDoc(
                    "EPA-HQ-OLEM-2099-0003-0100",
                    "Rule",
                    "Fake Waste Rule; Final Rule",
                    "2023-01-10T05:00:00Z",
                ),
                FakeDoc(
                    "EPA-HQ-OLEM-2099-0003-0101",
                    "Supporting & Related Material",
                    "Summary of Public Comments and Responses",
                    "2023-01-10T05:00:00Z",
                ),
            ],
        ),
        FakeDocket(
            id="EPA-R05-OAR-2099-0004",
            title="Air Plan Approval; Ohio; Fake SIP",
            comment_count=500,
            documents=[
                FakeDoc(
                    "EPA-R05-OAR-2099-0004-0010",
                    "Rule",
                    "Air Plan Approval; Ohio; Fake SIP",
                    "2023-04-04T04:00:00Z",
                ),
            ],
        ),
        FakeDocket(
            id="EPA-HQ-OPP-2099-0005",
            title="Fake Pesticide Registration Rule",
            comment_count=700,
            documents=[
                FakeDoc(
                    "EPA-HQ-OPP-2099-0005-0020",
                    "Rule",
                    "Fake Rule; Correction",
                    "2023-07-07T04:00:00Z",
                    "Correction",
                ),
            ],
        ),
        FakeDocket(
            id="EPA-HQ-OAR-2099-0006",
            title="Fake Rule Finalized Too Early",
            comment_count=400,
            documents=[
                FakeDoc(
                    "EPA-HQ-OAR-2099-0006-0050",
                    "Rule",
                    "Fake Old Rule; Final Rule",
                    "2021-06-01T04:00:00Z",
                    "Final Rule",
                ),
            ],
        ),
    ]
