from __future__ import annotations

import re
from typing import Iterable, List, Tuple
from datetime import datetime, timezone
import calendar
from dateutil import parser as dateparser

from .config import Config
from .models import Job


def title_contains_any(text: str, keywords: List[str]) -> bool:
    lower = text.lower()
    return any(kw.lower() in lower for kw in keywords)


def is_austin_location(text: str, austin_aliases: List[str]) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(alias in lower for alias in austin_aliases)


def is_us_remote(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    
    # Explicit US indicators
    us_tokens = [
        "remote - us",
        "us remote",
        "remote us",
        "united states",
        "usa",
        "u.s.",
        "within the us",
        "eligible to work in the us",
        "us-based",
        "us based",
        "united states only",
        "us only"
    ]
    if any(t in lower for t in us_tokens):
        return True
    
    # Reject non-US locations
    non_us_indicators = [
        "denmark", "copenhagen", "europe", "eu", "emea", "uk", "london", "germany", "berlin",
        "france", "paris", "netherlands", "amsterdam", "sweden", "stockholm", "norway", "oslo",
        "canada", "toronto", "vancouver", "montreal", "australia", "sydney", "melbourne",
        "singapore", "tokyo", "japan", "india", "bangalore", "mumbai", "delhi"
    ]
    if any(indicator in lower for indicator in non_us_indicators):
        return False
    
    # If explicitly mentions EU/EMEA-only, reject as US remote
    if any(t in lower for t in ["emea", "eu only", "europe only", "uk only", "canada only", "australia only"]):
        return False
    
    # Fallback: mention of "remote" without country is ambiguous; allow lower-priority paths to tag it
    return "remote" in lower


def _is_manager_or_sales(title_lower: str, combined_lower: str) -> bool:
    manager_tokens = [
        " manager", "manager ", " manager ", "director", "vp ", "vice president",
    ]
    sales_tokens = [
        "sales", "account executive", "account manager", "partner", "partnership",
        "business development", "bd ", "customer success", "marketing",
    ]
    if any(tok in title_lower for tok in manager_tokens):
        return True
    if any(tok in title_lower for tok in sales_tokens):
        return True
    # Also scan combined text lightly
    if any(phrase in combined_lower for phrase in ["global partner", "alliances", "channel sales"]):
        return True
    return False


def _is_senior_level(title_lower: str, exclude_keywords: List[str]) -> bool:
    # Only exclude when configured via exclude_keywords
    return any(f" {kw} " in f" {title_lower} " for kw in exclude_keywords)

def split_scope(job: Job, cfg: Config) -> Tuple[str, bool]:
    """Return (scope_tag, is_stretch).

    scope_tag is either cfg.telegram.tag_austin or cfg.telegram.tag_us_remote.
    is_stretch uses Job.is_stretch().
    """
    location = job.location or ""
    if is_austin_location(location, cfg.locations.austin_aliases):
        return cfg.telegram.tag_austin, job.is_stretch()
    if is_us_remote(location):
        return cfg.telegram.tag_us_remote, job.is_stretch()
    # Sometimes location text is in description; try it as a fallback
    if job.description:
        desc = job.description
        if is_austin_location(desc, cfg.locations.austin_aliases):
            return cfg.telegram.tag_austin, job.is_stretch()
        if is_us_remote(desc):
            return cfg.telegram.tag_us_remote, job.is_stretch()
    # No scope match - job doesn't fit Austin or US-remote criteria
    return "", job.is_stretch()


def _compute_score(text: str, include_keywords: List[str], bonus_keywords: List[str]) -> int:
    lower = text.lower()
    score = sum(1 for kw in include_keywords if kw.lower() in lower)
    score += sum(1 for kw in bonus_keywords if kw.lower() in lower)
    return score


def apply_keyword_filters(jobs: Iterable[Job], cfg: Config) -> List[Job]:
    results: List[Job] = []
    now = datetime.now(timezone.utc)
    # Adaptive recency: widen on weekends
    max_age_hours = cfg.app.max_post_age_hours
    if getattr(cfg.app, 'adaptive_recency', False):
        weekday = now.weekday()  # 0=Mon .. 6=Sun
        if weekday in (5, 6):  # Sat/Sun
            max_age_hours = getattr(cfg.app, 'weekend_max_post_age_hours', max_age_hours)
        else:
            max_age_hours = getattr(cfg.app, 'weekday_max_post_age_hours', max_age_hours)
    for job in jobs:
        text = f"{job.title} | {job.company} | {job.description or ''}"
        
        # Location filtering - enforce US-only if configured
        if getattr(cfg.locations, 'us_only_remote', False):
            location_text = f"{job.location or ''} {job.description or ''}".lower()
            # Reject non-US locations
            non_us_indicators = [
                "denmark", "copenhagen", "europe", "eu", "emea", "uk", "london", "germany", "berlin",
                "france", "paris", "netherlands", "amsterdam", "sweden", "stockholm", "norway", "oslo",
                "canada", "toronto", "vancouver", "montreal", "australia", "sydney", "melbourne",
                "singapore", "tokyo", "japan", "india", "bangalore", "mumbai", "delhi"
            ]
            if any(indicator in location_text for indicator in non_us_indicators):
                continue
            # Reject if explicitly mentions non-US only
            if any(phrase in location_text for phrase in ["eu only", "europe only", "uk only", "canada only", "australia only"]):
                continue
        
        # Title must include any of these tokens (strict role focus)
        if cfg.filters.title_must_include_any:
            title_lower = job.title.lower()
            if not any(tok.lower() in title_lower for tok in cfg.filters.title_must_include_any):
                continue
        # Company allow/deny
        if cfg.filters.company_whitelist and job.company.lower() not in cfg.filters.company_whitelist:
            continue
        if cfg.filters.company_blacklist and job.company.lower() in cfg.filters.company_blacklist:
            continue

        # Exclude employment types by simple heuristics
        title_lower = job.title.lower()
        combined_lower = text.lower()
        if cfg.filters.exclude_intern and ("intern" in title_lower or "internship" in combined_lower):
            continue
        if cfg.filters.exclude_contract and any(x in combined_lower for x in ["contract", "1099", "c2c"]):
            continue
        if cfg.filters.exclude_part_time and any(x in combined_lower for x in ["part-time", "part time"]):
            continue
        if cfg.filters.exclude_temp and any(x in combined_lower for x in ["temporary", "temp role"]):
            continue

        # Exclude obvious non-engineering roles and senior/lead/staff
        if _is_manager_or_sales(title_lower, combined_lower):
            continue
        if _is_senior_level(title_lower, cfg.filters.exclude_title_keywords):
            continue

        # Keyword scoring (adaptive: if no description available, allow lower threshold)
        score = _compute_score(text, cfg.filters.include_keywords, cfg.filters.include_bonus_keywords)
        required_min = 1 if not job.description else cfg.filters.min_score
        if score < required_min:
            continue

        # Exclude bad text
        if cfg.filters.exclude_text_keywords and any(kw.lower() in combined_lower for kw in cfg.filters.exclude_text_keywords):
            continue
        # Recency filter
        if job.posted_at_iso:
            try:
                dt = dateparser.parse(job.posted_at_iso)
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_hours = (now - dt).total_seconds() / 3600.0
                if age_hours > max_age_hours:
                    continue
            except Exception:
                pass
        results.append(job)
    return results


