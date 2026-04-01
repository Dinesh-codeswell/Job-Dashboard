# ✅ Your Setup is Ready!

## Your Notion Database Configuration

**Database Name:** High Growth Roles Tracker  
**Database ID:** `2e7e82acc24f80f781f1ef088dbff443`  
**URL:** https://www.notion.so/High-Growth-Roles-Tracker-Updated-every-hour-2e7e82acc24f80f781f1ef088dbff443

### Columns (Already Configured ✅)

| Column Name | Type | Purpose |
|-------------|------|---------|
| Company | Rich text | Company name (e.g., "Google", "Microsoft") |
| Position | Rich text | Job title (e.g., "SDE", "Product Manager") |
| Date Posted | Date (YYYY/MM/DD) | **Date added to your tracker** (not LinkedIn posting date) |
| Location | Rich text | Job location (e.g., "Bangalore", "Remote") |
| Application Link | URL | LinkedIn job URL |

---

## Quick Start - 3 Steps

### Step 1: Create Notion Integration

1. Go to: https://www.notion.so/my-integrations
2. Click **+ New integration**
3. Name: "LinkedIn Job Scraper"
4. Copy the token (starts with `secret_...`)

### Step 2: Connect Integration to Database

1. Open your database: https://www.notion.so/High-Growth-Roles-Tracker-Updated-every-hour-2e7e82acc24f80f781f1ef088dbff443
2. Click **⋯** (three dots) in top-right
3. Scroll down → **Add connections**
4. Select "LinkedIn Job Scraper" (your integration)
5. Click **Confirm**

### Step 3: Configure .env File

1. Copy the template:
   ```bash
   copy .env.example.notion .env
   ```

2. Edit `.env` and add your integration token:
   ```env
   NOTION_API_KEY=secret_your_actual_token_here
   NOTION_DATABASE_ID=2e7e82acc24f80f781f1ef088dbff443
   ```

3. Save the file

---

## Run the Scraper

### Option 1: Double-click the batch file
```
run_notion_scraper.bat
```

### Option 2: Command line
```bash
python scrape_india_jobs_notion.py
```

### With options:
```bash
# More jobs per keyword
python scrape_india_jobs_notion.py --limit 20

# Specific city
python scrape_india_jobs_notion.py --location Bangalore

# Visible browser (debug)
python scrape_india_jobs_notion.py --headless False
```

---

## What Gets Scraped

### ✅ Target Roles (Core Technical/Business)
- SDE, Software Engineer, Backend/Frontend/Full Stack
- Product Manager (PM), Associate Product Manager (APM)
- Data Analyst, Business Analyst, Product Analyst
- Data Scientist, ML Engineer, AI Engineer
- Growth Manager, Strategy Manager, Operations Manager
- Technical Program Manager (TPM)
- Solutions Architect, Cloud Architect, DevOps, SRE
- Product Designer, UX Designer
- Management Consultant, Technology Consultant

### ❌ Excluded Roles
- Accountant, Accounting
- Copywriter, Content Writer
- Video Editor
- Data Entry
- Customer Support, Telecaller
- Basic Sales Executive
- HR Executive, Recruiter
- Social Media Manager, SEO

---

## Filters Applied

1. **Location:** India (or specific city if specified)
2. **Time:** Posted in past 24 hours only
3. **Role Type:** Core technical/business roles only
4. **Duplicates:** Skips jobs already in your Notion

---

## Example Output

After running, your Notion will have entries like:

| Company | Position | Date Posted | Location | Application Link |
|---------|----------|-------------|----------|------------------|
| Google | SDE II | 2024-01-15 | Bangalore | https://... |
| Microsoft | Product Manager | 2024-01-15 | Hyderabad | https://... |
| Amazon | Data Scientist | 2024-01-15 | Mumbai | https://... |

> **Note:** "Date Posted" = today's date (when you added it to tracker)

---

## Automation (Recommended)

### Run Daily with Windows Task Scheduler

1. Open **Task Scheduler**
2. **Create Basic Task** → "LinkedIn Jobs Scraper"
3. **Trigger:** Daily at 9:00 AM
4. **Action:** Start a program
   - Program: `C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe`
   - Arguments: `scrape_india_jobs_notion.py --limit 15`
   - Start in: `C:\linkedin_scraper`

### Or use the batch file
Create a scheduled task to run:
```
C:\linkedin_scraper\run_notion_scraper.bat
```

---

## Troubleshooting

### "Failed to connect to Notion"
- ✅ Check `NOTION_API_KEY` starts with `secret_`
- ✅ Verify integration is connected to database
- ✅ Database ID is correct: `2e7e82acc24f80f781f1ef088dbff443`

### "No jobs added"
- Jobs must be posted in past 24h (try running morning/evening)
- Check LinkedIn session exists (`linkedin_session.json`)
- If no session: `python samples/create_session.py`

### "Column mismatch error"
- Your columns are already correct! This shouldn't happen.

---

## Next Steps

1. ✅ **Create Notion integration** (Step 1 above)
2. ✅ **Connect to database** (Step 2 above)
3. ✅ **Create .env file** (Step 3 above)
4. ✅ **Test run:** `python scrape_india_jobs_notion.py --headless False`

---

**You're all set! Happy job hunting! 🚀**

For detailed docs:
- `NOTION_SETUP.md` - Full Notion setup guide
- `NOTION_JOBS_README.md` - Quick reference
