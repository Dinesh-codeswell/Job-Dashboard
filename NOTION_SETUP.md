# Notion Integration Setup Guide

This guide walks you through setting up Notion to receive LinkedIn job listings scraped by the India Jobs Scraper.

## Overview

The scraper stores jobs in a Notion database (table) with the following columns:
| Column Name | Type | Description |
|-------------|------|-------------|
| Company | Rich text | Company name |
| Position | Rich text | Job title/role |
| Date Posted | Date (YYYY/MM/DD) | When the job was added to the dashboard (not posting date) |
| Location | Rich text | Job location |
| Application Link | URL | LinkedIn job posting URL |

---

## Step 1: Create a Notion Database

### Your Database is Already Set Up! ✅

Based on your provided details:
- **Database Name**: High Growth Roles Tracker
- **Database ID**: `2e7e82acc24f80f781f1ef088dbff443`
- **Columns**: 
  - Company (Rich text)
  - Position (Rich text)
  - Date Posted (Date, format: Year/Month/Day)
  - Location (Rich text)
  - Application Link (URL)

You can skip to **Step 2** (Create Integration).

### Option A: Create from Scratch (For Reference)

1. Open [Notion](https://www.notion.so)
2. Create a new page or open an existing one
3. Type `/database` and select **Database - Table**
4. Choose **New database**
5. Name it something like "LinkedIn Jobs - India" or "Core Tech Jobs"

### Option B: Use Existing Database

If you already have a database where you want to store jobs, you can use that.

---

## Step 2: Configure Database Columns

### Your Columns Are Already Configured! ✅

Your database already has the correct columns with proper types:
- **Company** (Rich text)
- **Position** (Rich text)
- **Date Posted** (Date, format: YYYY/MM/DD)
- **Location** (Rich text)
- **Application Link** (URL)

**Note:** The scraper will automatically use "Date Posted" as the date the job was added to your tracker (not the LinkedIn posting date). The date format is Year/Month/Day (e.g., 2024/01/15).

### For Reference: How to Configure Columns

---

## Step 3: Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **+ New integration**
3. Fill in the details:
   - **Name**: LinkedIn Job Scraper (or any name you prefer)
   - **Logo**: Optional
   - **Associated workspace**: Select your workspace
4. Click **Submit**
5. Copy the **Internal Integration Token** (starts with `secret_...`)
   - ⚠️ **Save this token securely** - you'll need it in the next step

---

## Step 4: Connect Your Database to the Integration

Your integration needs permission to access your database:

1. Open your Notion database (the one you created in Step 1)
2. Click the **⋯** (three dots) menu in the top-right corner
3. Scroll down and click **Add connections**
4. Find and select your integration name (e.g., "LinkedIn Job Scraper")
5. Click **Confirm**

> ✅ Your database is now connected to the integration!

---

## Step 5: Get Your Database ID

You need the database ID to configure the scraper:

### Method 1: From URL (Easiest)

1. Open your Notion database in your browser
2. Look at the URL in your address bar:
   ```
   https://www.notion.so/your-workspace/DATABASE_ID?v=xxxxx
   ```
3. Copy the **DATABASE_ID** part (it's between the workspace name and `?v=`)
   - Example: `https://www.notion.so/myworkspace/a1b2c3d4e5f6...?v=xyz`
   - Database ID: `a1b2c3d4e5f6...`

### Method 2: From Integration Page

1. Go back to [your integrations](https://www.notion.so/my-integrations)
2. Click on your integration
3. Under **Related content**, you should see your database
4. The database ID is shown there

---

## Step 6: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   copy .env.example.notion .env
   ```

2. Open `.env` and fill in your credentials:
   ```env
   NOTION_API_KEY=secret_your_integration_token_here
   NOTION_DATABASE_ID=your_database_id_here
   ```

3. Save the file

---

## Step 7: Install Dependencies

Install the Notion client library:

```bash
pip install notion-client
```

Or if you're using the project's requirements:
```bash
pip install -r requirements.txt
```

---

## Step 8: Test the Connection

Run a quick test to verify everything is set up correctly:

```bash
python -c "from linkedin_scraper.integrations.notion import NotionIntegration; n = NotionIntegration('your_api_key', 'your_database_id'); print('Connected!' if n.connect() else 'Failed')"
```

Or simply run the scraper with `--headless False` to see if it connects:

```bash
python scrape_india_jobs_notion.py --headless False
```

---

## Usage

### Basic Usage

```bash
python scrape_india_jobs_notion.py
```

This will:
- Search for core technical/business roles across India
- Filter jobs posted in the past 24 hours
- Exclude basic roles (accountant, copywriter, video editor, etc.)
- Add matching jobs to your Notion database

### With Custom Options

```bash
# Scrape more jobs per keyword
python scrape_india_jobs_notion.py --limit 20

# Target a specific city
python scrape_india_jobs_notion.py --location Bangalore

# Use specific keywords only
python scrape_india_jobs_notion.py --keywords "SDE" "Product Manager" "Data Scientist"

# Run with browser visible (for debugging)
python scrape_india_jobs_notion.py --headless False

# Disable duplicate checking
python scrape_india_jobs_notion.py --no-dedup
```

---

## Troubleshooting

### "Failed to connect to Notion"

- ✅ Check that your `NOTION_API_KEY` is correct (starts with `secret_`)
- ✅ Verify you've connected the integration to your database (Step 4)
- ✅ Ensure the database ID is correct (32 characters, no dashes)

### "No jobs added to Notion"

- ✅ Check that jobs are being found (look at the summary)
- ✅ Verify the 24-hour filter - there may be few jobs late at night
- ✅ Check that your keywords match the jobs you're looking for
- ✅ Review excluded roles - some jobs may be filtered out

### "Duplicate jobs skipped"

This is normal! The scraper skips jobs already in your database. To re-add them:
- Use `--no-dedup` flag, or
- Delete the duplicates from Notion first

### Column Mismatch Error

If you see errors about properties:
- ✅ Verify your database has these columns: Company (Rich text), Position (Rich text), Date Posted (Date), Location (Rich text), Application Link (URL)
- ✅ Check column types match: Company/Rich text, Position/Rich text, Date Posted/Date, Location/Rich text, Application Link/URL
- ✅ Column names are case-sensitive

---

## Automation (Optional)

### Run Daily with Task Scheduler (Windows)

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Set trigger (e.g., daily at 9 AM)
4. Action: **Start a program**
5. Program: `python.exe` (full path)
6. Arguments: `scrape_india_jobs_notion.py`
7. Start in: `C:\linkedin_scraper`

### Run with a Batch File

Create `run_notion_scraper.bat`:
```batch
@echo off
cd /d C:\linkedin_scraper
python scrape_india_jobs_notion.py --limit 15
pause
```

Double-click to run anytime!

---

## What Gets Scraped?

### ✅ Included Roles

- Software Development Engineer (SDE)
- Product Manager (PM), Associate Product Manager (APM)
- Data Analyst, Business Analyst, Product Analyst
- Data Scientist, Machine Learning Engineer
- Growth Manager, Strategy Manager
- Technical Program Manager (TPM)
- Solutions Architect, Cloud Architect
- DevOps Engineer, SRE
- Product Designer, UX Designer
- Management Consultant, Technology Consultant

### ❌ Excluded Roles

- Accountant, Accounting roles
- Copywriter, Content Writer
- Video Editor
- Data Entry
- Basic Customer Support
- Telecaller
- Basic Sales Executive
- HR Executive, Recruiter
- Graphic Designer (unless Product Designer)
- Social Media Manager
- SEO/Digital Marketing Executive

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the scraper output for specific error messages
3. Ensure your LinkedIn session is valid (run `python samples/create_session.py` if needed)

---

## Privacy & Security

- ⚠️ **Never commit your `.env` file** to version control
- ⚠️ **Keep your Notion API token secret** - it provides access to your workspace
- ✅ The scraper only adds data to your database - it cannot delete or modify existing data
- ✅ Your LinkedIn credentials are stored locally in the session file

---

**Happy Job Hunting! 🎯**
