# LinkedIn Job Scraper → Google Sheets Workflow

Automatically scrape job listings from LinkedIn and upload them to Google Sheets.

## Quick Start

### Prerequisites

1. **LinkedIn Session**: You need a valid LinkedIn session file
2. **Google Sheets API**: Set up Google Sheets API access

### Step 1: Create LinkedIn Session (if not done)

```bash
python samples\create_session.py
```

This will open a browser window. Log in to LinkedIn, and it will create `linkedin_session.json`.

### Step 2: Set Up Google Sheets API

Run the interactive setup wizard:

```bash
python setup_google_sheets.py
```

Or follow the detailed instructions in [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md).

**Quick setup:**
1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create a service account and download `credentials.json`
4. Create a Google Sheet and share it with the service account email
5. Add the Sheet ID to your `.env` file

### Step 3: Run the Job Scraper

```bash
# Basic usage
python jobs_to_sheets.py --keywords "software engineer" --location "San Francisco"

# With more options
python jobs_to_sheets.py -k "data scientist" -l "Remote" --limit 20

# Show browser window (not headless)
python jobs_to_sheets.py -k "product manager" --headless False
```

## Command Line Options

```
usage: jobs_to_sheets.py [-h] -k KEYWORDS [-l LOCATION] [--limit LIMIT] 
                         [--headless HEADLESS] [--session-file SESSION_FILE] 
                         [--worksheet WORKSHEET] [--no-dedup]

options:
  -h, --help            show this help message and exit
  -k, --keywords        Job search keywords (required)
  -l, --location        Job location (e.g., "San Francisco, CA" or "Remote")
  --limit               Maximum number of jobs to scrape (default: 10)
  --headless            Run browser in headless mode (default: True)
  --session-file        Path to LinkedIn session file
  --worksheet           Name of Google Sheet worksheet (default: "Jobs")
  --no-dedup            Disable duplicate checking (upload all jobs)
```

## Examples

### Search for remote Python jobs
```bash
python jobs_to_sheets.py -k "Python developer" -l "Remote" --limit 15
```

### Search for jobs in New York
```bash
python jobs_to_sheets.py -k "data analyst" -l "New York, NY" --limit 20
```

### Scrape without duplicate checking
```bash
python jobs_to_sheets.py -k "machine learning" --no-dedup
```

### Use a different worksheet
```bash
python jobs_to_sheets.py -k "frontend" -l "Austin" --worksheet "Tech Jobs"
```

## Output in Google Sheets

The script creates a worksheet with the following columns:

| Column | Description |
|--------|-------------|
| Job Title | Position title |
| Company | Company name |
| Location | Job location |
| Posted Date | When the job was posted |
| Applicant Count | Number of applicants |
| Job URL | Direct link to LinkedIn job posting |
| Company URL | Link to company LinkedIn page |
| Description | Full job description |
| Benefits | Benefits information |
| Date Added | When the job was added to the sheet |

## Features

### Data Cleaning
- **Description Truncation**: Long descriptions are truncated to fit Google Sheets limits
- **Whitespace Cleanup**: Extra newlines and spaces are removed
- **URL Normalization**: URLs are cleaned and standardized

### Duplicate Detection
- Automatically checks if a job URL already exists in the sheet
- Skips duplicates to avoid redundant entries
- Use `--no-dedup` to disable this feature

### Error Handling
- Handles LinkedIn rate limits gracefully
- Continues scraping even if individual jobs fail
- Reports detailed error summary at the end

## Troubleshooting

### "Failed to connect to Google Sheets"
1. Make sure `credentials.json` exists in the project folder
2. Check that `GOOGLE_SHEET_ID` is set in `.env`
3. Verify the Google Sheet is shared with the service account email
4. Run `python setup_google_sheets.py` to test the connection

### "Rate limit detected"
LinkedIn has strict rate limits. Solutions:
- Wait a few hours before scraping again
- Reduce the `--limit` parameter
- Add delays between requests (modify the script)
- Use `headless=False` to appear more human-like

### "No jobs found"
- Check your search keywords and location
- Try broader search terms
- Verify your LinkedIn session is valid (re-run `create_session.py`)

### "Authentication error"
- Your LinkedIn session may have expired
- Run `python samples\create_session.py` to create a new session

## Advanced Usage

### Using in Your Own Script

```python
import asyncio
from linkedin_scraper import BrowserManager
from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration

async def main():
    # Initialize Google Sheets
    sheets = GoogleSheetsIntegration()
    sheets.connect(worksheet_name="Jobs")
    
    async with BrowserManager() as browser:
        await browser.load_session("linkedin_session.json")
        
        # Search for jobs
        search = JobSearchScraper(browser.page)
        job_urls = await search.search(keywords="engineer", location="Remote", limit=10)
        
        # Scrape and upload
        scraper = JobScraper(browser.page)
        for url in job_urls:
            job = await scraper.scrape(url)
            sheets.upload_job(job.to_dict())

asyncio.run(main())
```

### Custom Data Processing

You can modify the `_clean_job_data` method in `jobs_to_sheets.py` to customize how data is processed before uploading to Google Sheets.

## File Structure

```
linkedin_scraper/
├── jobs_to_sheets.py           # Main workflow script
├── setup_google_sheets.py      # Google Sheets setup wizard
├── GOOGLE_SHEETS_SETUP.md      # Detailed setup instructions
├── credentials.json            # Google API credentials (create this)
├── linkedin_session.json       # LinkedIn session (create this)
├── .env                        # Configuration (Sheet ID, etc.)
└── linkedin_scraper/
    └── integrations/
        └── google_sheets.py    # Google Sheets integration module
```

## Security Notes

⚠️ **Never share these files:**
- `credentials.json` - Contains Google API credentials
- `linkedin_session.json` - Contains LinkedIn authentication cookies
- `.env` - Contains your Sheet ID and configuration

These files are already in `.gitignore` to prevent accidental commits.

## Rate Limits & Best Practices

1. **Don't scrape too many jobs at once** - Stay under 50 jobs per session
2. **Add delays** - The script already includes 2-second delays
3. **Use headless mode** - More stealthy, but can use `headless=False` if blocked
4. **Respect LinkedIn's ToS** - Use for personal/educational purposes only

## Support

- Issues: https://github.com/joeyism/linkedin_scraper/issues
- Documentation: See README.md in the main project
