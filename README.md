## Job Checker (Austin + US Remote)

High-signal job notifier for DevOps/Cloud roles, optimized for Austin, TX (on-site/hybrid/remote) and US-remote.

### Features
- Sources: Remotive and Greenhouse (by company boards). Optional: RemoteOK, WWR, Adzuna (keys), JobsPikr (key), Jobdataapi (key), USAJOBS.
- Filters: keywords (AWS/DevOps/Kubernetes/Terraform/etc.), Austin + US-remote, full-time by default.
- Core vs Stretch split:
  - Core: excludes Senior/Lead/Staff/Principal titles
  - Stretch: only those titles
- Telegram delivery to separate chats. SQLite de-duplication.

### Quick start
1) Python 3.10+
2) Install deps:
```
pip install -r requirements.txt
```
3) Copy env and config:
```
cp env.example .env
cp config.example.yml config.yml
```
4) Fill in `.env` with:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CORE_CHAT_ID
- TELEGRAM_STRETCH_CHAT_ID
 - Optional: ADZUNA_APP_ID, ADZUNA_APP_KEY, USAJOBS_USER_AGENT_EMAIL, JOBSPIKR_API_KEY, JOBDATAAPI_KEY

5) Run once:
```
python -m job_checker.main --once
```

Or poll every 2 minutes:
```
python -m job_checker.main --loop --interval-seconds 120
```

### Configuration
- Edit `config.yml` to adjust keywords, sources, and filters.
- If a credential is missing for a source, that source is skipped gracefully.

### Sources
- Remotive API: remote roles (filtered to US-remote where possible)
- Greenhouse Job Board API: first-party company boards via board tokens
- Optional (off by default): RemoteOK, We Work Remotely (RSS), Adzuna (APP_ID/APP_KEY), JobsPikr (JOBSPIKR_API_KEY), Jobdataapi (JOBDATAAPI_KEY), USAJOBS (User-Agent email)

### Notes
- Location logic prioritizes: Austin metro (any mode) and US-remote. Non-US remote is dropped.
- De-duplication key is primarily the job URL; fallback to a normalized composite key.
- Messages are tagged as [AUSTIN] or [US-REMOTE], and [CORE] or [STRETCH].

### Telegram setup
1) Create a bot with @BotFather and get the token
2) Create/choose two chats (Core and Stretch), add the bot, send any message in each
3) Use @userinfobot to get each chat ID
4) Put values into `.env`

### Disclaimer
Only public APIs/feeds are used. Respect each source's rate limits and terms. This tool avoids scraping behind logins.


