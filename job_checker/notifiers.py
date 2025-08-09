from __future__ import annotations

import os
import time
from typing import Iterable
from dateutil import parser as dateparser
import pytz

import requests

from .models import Job


class TelegramNotifier:
    def __init__(self, bot_token: str, core_chat_id: str, stretch_chat_id: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.core_chat_id = core_chat_id
        self.stretch_chat_id = stretch_chat_id

    def _format_message(self, job: Job, scope_tag: str, level_tag: str) -> str:
        title = job.title.strip()
        company = job.company.strip()
        location = job.location.strip()
        url = job.url
        # Format posted time in US Central Time if available
        posted_part = ""
        if job.posted_at_iso:
            try:
                dt = dateparser.parse(job.posted_at_iso)
                if dt is not None:
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=pytz.UTC)
                    ct = pytz.timezone("America/Chicago")
                    dt_ct = dt.astimezone(ct)
                    posted_str = dt_ct.strftime("%b %d, %I:%M %p %Z")
                    posted_part = f" (Posted: {posted_str})"
            except Exception:
                pass
        return f"{scope_tag} {level_tag} {title} — {company} — {location}{posted_part}\n{url}"

    def send(self, jobs: Iterable[Job], scope_tag: str, is_stretch: bool) -> None:
        level_tag = "[STRETCH]" if is_stretch else "[CORE]"
        chat_id = self.stretch_chat_id if is_stretch else self.core_chat_id
        for job in jobs:
            text = self._format_message(job, scope_tag, level_tag)
            try:
                requests.post(
                    self.base_url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "disable_web_page_preview": True,
                    },
                    timeout=10,
                )
            except Exception:
                # Best-effort notifier; ignore transient errors
                time.sleep(0.5)


