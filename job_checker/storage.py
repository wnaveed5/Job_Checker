from __future__ import annotations

import hashlib
import os
import sqlite3
from typing import Iterable

from .models import Job


class SeenStore:
    def __init__(self, db_path: str = "job_checker.db") -> None:
        self.db_path = db_path
        self._ensure()

    def _ensure(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen (
                    key TEXT PRIMARY KEY,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    @staticmethod
    def make_key(job: Job) -> str:
        if job.url:
            return hashlib.sha256(job.url.encode("utf-8")).hexdigest()
        composite = f"{job.source}|{job.company.lower()}|{job.title.lower()}|{job.location.lower()}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    def is_new(self, job: Job) -> bool:
        key = self.make_key(job)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT 1 FROM seen WHERE key = ?", (key,))
            row = cur.fetchone()
            return row is None

    def add(self, jobs: Iterable[Job]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO seen (key, url) VALUES (?, ?)",
                [
                    (
                        self.make_key(job),
                        job.url,
                    )
                    for job in jobs
                ],
            )
            conn.commit()


