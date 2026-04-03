# Unified India Jobs Scraper - Complete Guide

## 🚀 Overview

Single script that combines **LinkedIn**, **Indeed**, and **Naukri** job scraping with automatic Google Sheets storage.

```bash
python scrape_all_india_jobs.py
```

That's it! All three platforms scraped, deduplicated, and stored in Google Sheets.

---

## ✨ Features

### Multi-Platform Scraping

| Platform | Method | Jobs/Request | Rate Limit |
|----------|--------|--------------|------------|
| **LinkedIn** | Browser automation | ~25 | Strict |
| **Indeed** | GraphQL API | 100 | Moderate |
| **Naukri** | REST API | 20 | Moderate |

### Key Capabilities

✅ **Unified Workflow** - One script for all platforms
✅ **Google Sheets Storage** - Automatic upload to separate worksheets
✅ **Cross-Platform Deduplication** - Same job won't be added twice
✅ **48-Hour Filter** - Only recent jobs (configurable)
✅ **Smart Normalization** - Unified data format across platforms
✅ **Statistics Tracking** - Summary uploaded to Google Sheets
✅ **Error Handling** - Graceful failures with logging

---

## 📋 Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment (.env)

```bash
# LinkedIn
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password

# Google Sheets
GOOGLE_SHEET_ID=your-sheet-id
GOOGLE_CREDENTIALS_FILE=credentials.json

# Optional: Customize search
DEFAULT_JOB_BOARDS=linkedin,indeed,naukri
DEFAULT_CITIES=Bangalore,Mumbai,Pune,Gurugram,Chennai,Hyderabad
DEFAULT_RESULTS_PER_CITY=10
DEFAULT_HOURS_OLD=48
```

### 3. LinkedIn Session Setup

First-time setup:

```bash
# Run with visible browser to login
python scrape_all_india_jobs.py --headless False

# Login to LinkedIn in the browser
# Session will be saved to linkedin_session.json
```

Subsequent runs will use the saved session.

---

## 🎯 Usage

### Basic Usage

```bash
# Scrape all three platforms
python scrape_all_india_jobs.py
```

### Platform Selection

```bash
# LinkedIn only
python scrape_all_india_jobs.py --platforms linkedin

# Indeed and Naukri only
python scrape_all_india_jobs.py --platforms indeed naukari

# All three
python scrape_all_india_jobs.py --platforms linkedin indeed naukari
```

### Customize Search Depth

```bash
# More jobs per city
python scrape_all_india_jobs.py --limit-per-city 20

# Older jobs (past 7 days)
python scrape_all_india_jobs.py --max-days 7

# Faster scrape (fewer jobs)
python scrape_all_india_jobs.py --limit-per-city 5 --max-days 1
```

### City Selection

```bash
# Tier 1 cities only
python scrape_all_india_jobs.py --tier-1-only

# Specific cities
python scrape_all_india_jobs.py --cities Bangalore Mumbai Pune

# All cities (Tier 1 + Tier 2)
python scrape_all_india_jobs.py
```

### Internships

```bash
# Include internships (default)
python scrape_all_india_jobs.py

# Exclude internships
python scrape_all_india_jobs.py --no-internships
```

### Headless Mode

```bash
# Headless (no browser UI, default)
python scrape_all_india_jobs.py

# Visible browser (for debugging)
python scrape_all_india_jobs.py --headless False
```

---

## 📊 Google Sheets Output

### Worksheet Structure

The script creates/uses three worksheets:

1. **LinkedIn_Jobs** - Jobs from LinkedIn
2. **Indeed_Jobs** - Jobs from Indeed
3. **Naukri_Jobs** - Jobs from Naukri
4. **Summary** - Run statistics

### Column Format (All Sheets)

| Column | Field | Description |
|--------|-------|-------------|
| A | Company | Company name |
| B | Company Logo | Logo URL |
| C | Job Title | Position title |
| D | Employment Type | Full-time, Part-time, etc. |
| E | Posted | Date posted |
| F | Location | Job location |
| G | Job Description | Full description |
| H | Job URL | Link to job posting |
| I | Search City | City searched |
| J | Date Added | When added to sheet |

### Summary Sheet

| Column | Field |
|--------|-------|
| Timestamp | Run timestamp |
| LinkedIn Jobs | Count from LinkedIn |
| Indeed Jobs | Count from Indeed |
| Naukri Jobs | Count from Naukri |
| Total Jobs | Total uploaded |
| Duplicates Skipped | Duplicate count |
| Errors | Error count |

---

## ⚙️ Configuration

### Keywords

Edit `CONSULTING_KEYWORDS` and `INTERNSHIP_KEYWORDS` in the script:

```python
CONSULTING_KEYWORDS = [
    "Management Consultant",
    "Business Consultant",
    "Strategy Consultant",
    # ... add more
]

INTERNSHIP_KEYWORDS = [
    "Consulting Intern",
    "Business Analyst Intern",
    # ... add more
]
```

### Cities

Edit `DEFAULT_CITIES` in `.env` or use `--cities` flag:

```bash
DEFAULT_CITIES=Bangalore,Mumbai,Pune,Gurugram,Chennai,Hyderabad,Kolkata,Ahmedabad
```

### Job Age Filter

Edit `DEFAULT_HOURS_OLD` in `.env` or use `--max-days`:

```bash
# .env
DEFAULT_HOURS_OLD=48  # 48 hours = 2 days

# Command line
python scrape_all_india_jobs.py --max-days 3  # 3 days
```

---

## 🔄 How It Works

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    scrape_all_india_jobs.py                 │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   LinkedIn    │  │    Indeed     │  │    Naukri     │
│  (Browser)    │  │   (GraphQL)   │  │    (REST)     │
└───────────────┘  └───────────────┘  └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Unified Format       │
                │  + Deduplication      │
                └───────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ LinkedIn_Jobs │  │  Indeed_Jobs  │  │  Naukri_Jobs  │
│   (Sheet)     │  │   (Sheet)     │  │   (Sheet)     │
└───────────────┘  └───────────────┘  └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Summary     │
                    │   (Sheet)     │
                    └───────────────┘
```

### Execution Steps

1. **Initialize** - Load configuration, connect to Google Sheets
2. **LinkedIn Scraping** (if enabled)
   - Load browser session
   - Search each keyword + city combination
   - Apply 48-hour filter at URL level
   - Scrape job details
   - Upload to LinkedIn_Jobs sheet
3. **Indeed/Naukri Scraping** (if enabled)
   - Call jobspy API for each keyword + city
   - Process DataFrame results
   - Upload to respective sheets
4. **Deduplication** - Check URLs across all platforms
5. **Summary** - Upload statistics to Summary sheet

---

## 📈 Performance

### Expected Results

| Configuration | Jobs/Run | Time | Success Rate |
|---------------|----------|------|--------------|
| Tier 1 only, 10 jobs | 50-100 | 15-20 min | 80-95% |
| All cities, 10 jobs | 100-200 | 30-40 min | 75-90% |
| All cities, 20 jobs | 200-400 | 60-80 min | 70-85% |

### Optimization Tips

1. **Start Small**: Test with `--limit-per-city 5` first
2. **Tier 1 First**: Use `--tier-1-only` for quick results
3. **Increase Gradually**: Raise limits once confirmed working
4. **Schedule Runs**: Run every 2-3 days for fresh jobs
5. **Monitor Errors**: Check logs for issues

---

## 🐛 Troubleshooting

### LinkedIn Session Expired

```
❌ Authentication error: LinkedIn session expired
```

**Solution**: Re-login with visible browser

```bash
python scrape_all_india_jobs.py --headless False
```

### Google Sheets Connection Failed

```
❌ Failed to connect to Google Sheets
```

**Solution**: Check credentials and sheet ID

```bash
# Verify credentials.json exists
ls -la credentials.json

# Verify sheet ID in .env
echo $GOOGLE_SHEET_ID
```

### No Jobs Found

```
⚠️  No jobs found for 'Consultant' in Bangalore
```

**Solutions**:
- Broaden search terms
- Increase `--max-days`
- Check location spelling
- Try different keywords

### Too Many Duplicates

```
⚠️  Duplicates Skipped: 50
```

**Solution**: Normal after multiple runs. Sheet is working correctly by preventing duplicates.

### API Rate Limit

```
❌ Naukri API returned 406 - Recaptcha required
```

**Solutions**:
- Reduce `--limit-per-city`
- Increase delay between requests
- Use proxies for large-scale scraping

---

## 📝 Command Reference

| Flag | Description | Default |
|------|-------------|---------|
| `--platforms` | Platforms to scrape | linkedin indeed naukari |
| `--max-days` | Max job age in days | 2 |
| `--limit-per-city` | Jobs per keyword per city | 10 |
| `--headless` | Headless browser mode | True |
| `--no-internships` | Exclude internships | False |
| `--tier-1-only` | Tier 1 cities only | False |
| `--cities` | Specific cities | All DEFAULT_CITIES |

---

## 🔧 Advanced Configuration

### Custom Keywords

Edit the script to add industry-specific keywords:

```python
CONSULTING_KEYWORDS = [
    # Existing keywords
    "Management Consultant",
    
    # Add your keywords
    "Healthcare Consultant",
    "Energy Consultant",
    "Retail Consultant",
]
```

### Custom Cities

Add international cities:

```python
INDIAN_CITIES_TIER_2.extend(["Dubai", "Singapore", "London"])
```

### Increase Google Sheets Limits

For large scrapes (>1000 jobs):

```python
# In google_sheets.py
self.worksheet = self.spreadsheet.add_worksheet(
    title=worksheet_name,
    rows=5000,  # Increase from 1000
    cols=30     # Increase from 20
)
```

---

## 📊 Sample Output

### Console Output

```
======================================================================
🚀 UNIFIED INDIA JOBS SCRAPER
======================================================================
📍 Platforms: linkedin, indeed, naukari
📍 Cities: 9
📍 Keywords: 40
📍 Limit per city: 10
📍 Time Filter: PAST 2 DAYS
======================================================================

📊 Connecting to Google Sheets...
✅ Connected to 3 worksheets

======================================================================
🔗 LINKEDIN SCRAPING
======================================================================
✓ LinkedIn session loaded

🔍 LinkedIn: 'Management Consultant' in Bangalore (past 2 days)
  ✓ LinkedIn: Senior Consultant at McKinsey
  ✓ LinkedIn: Business Analyst at BCG
...

======================================================================
📊 WORKFLOW SUMMARY
======================================================================
🔗 LinkedIn Jobs:  45
📡 Indeed Jobs:   32
🇮🇳  Naukri Jobs:    28
📈 Total Jobs:    105
⚠️  Duplicates:     12
❌ Errors:         3
======================================================================
⏰ Completed at: 2026-04-03 15:30:00
======================================================================
```

### Google Sheets Output

**LinkedIn_Jobs Sheet:**

| Company | Logo | Job Title | Type | Posted | Location | Description | URL |
|---------|------|-----------|------|--------|----------|-------------|-----|
| McKinsey | [URL] | Senior Consultant | Full-time | 1 day ago | Bangalore | ... | [URL] |
| BCG | [URL] | Business Analyst | Full-time | 2 days ago | Mumbai | ... | [URL] |

**Summary Sheet:**

| Timestamp | LinkedIn | Indeed | Naukri | Total | Duplicates | Errors |
|-----------|----------|--------|--------|-------|------------|--------|
| 2026-04-03 15:30 | 45 | 32 | 28 | 105 | 12 | 3 |

---

## 🎓 Best Practices

1. **Run Schedule**: Every 2-3 days for fresh jobs
2. **Start Small**: Test with `--limit-per-city 5` first
3. **Monitor Logs**: Check for errors in console
4. **Backup Sheets**: Download sheets periodically
5. **Clean Old Jobs**: Remove jobs >30 days old monthly
6. **Respect Limits**: Don't scrape too frequently
7. **Use Filters**: Leverage Google Sheets filters for analysis

---

## 📊 Data Analysis

### Google Sheets Queries

```sql
-- Recent jobs by company
=QUERY(A:J, "SELECT B, COUNT(C) GROUP BY B ORDER BY COUNT(C) DESC LABEL B 'Company', COUNT(C) 'Jobs'")

-- Jobs by location
=QUERY(A:J, "SELECT F, COUNT(C) GROUP BY F ORDER BY COUNT(C) DESC LABEL F 'Location', COUNT(C) 'Jobs'")

-- Recent jobs (last 24 hours)
=QUERY(A:J, "SELECT * WHERE E CONTAINS '1 day' OR E CONTAINS 'today'")
```

### Pivot Tables

Create pivot tables for:
- Jobs by company
- Jobs by location
- Jobs by employment type
- Jobs by posting date

---

## 🚀 Next Steps

1. **First Run**: Test with minimal settings
   ```bash
   python scrape_all_india_jobs.py --tier-1-only --limit-per-city 5
   ```

2. **Verify Output**: Check Google Sheets for results

3. **Scale Up**: Increase limits gradually
   ```bash
   python scrape_all_india_jobs.py --limit-per-city 15 --max-days 3
   ```

4. **Automate**: Schedule regular runs
   ```bash
   # Windows Task Scheduler or cron
   0 9 */2 * * python /path/to/scrape_all_india_jobs.py
   ```

5. **Analyze**: Use Google Sheets for job market analysis

---

## 📞 Support

### Common Issues

| Issue | Solution |
|-------|----------|
| Session expired | Re-login with `--headless False` |
| No jobs found | Broaden search, increase `--max-days` |
| Too many errors | Reduce `--limit-per-city` |
| Sheets full | Create new sheet, update `GOOGLE_SHEET_ID` |

### Logs

Check console output for detailed logs. Increase verbosity:

```python
# In script
logging.basicConfig(level=logging.DEBUG)
```

---

**Happy Job Scraping! 🎯**

For more details, see:
- `INDEED_NAUKRI_INTEGRATION.md` - Indeed/Naukri specifics
- `JOB_STORAGE_GUIDE.md` - Storage options
- `scrape_indeed_naukri_example.py` - API examples
