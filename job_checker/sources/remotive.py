from __future__ import annotations

import requests
from typing import Iterable, List

from ..models import Job


REMOTIVE_API = "https://remotive.com/api/remote-jobs"


def fetch_remotive(keywords: List[str]) -> Iterable[Job]:
    query = "+".join(keywords)
    try:
        resp = requests.get(
            REMOTIVE_API,
            params={"search": query},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    jobs = []
    for item in data.get("jobs", []):
        title = item.get("title") or ""
        company = item.get("company_name") or ""
        location = item.get("candidate_required_location") or (item.get("job_type") or "Remote")
        url = item.get("url") or item.get("job_url") or ""
        desc = item.get("description")
        posted = item.get("publication_date")
        # Heuristic: Remotive includes non-US remote; filter out obvious non-US jobs
        loc_lower = (location or "").lower()
        desc_lower = (desc or "").lower()
        
        # Skip obvious non-US jobs
        if any(country in loc_lower or country in desc_lower for country in [
            "denmark", "sweden", "norway", "finland", "germany", "france", "spain", "italy",
            "netherlands", "belgium", "switzerland", "austria", "poland", "czech", "hungary",
            "romania", "bulgaria", "croatia", "slovenia", "slovakia", "estonia", "latvia",
            "lithuania", "ireland", "portugal", "greece", "cyprus", "malta", "luxembourg",
            "uk", "united kingdom", "england", "scotland", "wales", "northern ireland"
        ]):
            continue
            
        # Skip jobs with obvious non-US city mentions
        if any(city in loc_lower or city in desc_lower for city in [
            "london", "berlin", "paris", "madrid", "rome", "amsterdam", "brussels",
            "zurich", "vienna", "warsaw", "prague", "budapest", "bucharest", "sofia",
            "zagreb", "ljubljana", "bratislava", "tallinn", "riga", "vilnius", "dublin",
            "lisbon", "athens", "nicosia", "valletta", "copenhagen", "stockholm", "oslo",
            "helsinki", "reykjavik", "moscow", "kyiv", "minsk"
        ]):
            continue
        jobs.append(
            Job(
                source="remotive",
                id=str(item.get("id") or url),
                title=title,
                company=company,
                location=location or "Remote",
                url=url,
                description=desc,
                posted_at_iso=posted,
            )
        )
    return jobs


