from __future__ import annotations

from typing import Iterable, List

import requests

from ..models import Job


GREENHOUSE_BOARD_API = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


def fetch_greenhouse(board_tokens: List[str]) -> Iterable[Job]:
    jobs: List[Job] = []
    for token in board_tokens:
        token = token.strip()
        if not token:
            continue
        try:
            resp = requests.get(
                GREENHOUSE_BOARD_API.format(board_token=token),
                params={"content": "true"},  # include content/metadata when available
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue

        for item in data.get("jobs", []) or []:
            title = item.get("title") or ""
            location = (item.get("location") or {}).get("name") or ""
            url = item.get("absolute_url") or ""
            posted = item.get("updated_at") or item.get("created_at") or ""
            company = token
            jobs.append(
                Job(
                    source="greenhouse",
                    id=str(item.get("id") or url or title),
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    description=None,
                    posted_at_iso=posted,
                )
            )
    return jobs


