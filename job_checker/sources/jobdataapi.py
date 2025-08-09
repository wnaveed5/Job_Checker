from __future__ import annotations

import os
from typing import Iterable, List

import requests

from ..models import Job


JOBDATAAPI_ENDPOINT = "https://api.jobdataapi.com/v1/jobs/search"


def fetch_jobdataapi(keywords: List[str], location_query: str) -> Iterable[Job]:
    api_key = os.getenv("JOBDATAAPI_KEY")
    if not api_key:
        return []
    try:
        resp = requests.get(
            JOBDATAAPI_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}"},
            params={
                "query": " ".join(keywords),
                "location": location_query,
                "page_size": 50,
            },
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    jobs: List[Job] = []
    for item in data.get("results", []) or []:
        title = item.get("title") or ""
        company = (item.get("company") or {}).get("name") or ""
        location = item.get("location") or ""
        url = item.get("url") or ""
        posted = item.get("published_at") or ""
        desc = item.get("description") or None
        jobs.append(
            Job(
                source="jobdataapi",
                id=url or title,
                title=title,
                company=company,
                location=location,
                url=url,
                description=desc,
                posted_at_iso=posted,
            )
        )
    return jobs


