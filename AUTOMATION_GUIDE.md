# 🤖 Automated Job Scraper Setup Guide

## Overview

Your LinkedIn, Indeed, and Naukri job scraper now runs **automatically every 15 minutes** without any manual intervention needed!

---

## 📋 What Was Created

### Core Files

1. **`auto_scraper.py`** - The automated runner script
   - Handles error recovery
   - Comprehensive logging
   - Prerequisites checking
   - Runs the unified scraper (LinkedIn + Indeed + Naukri)

2. **`setup_automation.bat`** - One-time setup script
   - Creates Windows Task Scheduler task
   - Configures 15-minute intervals
   - Runs with SYSTEM privileges

3. **`automation_manager.bat`** - Management console
   - Start/Stop/Status controls
   - View logs
   - Manual execution
   - Interactive menu

4. **`logs/`** directory - Automatic log storage
   - Daily log files: `scraper_YYYY_MM_DD.log`
   - Persistent history of all runs

---

## 🚀 Quick Start (One-Time Setup)

### Step 1: Run Setup (Administrator Required)

```
Right-click: setup_automation.bat
Select: "Run as administrator"
```

This will:
- Create a scheduled task named `LinkedInJobsScraper_Auto`
- Set it to run every 15 minutes
- Configure it to run as SYSTEM (works even when you're logged out)

### Step 2: Verify Setup

```
automation_manager.bat status
```

You should see:
- ✅ Task is ENABLED
- Next scheduled run time
- Task configuration details

---

## 📊 Managing the Automation

### Interactive Menu

```
automation_manager.bat
```

This shows a menu with options:
1. Start automation
2. Stop automation
3. Check status
4. Restart automation
5. View recent logs
6. Run scraper manually
7. Help
0. Exit

### Command-Line Usage

```bash
# Check current status
automation_manager.bat status

# Stop automation
automation_manager.bat stop

# Start automation
automation_manager.bat start

# Restart automation
automation_manager.bat restart

# View logs
automation_manager.bat logs
```

---

## 📁 File Structure

```
linkedin_scraper/
├── auto_scraper.py              # Automated runner (called by scheduler)
├── scrape_all_india_jobs.py     # Main scraper (called by auto_scraper.py)
├── setup_automation.bat         # One-time setup script
├── automation_manager.bat       # Management console
├── AUTOMATION_GUIDE.md          # This file
├── .env                         # Configuration (credentials, settings)
├── credentials.json             # Google Sheets API credentials
├── linkedin_session.json        # LinkedIn session (auto-loads)
└── logs/                        # Created automatically
    ├── scraper_2026_04_03.log   # Today's logs
    ├── scraper_2026_04_02.log   # Yesterday's logs
    └── ...
```

---

## ⚙️ How It Works

### Schedule Flow

```
Every 15 minutes
    ↓
Windows Task Scheduler triggers
    ↓
Runs: python auto_scraper.py
    ↓
auto_scraper.py:
    ├─ Checks prerequisites (.env, credentials, session)
    ├─ Imports UnifiedIndiaJobsScraper
    ├─ Runs scraper (LinkedIn + Indeed + Naukri)
    ├─ Uploads to Google Sheets
    └─ Logs results
    ↓
Waits 15 minutes
    ↓
Repeats
```

### What Gets Scraped

- **Platforms**: LinkedIn, Indeed, Naukri
- **Cities**: All cities configured in `.env` (default: 6 major cities)
- **Keywords**: 36+ consulting roles + internships
- **Time Filter**: Last 48 hours
- **Limit**: 30 jobs per keyword per city
- **Output**: Google Sheets (separate tabs per platform)

---

## 🔧 Configuration

### Adjust Scrape Frequency

To change from 15 minutes to something else:

```bash
# Open Task Scheduler
taskschd.msc

# Find: LinkedInJobsScraper_Auto
# Right-click → Properties → Triggers
# Edit the trigger to your preferred interval
```

Or recreate with different interval:
```bash
# Stop current automation
automation_manager.bat stop

# Edit setup_automation.bat, change: /mo 15 to your value
# Then run setup again
automation_manager.bat start
```

### Adjust Search Parameters

Edit `.env` file:

```env
# Cities to search
DEFAULT_CITIES=Chennai,Mumbai,Pune,Gurugram,Bangalore,Hyderabad

# Jobs per keyword per city
DEFAULT_RESULTS_PER_CITY=30

# Time filter (hours)
DEFAULT_HOURS_OLD=48

# Job boards to scrape
DEFAULT_JOB_BOARDS=naukri,indeed,linkedin
```

### Modify Keywords

Edit `scrape_all_india_jobs.py`:
- Line ~70: `CONSULTING_KEYWORDS` list
- Line ~100: `INTERNSHIP_KEYWORDS` list

---

## 📖 Viewing Logs

### Via Management Console

```
automation_manager.bat logs
```

Shows the latest log file with last entries.

### Manually

```
# Open logs directory
start logs

# Or view specific day's log
type logs\scraper_2026_04_03.log
```

### Log File Contents

Each run logs:
```
2026-04-03 14:00:00 - INFO - ======================================================================
2026-04-03 14:00:00 - INFO - 🔍 CHECKING PREREQUISITES
2026-04-03 14:00:00 - INFO - ======================================================================
2026-04-03 14:00:01 - INFO - ✓ .env file found
2026-04-03 14:00:01 - INFO - ✓ Google credentials file found: credentials.json
2026-04-03 14:00:01 - INFO - ✓ LinkedIn session file found
2026-04-03 14:00:01 - INFO - ✓ Required environment variables set
2026-04-03 14:00:01 - INFO - ✅ All prerequisites met
2026-04-03 14:00:01 - INFO - ======================================================================
2026-04-03 14:00:01 - INFO - 🚀 STARTING AUTOMATED JOB SCRAPER
...
2026-04-03 14:15:30 - INFO - ✅ AUTOMATED RUN COMPLETED SUCCESSFULLY
2026-04-03 14:15:30 - INFO - ⏱️  Duration: 930.45 seconds (15.5 minutes)
```

---

## ⚠️ Troubleshooting

### Problem: Task doesn't run

**Solution 1:** Check task status
```bash
automation_manager.bat status
```

**Solution 2:** Verify prerequisites
```bash
# Check if these files exist
dir .env credentials.json linkedin_session.json
```

**Solution 3:** Run manually to see errors
```bash
python auto_scraper.py
```

**Solution 4:** Check Windows Task Scheduler
```bash
taskschd.msc
# Find: LinkedInJobsScraper_Auto
# Check "Last Run Result" - should be 0x0
```

### Problem: LinkedIn scraping fails

**Solution:** Refresh session
```bash
python samples\create_session.py
```

Session expires every 1-2 weeks. The automation will continue with Indeed/Naukri even if LinkedIn fails.

### Problem: Google Sheets errors

**Solutions:**
1. Verify `credentials.json` exists
2. Check `GOOGLE_SHEET_ID` in `.env`
3. Ensure sheet is shared with service account email

Test connection:
```bash
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('LinkedIn_Jobs'); print('Connected!')"
```

### Problem: Rate limiting / IP blocks

**Solutions:**
1. Reduce `DEFAULT_RESULTS_PER_CITY` in `.env` (try 10-15)
2. Increase time between runs (change to 30 minutes)
3. Wait 2-3 hours, then restart automation

### Problem: Task runs but no jobs found

**Check:**
1. Keywords match job titles on these platforms
2. Cities are spelled correctly in `.env`
3. Time filter isn't too restrictive (try `DEFAULT_HOURS_OLD=72`)

### Problem: High error rate in logs

**Common causes:**
- LinkedIn session expired → Re-run `create_session.py`
- Network issues → Check internet connection
- API rate limits → Reduce frequency or results per city

---

## 🔐 Security Notes

### Credentials Storage

- `.env` file contains sensitive data - never commit to Git
- `credentials.json` for Google Sheets - keep secure
- `linkedin_session.json` contains LinkedIn auth - protect it

### Task Scheduler Security

The task runs as **SYSTEM** user:
- ✅ Works even when you're logged out
- ✅ No visible browser windows
- ✅ Runs with elevated privileges
- ⚠️ Ensure your `.env` file has correct permissions

### Best Practices

1. **Weekly**: Check logs for errors
   ```bash
   automation_manager.bat logs
   ```

2. **Bi-weekly**: Refresh LinkedIn session
   ```bash
   python samples\create_session.py
   ```

3. **Monthly**: Review and update keywords/cities

4. **As needed**: Monitor Google Sheets for data quality

---

## 📈 Monitoring & Maintenance

### Daily (Automated)

- Scraper runs every 15 minutes
- Jobs uploaded to Google Sheets
- Logs written to `logs/` directory

### Weekly (Your Action)

1. Check logs for errors:
   ```bash
   automation_manager.bat logs
   ```

2. Review Google Sheets for new jobs

3. Refresh LinkedIn session if needed

### Monthly (Your Action)

1. Review and optimize keywords
2. Check if cities need updating
3. Clean up old log files
4. Verify Google Sheets quota usage

---

## 🎯 Example Workflow

### Morning Check (5 minutes)

```bash
# Open management console
automation_manager.bat

# Check status (option 3)
# View logs (option 5)
# Exit (option 0)

# Open Google Sheets to see new jobs
```

### If Something Goes Wrong

```bash
# Stop automation
automation_manager.bat stop

# Run manually to diagnose
python auto_scraper.py

# Fix any issues shown

# Restart automation
automation_manager.bat start
```

### Weekly Maintenance

```bash
# Refresh LinkedIn session
python samples\create_session.py

# Check logs for patterns
automation_manager.bat logs

# Verify Google Sheets data
```

---

## 📞 Common Commands Reference

```bash
# Quick status check
automation_manager.bat status

# Stop automation temporarily
automation_manager.bat stop

# Restart after fixing issues
automation_manager.bat start

# View what's happening
automation_manager.bat logs

# Run scraper right now (not waiting for schedule)
automation_manager.bat
# Then select option 6

# Get help
automation_manager.bat help
```

---

## 🎉 You're All Set!

Your job scraper now runs **completely automatically**:

✅ Every 15 minutes  
✅ No manual intervention needed  
✅ Automatic error handling  
✅ Comprehensive logging  
✅ Easy management tools  
✅ Works even when you're logged out  

Just check your Google Sheets regularly for new jobs! 📊

---

**Created**: April 3, 2026  
**Version**: 1.0  
**Task Name**: LinkedInJobsScraper_Auto
