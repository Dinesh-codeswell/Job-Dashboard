# ⚡ FRESH JOBS DASHBOARD - 24 Hours Only

## Core Philosophy

**Your dashboard is about SPEED and FRESHNESS** - being the FIRST to surface jobs posted within 24 hours.

### Why 24 Hours is CRITICAL

- ✅ Jobs posted in past 24h get **10x more applications** in first day
- ✅ Early applicants have **5x higher interview rates**
- ✅ Fresh jobs = Less competition = Better chances
- ✅ Your dashboard's VALUE PROPOSITION: Fastest alerts

---

## How It Works

### The Problem with 7-Day Filters
```
Day 1: Job posted → 500 applications
Day 3: Job posted → 200 applications  
Day 7: Job posted → 20 applications (but already stale)
```

### The 24-Hour Advantage
```
Job posted 2 hours ago → Your dashboard notifies → Apply in top 50 → 🎯 Interview!
```

---

## Optimal Scraping Schedule

### Recommended: Run Every 3-4 Hours

| Time | Purpose | Expected Jobs |
|------|---------|---------------|
| **9:00 AM** | Jobs posted overnight | 20-50 fresh jobs |
| **12:00 PM** | Morning postings | 10-30 fresh jobs |
| **3:00 PM** | Mid-day postings | 10-20 fresh jobs |
| **6:00 PM** | Afternoon postings | 15-40 fresh jobs |

### Why This Works

```
Run at 9 AM  → Catches jobs from 9 AM yesterday to 9 AM today (24h window)
Run at 12 PM → Catches jobs from 9 AM yesterday to 12 PM today
             → But duplicate check skips jobs already added
             → Only NEW jobs from 9-12 AM today are added ✅
```

---

## Usage

### Default Run (Recommended)
```bash
py scrape_india_jobs_notion.py
```
- Searches 50+ keywords
- 50 jobs per keyword
- **PAST 24 HOURS ONLY** ⚡
- Skips duplicates automatically

### High-Frequency Mode (More Jobs)
```bash
py scrape_india_jobs_notion.py --limit 100
```

### Target Specific Roles
```bash
py scrape_india_jobs_notion.py --keywords "SDE" "Product Manager" "Data Scientist"
```

### City-Specific
```bash
py scrape_india_jobs_notion.py --location Bangalore
py scrape_india_jobs_notion.py --location "Hyderabad"
```

---

## Expected Results

### First Run (9 AM)
```
⚡ FRESH JOBS DASHBOARD - India (24 HOURS ONLY)
======================================================================
📍 Time Filter: PAST 24 HOURS ONLY ⚡
💡 Tip: Run every 3-4 hours for best results

📊 WORKFLOW SUMMARY
======================================================================
✅ Success: True
📝 Keywords Searched: 50
🔍 Total Jobs Found: 2500
📄 Total Jobs Scraped: 1200
⚡ FRESH JOBS (24h): 85        ← Jobs from past 24h
🎯 Core Technical/Business Roles: 72
➕ Jobs Added to Notion: 72    ← All fresh jobs added!
⚠️  Duplicates Skipped: 0
❌ Excluded (non-core/old): 1128
======================================================================
💡 Next run: In 3-4 hours for more fresh jobs
```

### Second Run (12 PM - Same Day)
```
📊 WORKFLOW SUMMARY
======================================================================
✅ Success: True
📝 Keywords Searched: 50
🔍 Total Jobs Found: 2500
📄 Total Jobs Scraped: 1200
⚡ FRESH JOBS (24h): 90        ← Some new jobs posted since 9 AM
🎯 Core Technical/Business Roles: 18
➕ Jobs Added to Notion: 18    ← Only NEW jobs!
⚠️  Duplicates Skipped: 72     ← Previous jobs skipped
❌ Excluded (non-core/old): 1110
======================================================================
💡 Next run: In 3-4 hours for more fresh jobs
```

### Third Run (3 PM - Same Day)
```
📊 WORKFLOW SUMMARY
======================================================================
✅ Success: True
⚡ FRESH JOBS (24h): 95
🎯 Core Technical/Business Roles: 12
➕ Jobs Added to Notion: 12    ← More fresh jobs!
⚠️  Duplicates Skipped: 90
======================================================================
```

---

## Why You See Different Results Each Time

### The Rolling 24-Hour Window

```
9 AM Run:  [████████ 24h ████████]  → 72 jobs added
12 PM Run: [   ███ 24h ███        ]  → 18 NEW jobs (9-12 AM)
3 PM Run:  [      ██ 24h ██       ]  → 12 NEW jobs (12-3 PM)
6 PM Run:  [         ███ 24h ████ ]  → 25 NEW jobs (3-6 PM)

Total fresh jobs in one day: 72 + 18 + 12 + 25 = 127 jobs! ✅
```

### Duplicate Detection Works FOR You

- Cache file tracks all added job URLs
- Same job won't be added twice
- Each run only adds **NEW** jobs posted since last run
- Old jobs (24h+) automatically filtered out

---

## Automation (CRITICAL for Success)

### Windows Task Scheduler Setup

**Create 4 Daily Tasks:**

1. **9 AM Job Scraping**
   - Trigger: Daily at 9:00 AM
   - Action: `py scrape_india_jobs_notion.py --limit 50`

2. **12 PM Job Scraping**
   - Trigger: Daily at 12:00 PM
   - Action: `py scrape_india_jobs_notion.py --limit 50`

3. **3 PM Job Scraping**
   - Trigger: Daily at 3:00 PM
   - Action: `py scrape_india_jobs_notion.py --limit 50`

4. **6 PM Job Scraping**
   - Trigger: Daily at 6:00 PM
   - Action: `py scrape_india_jobs_notion.py --limit 50`

### Batch File for Manual Runs

Create `fresh_jobs_scraper.bat`:
```batch
@echo off
cd /d C:\linkedin_scraper
C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe scrape_india_jobs_notion.py --limit 50
echo.
echo ✅ Scraping complete! Check Notion for fresh jobs.
pause
```

---

## Tips for Maximum Freshness

### 1. Run More Frequently = More Jobs
```
Run 2x/day  → ~50 fresh jobs/day
Run 4x/day  → ~100+ fresh jobs/day
Run 6x/day  → ~150+ fresh jobs/day
```

### 2. Increase Limits During Peak Hours
```bash
# Morning (9 AM) - High volume
py scrape_india_jobs_notion.py --limit 100

# Mid-day (12 PM, 3 PM) - Lower volume
py scrape_india_jobs_notion.py --limit 50

# Evening (6 PM) - High volume
py scrape_india_jobs_notion.py --limit 100
```

### 3. Monitor Your Notion Dashboard
- Check Notion after each run
- Star/tag priority jobs immediately
- Apply within hours of posting (not days!)

### 4. Clear Cache Weekly (Optional)
```bash
# Reset duplicate tracking (use sparingly!)
python clear_notion_cache.py

# Then run scraper
py scrape_india_jobs_notion.py --limit 100
```

---

## Troubleshooting

### "No Fresh Jobs Found"
**Cause:** Running at wrong times or too frequently

**Solution:**
```bash
# Run at peak posting times
# 9-10 AM, 6-7 PM are best

# Increase search limit
py scrape_india_jobs_notion.py --limit 100

# Add more keywords
py scrape_india_jobs_notion.py --keywords "SDE" "Backend" "Frontend" "Full Stack"
```

### "Same Jobs Every Time"
**Cause:** Cache not working or 24h filter too lenient

**Solution:**
```bash
# Verify cache file exists
type notion_added_jobs_cache.json

# Check 24h filter is working
# Look for "⚡ FRESH JOBS (24h): X" in output
```

### "Too Many Duplicates Skipped"
**This is GOOD!** Means cache is working.

- High duplicate count = Previous runs caught old jobs
- Low new jobs count = Few jobs posted since last run
- **Solution:** Run less frequently or at different times

---

## Success Metrics

### Good Signs ✅
- `⚡ FRESH JOBS (24h): 10-100` per run
- `➕ Jobs Added to Notion: 5-50` per run
- `⚠️ Duplicates Skipped: 50-200` (cache working!)
- Different jobs each run

### Warning Signs ⚠️
- `⚡ FRESH JOBS (24h): 0` consistently
- `➕ Jobs Added to Notion: 0` consistently
- Same jobs appearing repeatedly

**Fix:** Run at different times, increase limits, add keywords

---

## Comparison: 24h vs 7-Day Approach

| Metric | 24-Hour (Your Dashboard) | 7-Day (Others) |
|--------|-------------------------|----------------|
| Jobs per run | 10-100 | 200-500 |
| Job freshness | ⚡ Posted <24h ago | 📅 Posted anytime |
| Competition | Low (early applicants) | High (late applicants) |
| Interview rate | 5x higher | Standard |
| Run frequency | 4x/day | 1x/week |
| **Value** | **FIRST to know** | Just another aggregator |

---

## Your Competitive Advantage

```
Other job boards:     Job posted → 24h later → Listed → 500 applications
Your dashboard:       Job posted → 2h later → Listed → 50 applications ✅
```

**This is why your dashboard exists.** Stay strict with 24h filter!

---

**Remember:** Quality > Quantity. One fresh job applied to early is worth 100 stale jobs.

For setup: See `NOTION_SETUP.md`  
For commands: See `NOTION_JOBS_README.md`
