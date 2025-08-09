from __future__ import annotations

from typing import Iterable, List

import feedparser

from ..models import Job


WWR_CATEGORY_FEEDS = {
    "devops-sysadmin": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "engineering": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
}


def fetch_wwr(categories: List[str]) -> Iterable[Job]:
    jobs = []
    for category in categories:
        feed_url = WWR_CATEGORY_FEEDS.get(category)
        if not feed_url:
            continue
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            continue
        for entry in getattr(feed, "entries", []) or []:
            title = entry.get("title") or ""
            link = entry.get("link") or ""
            summary = entry.get("summary") or entry.get("description") or ""
            company = ""
            if ":" in title:
                parts = title.split(":", 1)
                company = parts[0].strip()
                title = parts[1].strip()
            
            # Filter out obvious non-US jobs
            combined_text = f"{title} {company} {summary}".lower()
            
            # Skip jobs with European country mentions
            if any(country in combined_text for country in [
                "denmark", "sweden", "norway", "finland", "germany", "france", "spain", "italy",
                "netherlands", "belgium", "switzerland", "austria", "poland", "czech", "hungary",
                "romania", "bulgaria", "croatia", "slovenia", "slovakia", "estonia", "latvia",
                "lithuania", "ireland", "portugal", "greece", "cyprus", "malta", "luxembourg",
                "uk", "united kingdom", "england", "scotland", "wales", "northern ireland"
            ]):
                continue
                
            # Skip jobs with obvious non-US city mentions
            if any(city in combined_text for city in [
                "london", "berlin", "paris", "madrid", "rome", "amsterdam", "brussels",
                "zurich", "vienna", "warsaw", "prague", "budapest", "bucharest", "sofia",
                "zagreb", "ljubljana", "bratislava", "tallinn", "riga", "vilnius", "dublin",
                "lisbon", "athens", "nicosia", "valletta", "copenhagen", "stockholm", "oslo",
                "helsinki", "reykjavik", "moscow", "kyiv", "minsk"
            ]):
                continue
            jobs.append(
                Job(
                    source="wwr",
                    id=link,
                    title=title,
                    company=company,
                    location="Remote",
                    url=link,
                    description=summary,
                    posted_at_iso=str(entry.get("published") or entry.get("updated") or ""),
                )
            )
    return jobs


