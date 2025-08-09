from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import yaml


@dataclass
class AppConfig:
    interval_seconds: int = 120
    full_time_only: bool = True
    max_post_age_hours: int = 24
    adaptive_recency: bool = True
    weekday_max_post_age_hours: int = 24
    weekend_max_post_age_hours: int = 72


@dataclass
class FiltersConfig:
    include_keywords: List[str] = field(default_factory=list)
    include_bonus_keywords: List[str] = field(default_factory=list)
    exclude_title_keywords: List[str] = field(default_factory=list)
    exclude_text_keywords: List[str] = field(default_factory=list)
    title_must_include_any: List[str] = field(default_factory=list)
    min_score: int = 2
    company_whitelist: List[str] = field(default_factory=list)
    company_blacklist: List[str] = field(default_factory=list)
    exclude_contract: bool = True
    exclude_intern: bool = True
    exclude_part_time: bool = True
    exclude_temp: bool = True


@dataclass
class LocationsConfig:
    austin_aliases: List[str] = field(default_factory=list)
    us_only_remote: bool = True


@dataclass
class SourceToggle:
    enabled: bool = True
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourcesConfig:
    remotive: SourceToggle = field(default_factory=lambda: SourceToggle(True))
    greenhouse: SourceToggle = field(default_factory=lambda: SourceToggle(True))
    lever: SourceToggle = field(default_factory=lambda: SourceToggle(True))
    jobspikr: SourceToggle = field(default_factory=lambda: SourceToggle(False))
    jobdataapi: SourceToggle = field(default_factory=lambda: SourceToggle(False))


@dataclass
class TelegramConfig:
    tag_austin: str = "[AUSTIN]"
    tag_us_remote: str = "[US-REMOTE]"
    tag_core: str = "[CORE]"
    tag_stretch: str = "[STRETCH]"


@dataclass
class Config:
    app: AppConfig
    filters: FiltersConfig
    locations: LocationsConfig
    sources: SourcesConfig
    telegram: TelegramConfig


def _read_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def load_config(config_path: str) -> Config:
    data = _read_yaml(config_path)

    app = data.get("app", {})
    filters = data.get("filters", {})
    locations = data.get("locations", {})
    sources = data.get("sources", {})
    telegram = data.get("telegram", {})

    def make_toggle(name: str, default_enabled: bool, extras: Optional[Dict[str, Any]] = None) -> SourceToggle:
        node = sources.get(name, {})
        return SourceToggle(
            enabled=bool(node.get("enabled", default_enabled)),
            extras={k: v for k, v in node.items() if k != "enabled"}
            if node else (extras or {}),
        )

    cfg = Config(
        app=AppConfig(
            interval_seconds=int(app.get("interval_seconds", 120)),
            full_time_only=bool(app.get("full_time_only", True)),
            max_post_age_hours=int(app.get("max_post_age_hours", 24)),
            adaptive_recency=bool(app.get("adaptive_recency", True)),
            weekday_max_post_age_hours=int(app.get("weekday_max_post_age_hours", 24)),
            weekend_max_post_age_hours=int(app.get("weekend_max_post_age_hours", 72)),
        ),
        filters=FiltersConfig(
            include_keywords=list(filters.get("include_keywords", [])),
            include_bonus_keywords=list(filters.get("include_bonus_keywords", [])),
            exclude_title_keywords=list(filters.get("exclude_title_keywords", [])),
            exclude_text_keywords=list(filters.get("exclude_text_keywords", [])),
            title_must_include_any=list(filters.get("title_must_include_any", [])),
            min_score=int(filters.get("min_score", 2)),
            company_whitelist=[s.lower() for s in filters.get("company_whitelist", [])],
            company_blacklist=[s.lower() for s in filters.get("company_blacklist", [])],
            exclude_contract=bool(filters.get("exclude_contract", True)),
            exclude_intern=bool(filters.get("exclude_intern", True)),
            exclude_part_time=bool(filters.get("exclude_part_time", True)),
            exclude_temp=bool(filters.get("exclude_temp", True)),
        ),
        locations=LocationsConfig(
            austin_aliases=[s.lower() for s in locations.get("austin_aliases", [])],
            us_only_remote=bool(locations.get("us_only_remote", True)),
        ),
        sources=SourcesConfig(
            remotive=make_toggle("remotive", True),
            greenhouse=make_toggle("greenhouse", True),
            lever=make_toggle("lever", True),
            jobspikr=make_toggle("jobspikr", False),
            jobdataapi=make_toggle("jobdataapi", False),
        ),
        telegram=TelegramConfig(
            tag_austin=str(telegram.get("tag_austin", "[AUSTIN]")),
            tag_us_remote=str(telegram.get("tag_us_remote", "[US-REMOTE]")),
            tag_core=str(telegram.get("tag_core", "[CORE]")),
            tag_stretch=str(telegram.get("tag_stretch", "[STRETCH]")),
        ),
    )
    return cfg


