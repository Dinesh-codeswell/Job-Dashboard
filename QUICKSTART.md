# 🚀 QUICK START - LinkedIn Job Scraper to Google Sheets

## ✅ What's Already Set Up

| Component | Status |
|-----------|--------|
| Python 3.11 | ✅ Installed |
| Project dependencies | ✅ Installed |
| Playwright Chromium | ✅ Installed |
| LinkedIn session | ✅ Created (`linkedin_session.json`) |
| Google Sheets libraries | ✅ Installed |
| Workflow scripts | ✅ Created |

## ⚡ What You Need to Do

### 1. Set Up Google Sheets API (5 minutes)

**Option A: Interactive Setup (Recommended)**
```bash
python setup_google_sheets.py
```
Follow the prompts to configure.

**Option B: Manual Setup**

1. **Get Google Credentials:**
   - Go to https://console.cloud.google.com/
   - Create a new project
   - Enable "Google Sheets API"
   - Create a service account
   - Download JSON key as `credentials.json` in project folder

2. **Create & Share Google Sheet:**
   - Create a new Google Sheet at https://sheets.google.com/
   - Copy the Sheet ID from URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`
   - Share the sheet with the service account email (from credentials.json)

3. **Update .env file:**
   ```
   GOOGLE_SHEET_ID=your_sheet_id_here
   ```

### 2. Run the Job Scraper

```bash
# Search for jobs and upload to Google Sheets
python jobs_to_sheets.py -k "software engineer" -l "San Francisco" --limit 10
```

That's it! Jobs will be scraped from LinkedIn and automatically uploaded to your Google Sheet.

## 📋 Available Commands

```bash
# Basic search
python jobs_to_sheets.py -k "python developer" -l "Remote"

# Scrape more jobs
python jobs_to_sheets.py -k "data scientist" --limit 20

# Show browser window (debug mode)
python jobs_to_sheets.py -k "product manager" --headless False

# Skip duplicate checking
python jobs_to_sheets.py -k "frontend" --no-dedup

# Custom worksheet name
python jobs_to_sheets.py -k "backend" --worksheet "Engineering Jobs"
```

## 📊 Google Sheets Output

Your sheet will have these columns:
- Job Title
- Company
- Location
- Posted Date
- Applicant Count
- Job URL
- Company URL
- Description
- Benefits
- Date Added

## 🔧 Troubleshooting

**"credentials.json not found"**
→ Follow the Google Sheets setup in `GOOGLE_SHEETS_SETUP.md`

**"Rate limit detected"**
→ Wait a few hours, then try again with a lower limit

**"Session expired"**
→ Run `python samples\create_session.py` to create a new session

## 📖 Documentation

- `JOB_SCRAPER_WORKFLOW.md` - Complete usage guide
- `GOOGLE_SHEETS_SETUP.md` - Google Sheets API setup details
- `README.md` - Main project documentation

## ⚠️ Important Files (Keep Private!)

These files contain authentication credentials - never share them:
- `credentials.json` - Google API credentials
- `linkedin_session.json` - LinkedIn session cookies
- `.env` - Your configuration

They're already in `.gitignore` to prevent accidental commits.

---

**Ready to start scraping!** 🎉

Run: `python jobs_to_sheets.py -k "your_job_title" -l "your_location"`
