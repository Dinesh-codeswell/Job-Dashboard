# LinkedIn Scraper

Async LinkedIn scraper built with Playwright for extracting profile, company, and job data from LinkedIn.

## Quick Start

```bash
pip install linkedin-scraper
playwright install chromium
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials.

## Scripts

- `scrape_india_jobs_notion_optimized.py` — Scrapes India jobs and syncs to Notion
- `process_manual_posts.py` — Processes LinkedIn Post/Job URLs from Google Sheet
- `sync_engine.py` — Syncs data to Supabase
