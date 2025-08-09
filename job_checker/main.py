from __future__ import annotations

import argparse
import os
import sys
import time
from typing import List

from dotenv import load_dotenv

from .config import load_config, Config
from .filtering import apply_keyword_filters, split_scope
from .models import Job
from .notifiers import TelegramNotifier
from .storage import SeenStore
from .sources.remotive import fetch_remotive
from .sources.greenhouse import fetch_greenhouse
from .sources.jobspikr import fetch_jobspikr
from .sources.jobdataapi import fetch_jobdataapi
from .sources.lever import fetch_lever
from .sources.wwr import fetch_wwr


def gather_jobs(cfg: Config) -> List[Job]:
    jobs: List[Job] = []
    # Remotive
    if cfg.sources.remotive.enabled:
        jobs.extend(fetch_remotive(cfg.filters.include_keywords))
    # Greenhouse
    if cfg.sources.greenhouse.enabled:
        companies = cfg.sources.greenhouse.extras.get("companies", [])
        jobs.extend(list(fetch_greenhouse(companies)))
    # Lever
    if cfg.sources.lever.enabled:
        companies = cfg.sources.lever.extras.get("companies", [])
        jobs.extend(list(fetch_lever(companies)))
    # We Work Remotely (RSS)
    if getattr(cfg.sources, 'wwr', None) and cfg.sources.wwr.enabled:
        cats = cfg.sources.wwr.extras.get("categories", ["devops-sysadmin"])  # type: ignore[attr-defined]
        jobs.extend(list(fetch_wwr(cats)))
    # JobsPikr (optional)
    if cfg.sources.jobspikr.enabled:
        loc_q = cfg.sources.jobspikr.extras.get("location_query", "Austin, TX OR Remote US")
        jobs.extend(list(fetch_jobspikr(cfg.filters.include_keywords, loc_q)))
    # Jobdataapi (optional)
    if cfg.sources.jobdataapi.enabled:
        loc_q = cfg.sources.jobdataapi.extras.get("location_query", "Austin, TX OR Remote US")
        jobs.extend(list(fetch_jobdataapi(cfg.filters.include_keywords, loc_q)))
    return jobs


def run_once(cfg: Config) -> None:
    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    core_chat_id = os.getenv("TELEGRAM_CORE_CHAT_ID")
    stretch_chat_id = os.getenv("TELEGRAM_STRETCH_CHAT_ID")
    if not bot_token or not core_chat_id or not stretch_chat_id:
        print("Missing Telegram env: TELEGRAM_BOT_TOKEN/CORE_CHAT_ID/STRETCH_CHAT_ID", file=sys.stderr)
        return

    notifier = TelegramNotifier(bot_token, core_chat_id, stretch_chat_id)
    store = SeenStore()

    jobs = gather_jobs(cfg)
    jobs = apply_keyword_filters(jobs, cfg)

    # New only
    new_jobs = [j for j in jobs if store.is_new(j)]
    if not new_jobs:
        return

    # Group by scope and level
    austin_core: List[Job] = []
    austin_stretch: List[Job] = []
    us_core: List[Job] = []
    us_stretch: List[Job] = []

    for job in new_jobs:
        scope_tag, is_stretch = split_scope(job, cfg)
        if not scope_tag:
            continue
        if scope_tag == cfg.telegram.tag_austin:
            (austin_stretch if is_stretch else austin_core).append(job)
        elif scope_tag == cfg.telegram.tag_us_remote:
            (us_stretch if is_stretch else us_core).append(job)

    # Notify
    if austin_core:
        notifier.send(austin_core, cfg.telegram.tag_austin, is_stretch=False)
    if austin_stretch:
        notifier.send(austin_stretch, cfg.telegram.tag_austin, is_stretch=True)
    if us_core:
        notifier.send(us_core, cfg.telegram.tag_us_remote, is_stretch=False)
    if us_stretch:
        notifier.send(us_stretch, cfg.telegram.tag_us_remote, is_stretch=True)

    # Mark seen
    store.add(new_jobs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Checker: Austin + US Remote")
    parser.add_argument("--config", default="config.yml", help="Path to config.yml")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--bootstrap", action="store_true", help="Mark current listings as seen without sending")
    parser.add_argument(
        "--interval-seconds", type=int, default=None, help="Override interval from config"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    interval = args.interval_seconds or cfg.app.interval_seconds

    if args.once or not args.loop:
        if args.bootstrap:
            # gather + mark seen only
            from .storage import SeenStore
            store = SeenStore()
            jobs = gather_jobs(cfg)
            jobs = apply_keyword_filters(jobs, cfg)
            store.add(jobs)
        else:
            run_once(cfg)
        return

    while True:
        try:
            run_once(cfg)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        time.sleep(interval)


if __name__ == "__main__":
    main()


