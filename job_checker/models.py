from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Job:
    source: str
    id: str
    title: str
    company: str
    location: str
    url: str
    description: Optional[str] = None
    posted_at_iso: Optional[str] = None

    def is_stretch(self) -> bool:
        lowered = self.title.lower()
        for keyword in ("senior", "staff", "principal", "lead"):
            if keyword in lowered:
                return True
        return False


