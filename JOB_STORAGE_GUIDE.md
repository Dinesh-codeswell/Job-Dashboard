# Job Storage Guide - Indeed & Naukri Scraper

## Overview

Jobs fetched from Indeed and Naukri can now be **automatically stored** in multiple formats:

- 📄 **Local Files**: CSV, Excel, JSON, Parquet
- 📊 **Google Sheets**: Cloud spreadsheet
- 📝 **Notion**: Database pages
- 💾 **SQLite**: Local database

## Quick Start

### Auto-Save While Scraping

```python
from linkedin_scraper.integrations import scrape_multi_platform

# Scrape and auto-save to CSV + Excel
result = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="software engineer",
    location="Bangalore",
    results_wanted=50,
    auto_save=True,  # Enable auto-save
    output_dir="output/jobs"
)

# Access results
df = result['dataframe']
saved_files = result['saved_files']
print(f"Saved to: {saved_files}")
```

### Manual Save After Scraping

```python
from linkedin_scraper.integrations import (
    scrape_multi_platform,
    JobStorage
)

# Scrape first
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="python developer",
    location="Mumbai"
)

# Then save manually
storage = JobStorage(output_dir="output/jobs")
storage.save_all(
    df,
    save_csv=True,
    save_excel=True,
    save_json=True
)
```

## Storage Options

### 1. CSV Files

Lightweight, universal format.

```python
from linkedin_scraper.integrations import JobStorage

storage = JobStorage(output_dir="output/jobs")
filepath = storage.save_to_csv(df, filename="my_jobs.csv")

# Output: output/jobs/my_jobs.csv
```

**Options:**
- `filename`: Custom filename (auto-generated if not provided)
- `include_timestamp`: Add timestamp to filename (default: True)

### 2. Excel Files

Multi-sheet workbook with summary.

```python
storage = JobStorage(output_dir="output/jobs")
filepath = storage.save_to_excel(
    df,
    filename="jobs_report.xlsx",
    include_summary=True,      # Summary statistics sheet
    split_by_site=True         # Separate sheet per platform
)

# Output sheets:
# - Summary (job counts per platform)
# - All Jobs (combined)
# - Indeed Jobs
# - Naukri Jobs
```

### 3. JSON Files

Structured data format.

```python
filepath = storage.save_to_json(
    df,
    filename="jobs.json",
    orient='records',  # Array of objects
    indent=2
)
```

### 4. Parquet Files

Efficient binary format (great for large datasets).

```python
filepath = storage.save_to_parquet(
    df,
    filename="jobs.parquet"
)
```

**Requirements:** `pip install pyarrow`

### 5. SQLite Database

Queryable local database.

```python
db_path = storage.save_to_sqlite(
    df,
    table_name="jobs",
    database_path="output/jobs.db"
)

# Query later
import sqlite3
conn = sqlite3.connect("output/jobs.db")
df = pd.read_sql("SELECT * FROM jobs WHERE site='indeed'", conn)
```

### 6. Google Sheets ☁️

Cloud-based spreadsheet (requires setup).

```python
storage = JobStorage(
    output_dir="output/jobs",
    google_sheet_id="your-sheet-id",
    google_credentials_file="credentials.json"
)

success = storage.save_to_google_sheets(
    df,
    sheet_name="Indeed Jobs",
    clear_first=False  # Append to existing data
)
```

**Setup Required:**
1. Create Google Cloud project
2. Enable Sheets API
3. Create service account
4. Download credentials JSON
5. Share sheet with service account email

### 7. Notion Database 📝

Add jobs to Notion workspace.

```python
storage = JobStorage(
    output_dir="output/jobs",
    notion_database_id="your-db-id",
    notion_api_key="your-api-key"
)

success = storage.save_to_notion(df)
```

**Setup Required:**
1. Create Notion integration
2. Get API key
3. Share database with integration

## Auto-Save Configuration

### Save to Multiple Formats

```python
result = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="data scientist",
    location="Bangalore",
    auto_save=True,
    output_dir="output/ds_jobs",
    save_formats=['csv', 'excel', 'sqlite']  # Multiple formats
)

print(result['saved_files'])
# {
#   'csv': 'output/ds_jobs/jobs_20260403_120000.csv',
#   'excel': 'output/ds_jobs/jobs_report_20260403_120000.xlsx',
#   'sqlite': 'output/ds_jobs/jobs.db'
# }
```

### Available Formats

- `'csv'` - CSV file
- `'excel'` - Excel workbook
- `'json'` - JSON file
- `'parquet'` - Parquet file
- `'sqlite'` - SQLite database
- `'google_sheets'` - Google Sheets (requires config)

## JobStorage Class Reference

### Initialize

```python
storage = JobStorage(
    output_dir="output/jobs",           # Local files directory
    google_sheet_id="sheet-id",         # Optional
    google_credentials_file="creds.json", # Optional
    notion_database_id="db-id",         # Optional
    notion_api_key="api-key"            # Optional
)
```

### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `save_to_csv(df)` | Save to CSV | File path |
| `save_to_excel(df)` | Save to Excel | File path |
| `save_to_json(df)` | Save to JSON | File path |
| `save_to_parquet(df)` | Save to Parquet | File path |
| `save_to_sqlite(df)` | Save to SQLite | DB path |
| `save_to_google_sheets(df)` | Save to Sheets | bool |
| `save_to_notion(df)` | Save to Notion | bool |
| `save_all(df, ...)` | Save to multiple formats | Dict[format→path] |

### save_all() Parameters

```python
storage.save_all(
    df,
    save_csv=True,           # Save CSV
    save_excel=True,         # Save Excel
    save_json=False,         # Save JSON
    save_parquet=False,      # Save Parquet
    save_sqlite=False,       # Save SQLite
    save_google_sheets=False,# Save to Sheets
    save_notion=False        # Save to Notion
)
```

## Convenience Function

### auto_save_jobs()

Quick auto-save without creating storage object:

```python
from linkedin_scraper.integrations import auto_save_jobs

df = scrape_multi_platform(["indeed", "naukri"], "python")

# Auto-save to CSV + Excel
saved = auto_save_jobs(
    df,
    output_dir="output/jobs",
    formats=['csv', 'excel']
)

print(saved)
# {'csv': 'path/to/file.csv', 'excel': 'path/to/file.xlsx'}
```

## Examples

### Example 1: Basic Auto-Save

```python
from linkedin_scraper.integrations import scrape_multi_platform

result = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="software engineer",
    location="Bangalore",
    results_wanted=50,
    auto_save=True  # Saves to CSV + Excel by default
)

print(f"Total jobs: {result['total_jobs']}")
print(f"Files: {result['saved_files']}")
```

### Example 2: Save to All Formats

```python
result = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="data analyst",
    auto_save=True,
    save_formats=['csv', 'excel', 'json', 'parquet', 'sqlite']
)

# Check all saved locations
for format_type, path in result['saved_files'].items():
    print(f"{format_type}: {path}")
```

### Example 3: Google Sheets Integration

```python
result = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="consultant",
    location="Gurugram",
    auto_save=True,
    save_formats=['csv', 'excel', 'google_sheets'],
    google_sheet_id="1abc123xyz...",
    google_credentials_file="credentials.json"
)
```

### Example 4: Scheduled Scraping with Storage

```python
# scheduled_scraper.py
from linkedin_scraper.integrations import scrape_multi_platform, JobStorage
from datetime import datetime

# Scrape daily
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="python developer",
    location="Remote",
    results_wanted=100
)

# Save with date-stamped filename
date_str = datetime.now().strftime("%Y%m%d")
storage = JobStorage(output_dir="output/daily")

storage.save_to_csv(
    df,
    filename=f"python_jobs_{date_str}.csv"
)

storage.save_to_sqlite(
    df,
    table_name="daily_jobs"
)
```

### Example 5: Manual Storage with Custom Logic

```python
from linkedin_scraper.integrations import scrape_multi_platform, JobStorage

df = scrape_multi_platform(["indeed", "naukri"], "machine learning")

storage = JobStorage(output_dir="output/ml_jobs")

# Save all jobs
storage.save_all(df, save_csv=True, save_excel=True)

# Save per-platform
for site in df['site'].unique():
    site_df = df[df['site'] == site]
    storage.save_to_csv(site_df, filename=f"{site}_jobs.csv")

# Save only remote jobs
remote_df = df[df['is_remote'] == True]
if len(remote_df) > 0:
    storage.save_to_csv(remote_df, filename="remote_jobs.csv")
```

## File Organization

Recommended structure:

```
output/
├── jobs/
│   ├── jobs_20260403_120000.csv
│   ├── jobs_report_20260403_120000.xlsx
│   └── jobs.db
├── indeed/
│   └── indeed_jobs.csv
├── naukri/
│   └── naukri_jobs.csv
└── daily/
    ├── python_jobs_20260403.csv
    └── java_jobs_20260403.csv
```

## Best Practices

1. **Use auto_save for simplicity**: Set `auto_save=True` in scrape function
2. **Choose appropriate formats**:
   - CSV for sharing/analysis
   - Excel for reports
   - SQLite for querying
   - Parquet for large datasets
3. **Timestamp filenames**: Prevent overwrites
4. **Organize by search**: Separate folders for different searches
5. **Backup important data**: Use Google Sheets for cloud backup

## Troubleshooting

### CSV/Excel not saving

Check write permissions:
```python
from pathlib import Path
Path("output/jobs").mkdir(parents=True, exist_ok=True)
```

### Google Sheets error

Verify credentials:
```python
from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration

integration = GoogleSheetsIntegration(
    sheet_id="your-id",
    credentials_file="credentials.json"
)
```

### Notion error

Check database sharing:
- Open Notion database
- Click "..." → "Connect to"
- Select your integration

### SQLite locked

Close other connections:
```python
import sqlite3
conn = sqlite3.connect("jobs.db")
conn.close()
```

## Migration from Old Code

**Before (no auto-save):**
```python
df = scrape_multi_platform(["indeed", "naukri"], "python")
save_jobs_to_csv(df, "jobs.csv")  # Manual
```

**After (with auto-save):**
```python
result = scrape_multi_platform(
    ["indeed", "naukri"],
    "python",
    auto_save=True  # Automatic!
)
```

## Summary

| Storage Type | Best For | Setup Required |
|--------------|----------|----------------|
| CSV | Quick analysis, sharing | None |
| Excel | Reports, stakeholders | None |
| JSON | APIs, web apps | None |
| Parquet | Large datasets | `pip install pyarrow` |
| SQLite | Queries, persistence | None |
| Google Sheets | Collaboration, cloud | Google Cloud setup |
| Notion | Workflow integration | Notion integration |

---

**Happy Scraping & Storing! 🚀**
