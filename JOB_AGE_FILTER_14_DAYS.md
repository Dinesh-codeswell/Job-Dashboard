# Job Age Filter - 14 Days Maximum

## ✅ Feature Implemented

All job scrapers now automatically filter out jobs older than **14 days (2 weeks)**.

---

## 🎯 What Changed

### Updated Scripts
1. **`jobs_to_sheets.py`** - General job scraper
2. **`scrape_consulting_india.py`** - Consulting jobs scraper for India

### New Functionality
- ✅ Automatic age detection from LinkedIn's "X days ago" format
- ✅ Skip jobs older than 14 days
- ✅ Display count of skipped old jobs in summary
- ✅ Configurable max age (default: 14 days)

---

## 📊 How It Works

### Age Detection

The scraper parses LinkedIn's posted date format:
- `"2 hours ago"` → 0.08 days → ✅ Include
- `"3 days ago"` → 3 days → ✅ Include
- `"1 week ago"` → 7 days → ✅ Include
- `"2 weeks ago"` → 14 days → ✅ Include (boundary)
- `"3 weeks ago"` → 21 days → ❌ Skip
- `"1 month ago"` → 30 days → ❌ Skip

### Time Unit Conversion

```python
minutes → days: value / (24 * 60)
hours   → days: value / 24
days    → days: value
weeks   → days: value * 7
months  → days: value * 30
```

### Filter Logic

```python
if days_ago <= 14:
    Upload to Google Sheets ✅
else:
    Skip with message ⏰
```

---

## 📝 Usage Examples

### General Job Scraper

```bash
# Default (14 days filter)
python jobs_to_sheets.py -k "Data Analyst" -l "Remote" --limit 15

# Jobs will be automatically filtered
# Only jobs ≤14 days old will be uploaded
```

### Consulting Jobs Scraper

```bash
# Default (14 days filter)
python scrape_consulting_india.py --cities "Chennai" "Mumbai" --limit-per-city 10

# Only recent consulting jobs will be added
```

---

## 📊 Output Messages

### When Job is Too Old

```
⏰ Skipping - Job older than 14 days (3 weeks ago)
```

### Summary Display

```
📊 WORKFLOW SUMMARY
======================================================================
✅ Success: True
📍 Jobs Found: 50
📄 Jobs Scraped: 45
📊 Jobs Uploaded: 30
⚠️ Duplicates Skipped: 10
⏰ Jobs Too Old (>14 days): 5
======================================================================
```

---

## 🔧 Customization

### Change Maximum Age

Edit the script and modify the `max_days_old` parameter:

```python
# In jobs_to_sheets.py
results = await workflow.run(
    keywords="Data Analyst",
    location="Remote",
    limit=15,
    max_days_old=7  # Change to 7 days for example
)
```

### Disable Age Filter

Set `max_days_old` to a very high number:

```python
max_days_old=365  # Essentially no filter
```

---

## 🎯 Benefits

1. **Relevant Jobs Only** - Only recent, actionable jobs
2. **Better UX** - Team sees fresh opportunities
3. **Auto-Cleanup** - No manual filtering needed
4. **Transparent** - Shows count of skipped old jobs
5. **Configurable** - Easy to adjust time window

---

## 📈 Example Scenarios

### Scenario 1: Daily Scraping
```bash
# Run daily, only new jobs from last 14 days added
python jobs_to_sheets.py -k "Consultant" -l "Mumbai" --limit 20
```
**Result:** Only jobs posted in last 2 weeks uploaded

### Scenario 2: Weekly Clean Sweep
```bash
# Run once a week, get all recent jobs
python scrape_consulting_india.py --tier-1-only --limit-per-city 25
```
**Result:** Fresh consulting jobs from past 2 weeks

### Scenario 3: Multiple Runs Per Day
```bash
# Morning run
python jobs_to_sheets.py -k "Data Analyst" -l "Bangalore" --limit 10

# Evening run (duplicates skipped, old jobs filtered)
python jobs_to_sheets.py -k "Data Analyst" -l "Bangalore" --limit 10
```
**Result:** Only new, recent jobs added in second run

---

## 🧪 Testing

### Test Age Detection

```python
from jobs_to_sheets import JobScraperWorkflow

workflow = JobScraperWorkflow()

# Test various date formats
test_dates = [
    "2 hours ago",
    "5 days ago",
    "2 weeks ago",
    "3 weeks ago",
    "1 month ago"
]

for date_str in test_dates:
    is_recent = workflow._is_job_recent(date_str, max_days=14)
    print(f"{date_str}: {'✅ Recent' if is_recent else '❌ Too Old'}")
```

**Expected Output:**
```
2 hours ago: ✅ Recent
5 days ago: ✅ Recent
2 weeks ago: ✅ Recent
3 weeks ago: ❌ Too Old
1 month ago: ❌ Too Old
```

---

## 📋 Files Modified

| File | Changes |
|------|---------|
| `jobs_to_sheets.py` | Added `_is_job_recent()` method, updated `run()` |
| `scrape_consulting_india.py` | Added `_is_job_recent()` method, updated `scrape_city()` |

---

## ⚙️ Configuration

### Default Settings
- **Max Age:** 14 days (2 weeks)
- **Check:** Automatic on all jobs
- **Action:** Skip old jobs silently
- **Display:** Show count in summary

### Edge Cases Handled
- ✅ No date provided → Assume recent (include)
- ✅ Unparseable date → Assume recent (include)
- ✅ "Just now" / "Today" → Include
- ✅ Exact 14 days → Include (boundary)
- ✅ 15+ days → Skip

---

## 🎉 Summary

**Before:** All jobs regardless of age  
**After:** Only jobs ≤14 days old  

**Benefit:** Dashboard always shows fresh, relevant opportunities!

---

**Last Updated:** April 1, 2026  
**Version:** 1.0  
**Default Max Age:** 14 days
