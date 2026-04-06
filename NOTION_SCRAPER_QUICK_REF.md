# 🔧 Notion Scraper Quick Reference

## Available Scripts

| Script | Purpose | Lines | Best For |
|--------|---------|-------|----------|
| `simple_notion_scraper.py` | Lightweight, no dependencies | 381 | Quick runs, minimal setup |
| `scrape_india_jobs_notion.py` | Full-featured India scraper | 742 | Comprehensive scraping |
| `scrape_india_jobs_notion_optimized.py` | Optimized for speed/success rate | 859 | **Recommended** (85-95% success) |

---

## Setup

### 1. Environment Variables (`.env`)

```bash
# Notion Configuration
NOTION_API_KEY=your_notion_integration_key
NOTION_DATABASE_ID=your_database_id

# LinkedIn Credentials
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password
```

### 2. Notion Database Setup

Your Notion database should have these columns:
- **Job Title** (Title column - must be first)
- **Company** (Text)
- **Location** (Text)
- **Posted Date** (Text)
- **Employment Type** (Select)
- **Job URL** (URL)
- **Description** (Text)
- **Search Keywords** (Text)
- **Scraped At** (Date)

---

## Usage

### Simple Scraper (Fastest)
```bash
python simple_notion_scraper.py --limit 30
python simple_notion_scraper.py --keywords "SDE" "Product Manager" --limit 50
```

### Optimized Scraper (Recommended)
```bash
python scrape_india_jobs_notion_optimized.py --limit 50
python scrape_india_jobs_notion_optimized.py --keywords "Data Analyst" "Growth" --cities "Bangalore" "Mumbai"
```

### Full Scraper (Most Comprehensive)
```bash
python scrape_india_jobs_notion.py --limit 100
```

---

## Key Features

✅ **24-hour filter** - Only fetches jobs posted in last 24 hours  
✅ **Duplicate detection** - Skips jobs already in Notion  
✅ **Smart keyword filtering** - Targets high-value technical/business roles  
✅ **Excludes basic roles** - Filters out accountant, copywriter, video editor, etc.  
✅ **Auto-retry** - Handles rate limits and temporary failures  
✅ **Caching** - Remembers previously added jobs  

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Notion API error" | Check `NOTION_API_KEY` and database permissions |
| "Database not found" | Verify `NOTION_DATABASE_ID` is correct |
| No jobs found | Increase `--limit` or broaden keywords |
| Login failed | Update LinkedIn credentials in `.env` |

---

## Data Flow

```
LinkedIn → Browser (Playwright) → Parse Jobs → Filter (24h) → Notion API → Database
```

---

**See `NOTION_SETUP.md` for detailed setup instructions.**
