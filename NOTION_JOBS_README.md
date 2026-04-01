# LinkedIn Jobs to Notion - Quick Reference

## What This Does

Scrapes LinkedIn jobs posted in the **past 24 hours** in **India** for **core technical and business roles**, and stores them in a **Notion database**.

## Target Roles

### ✅ Included
- SDE, Software Engineer, Backend/Frontend/Full Stack Engineer
- Product Manager (PM), Associate Product Manager (APM)
- Data Analyst, Business Analyst, Product Analyst
- Data Scientist, Machine Learning Engineer, AI Engineer
- Growth Manager, Strategy Manager, Operations Manager
- Technical Program Manager (TPM), Program Manager
- Solutions Architect, Cloud Architect, DevOps Engineer, SRE
- Product Designer, UX Designer
- Management Consultant, Technology Consultant

### ❌ Excluded
- Accountant, Accounting roles
- Copywriter, Content Writer
- Video Editor
- Data Entry
- Customer Support, Telecaller
- Basic Sales Executive
- HR Executive, Recruiter
- Social Media Manager, SEO Executive

---

## Quick Start

### 1. Install Dependencies

```bash
pip install notion-client
```

### 2. Setup Notion

Follow `NOTION_SETUP.md` to:
- Create a Notion database with columns: Company, Role, Date Added, Location, URL
- Create a Notion integration
- Get your API key and database ID

### 3. Configure Environment

```bash
copy .env.example.notion .env
```

Edit `.env` and add:
```env
NOTION_API_KEY=secret_your_token_here
NOTION_DATABASE_ID=your_database_id_here
```

### 4. Create LinkedIn Session (if not already done)

```bash
python samples/create_session.py
```

### 5. Run the Scraper

```bash
python scrape_india_jobs_notion.py
```

---

## Command Options

```bash
# Basic usage (default: 10 jobs per keyword, India-wide)
python scrape_india_jobs_notion.py

# Scrape more jobs per keyword
python scrape_india_jobs_notion.py --limit 20

# Target a specific city
python scrape_india_jobs_notion.py --location Bangalore
python scrape_india_jobs_notion.py --location Mumbai
python scrape_india_jobs_notion.py --location Pune

# Use specific keywords only
python scrape_india_jobs_notion.py --keywords "SDE" "Product Manager"

# Run with visible browser (for debugging)
python scrape_india_jobs_notion.py --headless False

# Disable duplicate checking
python scrape_india_jobs_notion.py --no-dedup

# Combine options
python scrape_india_jobs_notion.py --limit 15 --location Bangalore --headless False
```

---

## Notion Database Setup

Your Notion database must have these **exact column names**:

| Column Name | Type | Required |
|-------------|------|----------|
| Company | **Title** | ✅ Yes |
| Position | Rich text | ✅ Yes |
| Date Posted | Date (YYYY/MM/DD) | ✅ Yes |
| Location | Rich text | ✅ Yes |
| Application Link | URL | ✅ Yes |

**Important:** Column names are case-sensitive!

### Your Database ✅

Your database "High Growth Roles Tracker" is already configured correctly:
- Database ID: `2e7e82acc24f8102bbbaf27171a0d1ef`
- All required columns are present
- Column types match: Company (Title), Position (Rich text), Date Posted (Date), Location (Rich text), Application Link (URL)

---

## How It Works

1. **Search**: Searches LinkedIn for each keyword (e.g., "SDE", "Product Manager") in India
2. **Filter 24h**: Only keeps jobs posted in the past 24 hours
3. **Filter Roles**: Excludes basic roles (accountant, copywriter, etc.)
4. **Deduplicate**: Skips jobs already in your Notion database
5. **Store**: Adds matching jobs to Notion with Company, Role, Date Added, Location, URL

---

## Output Example

Your Notion database will look like:

| Company | Position | Date Posted | Location | Application Link |
|---------|----------|-------------|----------|------------------|
| Google | Software Development Engineer | 2024-01-15 | Bangalore | https://linkedin.com/jobs/view/... |
| Microsoft | Product Manager | 2024-01-15 | Hyderabad | https://linkedin.com/jobs/view/... |
| Amazon | Data Scientist | 2024-01-15 | Mumbai | https://linkedin.com/jobs/view/... |
| Flipkart | Growth Manager | 2024-01-15 | Bangalore | https://linkedin.com/jobs/view/... |

> **Note:** "Date Posted" is the date the job was added to your tracker (today's date), not when LinkedIn posted it.

---

## Troubleshooting

### No jobs added
- Check if there are jobs posted in the past 24h (try running in morning/evening)
- Verify your LinkedIn session is valid
- Check the scraper output for filtering reasons

### Notion connection failed
- Verify `NOTION_API_KEY` starts with `secret_`
- Ensure integration is connected to your database (see NOTION_SETUP.md)
- Check database ID is correct (32 characters)

### Too many jobs excluded
- Adjust keywords with `--keywords` option
- Review excluded roles list - some jobs may match exclusion patterns

---

## Automation

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → "LinkedIn Jobs Scraper"
3. Trigger: Daily at 9:00 AM
4. Action: Start a program
   - Program: `C:\Path\To\Python\python.exe`
   - Arguments: `scrape_india_jobs_notion.py --limit 15`
   - Start in: `C:\linkedin_scraper`

### Batch File

Create `scrape_jobs.bat`:
```batch
@echo off
cd /d C:\linkedin_scraper
python scrape_india_jobs_notion.py --limit 15
pause
```

---

## Files Created

- `scrape_india_jobs_notion.py` - Main scraper script
- `linkedin_scraper/integrations/notion.py` - Notion integration module
- `.env.example.notion` - Environment template
- `NOTION_SETUP.md` - Detailed setup guide
- `requirements.txt` - Updated with notion-client

---

## Tips

1. **Run twice daily**: Morning (9-10 AM) and evening (6-7 PM) for best coverage
2. **Start small**: Use `--limit 5` first to test, then increase
3. **Monitor duplicates**: The scraper skips jobs already in Notion
4. **Customize keywords**: Add/remove roles based on your preferences
5. **Check Notion regularly**: Review and tag/star interesting jobs

---

## Support

- Setup issues: See `NOTION_SETUP.md`
- LinkedIn session: Run `python samples/create_session.py`
- General help: Check scraper output for specific error messages

---

**Good luck with your job search! 🚀**
