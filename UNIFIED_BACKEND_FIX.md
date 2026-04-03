# Unified Backend Fix - Job Fetching from 3 Sheets

## Problem Identified

The API endpoints were not fetching jobs from the three spreadsheets (LinkedIn_Jobs, Indeed_Jobs, Naukri_Jobs) because:

### Root Cause
There were **TWO different data fetchers** in the codebase:

1. **`dashboard/data/sheets_fetcher.py`** ✅ - The **unified fetcher** that fetches from ALL 3 sheets
2. **`api/data_fetcher.py`** ❌ - The **old single-sheet fetcher** that only fetches from ONE worksheet

### The Issue
- **`api/index.py`** (Vercel API) was importing from **`data_fetcher.py`** (the old single-sheet version) ❌
- **`dashboard/app.py`** (local Flask app) was importing from **`data/sheets_fetcher.py`** (the unified version) ✅

This meant:
- ✅ Local development worked fine (using `dashboard/app.py`)
- ❌ Vercel deployment didn't work (using `api/index.py` with old fetcher)

## Solution Applied

Updated **`api/index.py`** to use the unified `dashboard/data/sheets_fetcher.py` instead of the old `api/data_fetcher.py`.

### Changes Made

**File: `api/index.py`**

The `get_fetcher()` function now:
1. Tries to import from `dashboard/data/sheets_fetcher.py` (unified version)
2. Adds fallback mechanisms for Vercel serverless environment
3. Provides clear console output showing which fetcher is being used

Key improvements:
```python
# Now imports the unified fetcher
from sheets_fetcher import get_data_fetcher  # Fetches from all 3 sheets
```

## How It Works Now

### Data Flow (Fixed)

```
FRONTEND REQUEST
    ↓
API ENDPOINT (api/index.py)
    ↓
get_fetcher()
    ↓
SheetsDataFetcher (dashboard/data/sheets_fetcher.py) ✅ UNIFIED
    ↓
fetch_all_jobs()
    ├─→ LinkedIn_Jobs sheet
    ├─→ Indeed_Jobs sheet
    ├─→ Naukri_Jobs sheet
    └─→ Merge all jobs, sort by date, cache
    ↓
Return unified job list to frontend
```

### Unified Fetcher Features

The `SheetsDataFetcher` in `dashboard/data/sheets_fetcher.py`:

1. **Fetches from multiple worksheets** in order:
   - Primary: `LinkedIn_Jobs`, `Indeed_Jobs`, `Naukri_Jobs`
   - Fallback: `Consulting_Jobs_India`, `Jobs`, `Consulting Jobs India`
   - Dynamic: Any other worksheets found in the spreadsheet

2. **Adds source tracking**: Each job gets a `source` field (e.g., "linkedin", "indeed", "naukri")

3. **In-memory caching**: Prevents repeated API calls to Google Sheets

4. **Search and filtering**: Supports query, city, and employment type filters

## Testing the Fix

### Local Testing

1. **Start the local Flask dashboard**:
   ```bash
   cd C:\Linkedin_scraper\dashboard
   python app.py
   ```

2. **Check the API response**:
   ```bash
   curl http://localhost:5000/api/jobs
   ```

3. **Check stats endpoint**:
   ```bash
   curl http://localhost:5000/api/stats
   ```

4. **Refresh data** (clears cache):
   ```bash
   curl -X POST http://localhost:5000/api/refresh
   ```

### Vercel Deployment Testing

After deploying to Vercel:

1. **Check health endpoint**:
   ```
   https://your-app.vercel.app/api/health
   ```

2. **Check jobs endpoint**:
   ```
   https://your-app.vercel.app/api/jobs
   ```

3. **Check logs in Vercel**:
   - Go to your Vercel dashboard
   - Check the function logs
   - Look for: `✅ Using unified data fetcher (fetches from LinkedIn_Jobs, Indeed_Jobs, Naukri_Jobs)`
   - Look for: `✅ Total fetched X jobs from all sources`

### Expected Console Output

When the API starts, you should see:
```
✅ Using unified data fetcher (fetches from LinkedIn_Jobs, Indeed_Jobs, Naukri_Jobs)
✅ Using credentials from file: credentials.json
✅ Unified fetcher initialized - will fetch from LinkedIn_Jobs, Indeed_Jobs, Naukri_Jobs
```

When fetching jobs:
```
📊 Available worksheets: ['LinkedIn_Jobs', 'Indeed_Jobs', 'Naukri_Jobs', 'Summary']
📊 Trying to fetch from worksheet: LinkedIn_Jobs
✅ Found 50 jobs in LinkedIn_Jobs
✅ Successfully fetched 50 jobs from LinkedIn_Jobs
📊 Trying to fetch from worksheet: Indeed_Jobs
✅ Found 30 jobs in Indeed_Jobs
✅ Successfully fetched 30 jobs from Indeed_Jobs
📊 Trying to fetch from worksheet: Naukri_Jobs
✅ Found 20 jobs in Naukri_Jobs
✅ Successfully fetched 20 jobs from Naukri_Jobs
✅ Total fetched 100 jobs from all sources
```

## Troubleshooting

### No Jobs Showing

1. **Check credentials**:
   ```bash
   curl https://your-app.vercel.app/api/health
   ```
   Should return: `{"status": "healthy", "jobs_count": X}`

2. **Check sheet names**: Ensure your Google Sheets has worksheets named exactly:
   - `LinkedIn_Jobs` (case-sensitive)
   - `Indeed_Jobs`
   - `Naukri_Jobs`

3. **Check GOOGLE_SHEET_ID**: Verify it's set correctly in `.env` or Vercel environment variables

4. **Force refresh**:
   ```bash
   curl -X POST https://your-app.vercel.app/api/refresh
   ```

### Import Errors

If you see import errors in Vercel logs, the fallback mechanisms should handle it:
- Tries `dashboard/data/sheets_fetcher.py` first
- Falls back to loading from file path directly
- Check logs for which method was used

### Performance Issues

The unified fetcher has built-in caching (60 seconds by default). To adjust:
- Modify `cache_timeout` parameter in `fetch_all_jobs()`
- Default is 60 seconds for jobs, 120 seconds for stats

## Next Steps

1. ✅ **Deploy to Vercel**: Push your changes
2. ✅ **Monitor logs**: Check Vercel function logs for successful initialization
3. ✅ **Test frontend**: Verify jobs appear in the dashboard
4. ✅ **Optional**: Delete or archive `api/data_fetcher.py` to avoid confusion

## Files Modified

- `api/index.py` - Updated to use unified fetcher

## Files to Keep

- ✅ `dashboard/data/sheets_fetcher.py` - The unified fetcher (KEEP)
- ✅ `dashboard/app.py` - Local Flask app (KEEP)
- ✅ `api/index.py` - Vercel API (UPDATED)
- ⚠️ `api/data_fetcher.py` - Old single-sheet fetcher (CAN BE DELETED/ARCHIVED)

## Architecture Summary

```
SCRAPING (Write):
  scrape_all_india_jobs.py
    ├─→ LinkedIn_Jobs sheet
    ├─→ Indeed_Jobs sheet
    └─→ Naukri_Jobs sheet

DASHBOARD (Read) - NOW UNIFIED:
  Frontend → API (api/index.py OR dashboard/app.py)
    → get_fetcher()
    → SheetsDataFetcher (dashboard/data/sheets_fetcher.py)
      → fetch_all_jobs() from ALL 3 sheets
      → Merge, sort, cache
      → Return unified results
```

---

**Date Fixed**: 2026-04-03
**Status**: ✅ Ready for deployment
