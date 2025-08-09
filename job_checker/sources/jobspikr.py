from __future__ import annotations

import os
from typing import Iterable, List

import requests

from ..models import Job


JOBSPIKR_ENDPOINT = "https://api.jobspikr.com/v3/jobs"


def fetch_jobspikr(keywords: List[str], location_query: str) -> Iterable[Job]:
    api_key = os.getenv("JOBSPIKR_API_KEY")
    if not api_key:
        return []
    try:
        resp = requests.get(
            JOBSPIKR_ENDPOINT,
            headers={"x-api-key": api_key},
            params={
                "q": " ".join(keywords),
                "l": location_query,
                "num": 50,
            },
            timeout=25,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    jobs: List[Job] = []
    for item in data.get("data", []) or []:
        title = item.get("job_title") or ""
        company = item.get("company_name") or ""
        location = item.get("job_location") or ""
        url = item.get("job_url") or ""
        posted = item.get("post_date") or ""
        desc = item.get("job_description") or None
        jobs.append(
            Job(
                source="jobspikr",
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


