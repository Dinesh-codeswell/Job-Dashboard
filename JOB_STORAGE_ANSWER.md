# Job Storage Answer: Where Are Indeed & Naukri Jobs Stored?

## Short Answer

**By default: NOWHERE** - Jobs are returned as a pandas DataFrame in memory only.

**With auto_save=True: CSV + Excel** in `output/jobs/` directory.

---

## The Complete Picture

### Before (Original Implementation)

Jobs fetched from Indeed and Naukri were **NOT automatically stored**:

```python
from linkedin_scraper.integrations import scrape_multi_platform

df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="software engineer",
    location="Bangalore"
)

# ❌ Jobs are ONLY in the DataFrame
# ❌ Nothing is saved automatically
# ❌ You must manually save:
# save_jobs_to_csv(df, "jobs.csv")
```

### After (Updated Implementation)

Now you have **automatic storage options**:

```python
from linkedin_scraper.integrations import scrape_multi_platform

# ✅ Auto-saves to CSV + Excel
result = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="software engineer",
    location="Bangalore",
    auto_save=True,  # Enable auto-save
    output_dir="output/jobs"
)

# Jobs are saved to:
# - output/jobs/jobs_YYYYMMDD_HHMMSS.csv
# - output/jobs/jobs_report_YYYYMMDD_HHMMSS.xlsx
```

---

## Storage Locations

### 1. Default Auto-Save (CSV + Excel)

**Location:** `output/jobs/`

**Files:**
- `jobs_YYYYMMDD_HHMMSS.csv` - All jobs in CSV format
- `jobs_report_YYYYMMDD_HHMMSS.xlsx` - Excel with sheets per platform

**Enable:**
```python
result = scrape_multi_platform(
    ...,
    auto_save=True,
    output_dir="output/jobs"
)
```

### 2. Multiple Formats

**Location:** `output/jobs/`

**Files:**
- `jobs_YYYYMMDD_HHMMSS.csv`
- `jobs_report_YYYYMMDD_HHMMSS.xlsx`
- `jobs_YYYYMMDD_HHMMSS.json`
- `jobs.db` (SQLite database)

**Enable:**
```python
result = scrape_multi_platform(
    ...,
    auto_save=True,
    save_formats=['csv', 'excel', 'json', 'sqlite']
)
```

### 3. Manual Storage

**Location:** Your choice

**Example:**
```python
from linkedin_scraper.integrations import JobStorage

storage = JobStorage(output_dir="output/my_jobs")
storage.save_all(
    df,
    save_csv=True,
    save_excel=True,
    save_json=True
)
```

---

## Storage Flow Diagram

```
scrape_multi_platform()
         ↓
    [Indeed API]  [Naukri API]
         ↓              ↓
         └──────┬───────┘
                ↓
        pandas DataFrame (in memory)
                ↓
        ┌───────┴────────┐
        │                │
   auto_save=False  auto_save=True
        │                │
        ↓                ↓
   Return DataFrame  JobStorage.save_all()
   (NOT saved)            ↓
                    ┌─────┴─────┐
                    │           │
               CSV File     Excel File
               JSON File    SQLite DB
               (based on save_formats)
```

---

## Quick Reference

### Where are my jobs stored?

| Scenario | Storage Location |
|----------|-----------------|
| Default (no auto_save) | ❌ Nowhere (in memory only) |
| `auto_save=True` | ✅ `output/jobs/*.csv` + `*.xlsx` |
| `auto_save=True, save_formats=['csv']` | ✅ `output/jobs/*.csv` |
| `auto_save=True, save_formats=['excel']` | ✅ `output/jobs/*.xlsx` |
| `auto_save=True, save_formats=['sqlite']` | ✅ `output/jobs/jobs.db` |
| Manual `JobStorage` | ✅ Your specified directory |

### How to check where jobs were saved?

```python
result = scrape_multi_platform(..., auto_save=True)

print(result['saved_files'])
# {
#   'csv': 'output/jobs/jobs_20260403_120000.csv',
#   'excel': 'output/jobs/jobs_report_20260403_120000.xlsx'
# }
```

---

## Common Questions

### Q: "I scraped jobs but can't find the files!"

**A:** Did you set `auto_save=True`?

```python
# ❌ Without auto_save - jobs NOT saved
df = scrape_multi_platform(["indeed", "naukri"], "python")

# ✅ With auto_save - jobs saved
result = scrape_multi_platform(
    ["indeed", "naukri"],
    "python",
    auto_save=True
)
```

### Q: "Where is the output directory?"

**A:** Default is `output/jobs/` relative to your script.

```
C:\Linkedin_scraper\
├── output/
│   └── jobs/
│       ├── jobs_20260403_120000.csv
│       └── jobs_report_20260403_120000.xlsx
└── scrape_indeed_naukri_example.py
```

### Q: "Can I change the output directory?"

**A:** Yes, use `output_dir` parameter:

```python
result = scrape_multi_platform(
    ...,
    auto_save=True,
    output_dir="my_custom_output/jobs"  # Custom location
)
```

### Q: "Can I save to Google Sheets automatically?"

**A:** Yes, configure Google Sheets credentials:

```python
result = scrape_multi_platform(
    ...,
    auto_save=True,
    save_formats=['csv', 'excel', 'google_sheets'],
    google_sheet_id="your-sheet-id",
    google_credentials_file="credentials.json"
)
```

### Q: "How do I access the DataFrame after auto-save?"

**A:** It's in the result dictionary:

```python
result = scrape_multi_platform(..., auto_save=True)

df = result['dataframe']  # Access DataFrame
print(f"Total jobs: {result['total_jobs']}")
print(f"Files: {result['saved_files']}")
```

---

## Implementation Details

### Files Created

1. **`linkedin_scraper/integrations/job_storage.py`**
   - `JobStorage` class - Unified storage manager
   - `auto_save_jobs()` - Convenience function

2. **Updated `multi_platform_scraper.py`**
   - Added `auto_save` parameter
   - Added `output_dir` parameter
   - Added `save_formats` parameter
   - Returns dict with DataFrame + saved files when auto_save=True

### Storage Methods

| Method | Format | Description |
|--------|--------|-------------|
| `save_to_csv()` | CSV | Comma-separated values |
| `save_to_excel()` | Excel | Multi-sheet workbook |
| `save_to_json()` | JSON | Structured data |
| `save_to_parquet()` | Parquet | Binary format |
| `save_to_sqlite()` | SQLite | Database |
| `save_to_google_sheets()` | Google Sheets | Cloud spreadsheet |
| `save_to_notion()` | Notion | Database pages |
| `save_all()` | Multiple | Save to all formats |

---

## Examples

### Example 1: Default Auto-Save

```python
from linkedin_scraper.integrations import scrape_multi_platform

result = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="python developer",
    location="Bangalore",
    auto_save=True  # Saves to CSV + Excel
)

# Files created:
# - output/jobs/jobs_20260403_120000.csv
# - output/jobs/jobs_report_20260403_120000.xlsx
```

### Example 2: Custom Formats

```python
result = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="data scientist",
    auto_save=True,
    save_formats=['csv', 'json', 'sqlite']  # Custom formats
)

# Files created:
# - output/jobs/jobs_20260403_120000.csv
# - output/jobs/jobs_20260403_120000.json
# - output/jobs/jobs.db
```

### Example 3: Manual Storage

```python
from linkedin_scraper.integrations import scrape_multi_platform, JobStorage

# Scrape
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="consultant",
    auto_save=False  # Manual
)

# Store manually
storage = JobStorage(output_dir="output/consulting")
storage.save_all(
    df,
    save_csv=True,
    save_excel=True,
    save_json=True
)
```

---

## Summary

| Question | Answer |
|----------|--------|
| **Are jobs stored by default?** | ❌ No, only in DataFrame |
| **How to enable auto-storage?** | Set `auto_save=True` |
| **Where are jobs stored?** | `output/jobs/` directory |
| **What formats?** | CSV + Excel (default), more available |
| **Can I customize storage?** | Yes, use `save_formats` list |
| **Can I use manual storage?** | Yes, use `JobStorage` class |
| **How to access saved files?** | Check `result['saved_files']` |

---

**TL;DR:** Set `auto_save=True` to automatically save jobs to `output/jobs/` in CSV and Excel formats!
