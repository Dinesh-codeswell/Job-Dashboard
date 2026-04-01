# Setup Complete! 🎉

Your LinkedIn Jobs to Notion scraper is ready to use. Here's what was set up:

---

## Files Created

1. **`scrape_india_jobs_notion.py`** - Main scraper script
   - Searches LinkedIn for core technical/business roles in India
   - Filters jobs posted in the past 24 hours
   - Excludes basic roles (accountant, copywriter, video editor, etc.)
   - Stores jobs in your Notion database

2. **`linkedin_scraper/integrations/notion.py`** - Notion integration module
   - Handles connection to Notion API
   - Adds jobs to your database
   - Checks for duplicates

3. **`.env.example.notion`** - Environment variables template
   - Copy to `.env` and add your Notion credentials

4. **`NOTION_SETUP.md`** - Detailed Notion setup guide
   - Step-by-step instructions for creating database
   - How to create Notion integration
   - How to get database ID

5. **`NOTION_JOBS_README.md`** - Quick reference guide
   - Usage examples
   - Command options
   - Troubleshooting

6. **`requirements.txt`** - Updated with `notion-client` dependency

---

## What You Need to Do in Notion

### 1. Create a Database

1. Go to Notion and create a new page
2. Type `/database` and select **Database - Table**
3. Name it "LinkedIn Jobs - India" or similar

### 2. Add These Columns

Your database MUST have these exact columns:

| Column Name | Type |
|-------------|------|
| Company | Title (default) |
| Role | Rich text |
| Date Added | Date |
| Location | Rich text |
| URL | URL |

### 3. Create Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click **+ New integration**
3. Name it "LinkedIn Job Scraper"
4. Copy the **Internal Integration Token** (starts with `secret_...`)

### 4. Connect Integration to Database

1. Open your database in Notion
2. Click **⋯** (three dots) → **Add connections**
3. Select your integration

### 5. Get Database ID

1. Open your database
2. Copy the ID from the URL (between workspace name and `?v=`)
   - Example: `https://www.notion.so/workspace/a1b2c3d4e5f6...?v=xyz`
   - Database ID: `a1b2c3d4e5f6...`

---

## Configuration

### Step 1: Copy Environment Template

```bash
copy .env.example.notion .env
```

### Step 2: Edit `.env`

```env
NOTION_API_KEY=secret_your_actual_token_here
NOTION_DATABASE_ID=your_actual_database_id_here
```

---

## Usage

### Basic Run

```bash
python scrape_india_jobs_notion.py
```

### With Options

```bash
# More jobs per keyword
python scrape_india_jobs_notion.py --limit 20

# Specific city
python scrape_india_jobs_notion.py --location Bangalore

# Specific keywords
python scrape_india_jobs_notion.py --keywords "SDE" "Product Manager"

# Visible browser (for debugging)
python scrape_india_jobs_notion.py --headless False
```

---

## Target Roles

### ✅ Included (Core Technical/Business)
- SDE, Software Engineer, Backend/Frontend/Full Stack
- Product Manager (PM), Associate Product Manager (APM)
- Data Analyst, Business Analyst
- Data Scientist, ML Engineer, AI Engineer
- Growth Manager, Strategy Manager
- Technical Program Manager (TPM)
- Solutions Architect, DevOps, SRE
- Product Designer, UX Designer
- Management/Technology Consultant

### ❌ Excluded (Basic Roles)
- Accountant, Accounting
- Copywriter, Content Writer
- Video Editor
- Data Entry
- Customer Support, Telecaller
- Basic Sales Executive
- HR Executive, Recruiter
- Social Media Manager, SEO

---

## How It Works

```
1. Search LinkedIn for each keyword in India
   ↓
2. For each job found:
   ├─ Check if posted within 24 hours
   ├─ Check if it's a core role (not excluded)
   ├─ Check if already in Notion (duplicate)
   └─ Add to Notion if all checks pass
   ↓
3. Summary report
```

---

## Example Output in Notion

| Company | Role | Date Added | Location | URL |
|---------|------|------------|----------|-----|
| Google | SDE II | 2024-01-15 | Bangalore | https://... |
| Microsoft | Product Manager | 2024-01-15 | Hyderabad | https://... |
| Amazon | Data Scientist | 2024-01-15 | Mumbai | https://... |

---

## Next Steps

1. ✅ **Set up Notion database** (see NOTION_SETUP.md)
2. ✅ **Create `.env` file** with your credentials
3. ✅ **Ensure LinkedIn session exists** (`linkedin_session.json`)
   - If not, run: `python samples/create_session.py`
4. ✅ **Test run**: `python scrape_india_jobs_notion.py --headless False`

---

## Troubleshooting

### "Failed to connect to Notion"
- Check `NOTION_API_KEY` starts with `secret_`
- Verify integration is connected to database
- Check database ID is correct

### "No jobs added"
- Jobs must be posted in past 24 hours (try running morning/evening)
- Check LinkedIn session is valid
- Review excluded roles - some jobs may be filtered

### Import errors
- Run: `pip install notion-client`

---

## Automation (Optional)

Create `run_jobs_scraper.bat`:

```batch
@echo off
cd /d C:\linkedin_scraper
C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe scrape_india_jobs_notion.py --limit 15
pause
```

Run this daily or schedule with Windows Task Scheduler!

---

## Documentation Files

- **NOTION_SETUP.md** - Detailed Notion setup (read this first)
- **NOTION_JOBS_README.md** - Quick reference guide
- **.env.example.notion** - Environment template

---

**Ready to start scraping! 🚀**

For detailed setup instructions, see **NOTION_SETUP.md**
