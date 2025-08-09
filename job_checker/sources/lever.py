from __future__ import annotations

from typing import Iterable, List

import requests

from ..models import Job


LEVER_ENDPOINT = "https://api.lever.co/v0/postings/{company}?mode=json"


def fetch_lever(companies: List[str]) -> Iterable[Job]:
    jobs: List[Job] = []
    for company in companies:
        token = company.strip()
        if not token:
            continue
        try:
            resp = requests.get(LEVER_ENDPOINT.format(company=token), timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue
        for item in data or []:
            title = item.get("text") or item.get("title") or ""
            location = item.get("categories", {}).get("location") or ""
            url = item.get("hostedUrl") or item.get("applyUrl") or ""
            posted = item.get("createdAt") or item.get("listedAt") or ""
            # Lever timestamps are epoch ms; convert to ISO 8601 string
            if isinstance(posted, (int, float)):
                import datetime
                posted = datetime.datetime.utcfromtimestamp(int(posted)/1000).isoformat()+"Z"
            jobs.append(
                Job(
                    source="lever",
                    id=str(item.get("id") or url or title),
                    title=title,
                    company=token,
                    location=location,
                    url=url,
                    description=None,
                    posted_at_iso=str(posted),
                )
            )
    return jobs


