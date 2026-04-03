# Indeed & Naukri Integration - Implementation Summary

## Overview

Successfully integrated Indeed and Naukri job scraping capabilities into the existing LinkedIn scraper project. The implementation is based on the reference `jobspy` project structure and provides a unified interface for multi-platform job scraping.

## Files Created/Modified

### New Package: `jobspy/`

Core job scraping engine with the following structure:

```
jobspy/
├── __init__.py              # Main scrape_jobs() function, exports
├── model.py                 # Pydantic data models (JobPost, Site, Country, etc.)
├── util.py                  # Shared utilities (logging, sessions, converters)
├── config.py                # Configuration loader from .env
├── exception.py             # Custom exceptions for each platform
├── indeed/
│   ├── __init__.py          # Indeed scraper class (GraphQL API)
│   ├── constant.py          # GraphQL query, API headers, API key
│   └── util.py              # Indeed-specific helpers (remote detection, compensation)
└── naukri/
    ├── __init__.py          # Naukri scraper class (REST API)
    ├── constant.py          # API headers, request configuration
    └── util.py              # Naukri-specific helpers (salary parsing, date parsing)
```

### Integration Module: `linkedin_scraper/integrations/multi_platform_scraper.py`

High-level interface for end users:

- `scrape_multi_platform()` - Main function for multi-platform scraping
- `scrape_indeed()` - Indeed-only scraping
- `scrape_naukri()` - Naukri-only scraping
- `scrape_linkedin_indeed_naukri()` - All three platforms
- `save_jobs_to_csv()` - Save results to CSV
- `save_jobs_to_excel()` - Save results to Excel with sheets per platform

### Updated Files

1. **`linkedin_scraper/integrations/__init__.py`**
   - Added exports for new multi-platform scraper functions

2. **`requirements.txt`**
   - Added: `tls_client`, `numpy`, `markdownify`, `regex`, `pandas`

3. **`.env.example`**
   - Added Indeed/Naukri configuration section
   - Job boards selection
   - Default search parameters
   - Output configuration
   - Proxy settings
   - Advanced settings

### Documentation

1. **`INDEED_NAUKRI_INTEGRATION.md`**
   - Complete user guide
   - API reference
   - Examples
   - Troubleshooting
   - Architecture overview

2. **`scrape_indeed_naukri_example.py`**
   - 7 working examples demonstrating all features
   - Can run individual examples or all together

3. **`test_indeed_naukri.py`**
   - 9 comprehensive tests
   - Module imports verification
   - Model tests
   - API connection tests
   - Integration function tests

## Key Features Implemented

### Indeed Scraper

| Feature | Status |
|---------|--------|
| GraphQL API integration | ✅ |
| 100 jobs per page | ✅ |
| Cursor-based pagination | ✅ |
| Company data (industry, employees, revenue) | ✅ |
| Salary estimation | ✅ |
| Remote detection (multi-signal) | ✅ |
| Company logo extraction | ✅ |
| Email extraction | ✅ |
| Job type filtering | ✅ |
| Hours old filtering | ✅ |

### Naukri Scraper

| Feature | Status |
|---------|--------|
| REST API integration | ✅ |
| 20 jobs per page | ✅ |
| Page-based pagination | ✅ |
| Indian salary format (Lakhs/Crores) | ✅ |
| AmbitionBox integration (ratings, reviews) | ✅ |
| Skills extraction | ✅ |
| Experience range | ✅ |
| Work-from-home type inference | ✅ |
| Remote detection | ✅ |
| Anti-detection (request IDs, delays) | ✅ |
| 406 error handling | ✅ |

### Unified Features

| Feature | Status |
|---------|--------|
| Multi-platform scraping | ✅ |
| Concurrent execution | ✅ |
| Unified data model | ✅ |
| Pandas DataFrame output | ✅ |
| CSV export | ✅ |
| Excel export (per-platform sheets) | ✅ |
| Google Sheets integration ready | ✅ |
| Notion integration ready | ✅ |
| Proxy support | ✅ |
| Configurable logging | ✅ |

## Data Models

### JobPost (Unified)

```python
JobPost(
    # Core fields (all platforms)
    id: str
    title: str
    company_name: str
    job_url: str
    location: Location
    description: str
    date_posted: date
    job_type: list[JobType]
    compensation: Compensation
    is_remote: bool
    
    # Indeed-specific
    company_addresses: str
    company_num_employees: str
    company_revenue: str
    company_description: str
    company_logo: str
    
    # Naukri-specific
    skills: list[str]
    experience_range: str
    company_rating: float
    company_reviews_count: int
    vacancy_count: int
    work_from_home_type: str
)
```

### Enums

- `Site`: LINKEDIN, INDEED, NAUKRI, ZIP_RECRUITER, GLASSDOOR, GOOGLE, BAYT, BDJOBS
- `Country`: 50+ countries with Indeed/Glassdoor domain mapping
- `JobType`: FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP, etc.
- `CompensationInterval`: YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY
- `DescriptionFormat`: MARKDOWN, HTML, PLAIN

## API Endpoints

### Indeed
- **URL**: `https://apis.indeed.com/graphql`
- **Method**: POST
- **Auth**: API key in headers (`indeed-api-key`)
- **Format**: GraphQL
- **Rate Limit**: Moderate

### Naukri
- **URL**: `https://www.naukri.com/jobapi/v3/search`
- **Method**: GET
- **Auth**: Headers + dynamic request IDs
- **Format**: REST JSON
- **Rate Limit**: Moderate (406 on detection)

## Usage Examples

### Basic

```python
from linkedin_scraper.integrations import scrape_multi_platform

df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="software engineer",
    location="Bangalore",
    results_wanted=50,
    hours_old=48
)
```

### Advanced

```python
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="python developer",
    location="Mumbai",
    results_wanted=100,
    hours_old=168,
    is_remote=True,
    job_type="fulltime",
    description_format="markdown",
    country="india",
    verbose=2
)

# Save results
from linkedin_scraper.integrations import save_jobs_to_excel
save_jobs_to_excel(df, "jobs_report.xlsx")
```

## Testing

Run the test suite:

```bash
python test_indeed_naukri.py
```

Tests include:
1. Module imports
2. Scraper instantiation
3. Site enum values
4. Country enum values
5. ScraperInput model
6. JobPost model
7. Indeed API connection
8. Naukri API connection
9. Integration functions

Run examples:

```bash
python scrape_indeed_naukri_example.py
```

7 examples covering:
1. Basic scraping
2. Remote jobs only
3. Single platform
4. Save results
5. All three platforms
6. Naukri-specific fields
7. Indeed-specific fields

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                             │
│  scrape_multi_platform(sites, search_term, location, ...)   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  ScraperInput                               │
│  - site_type: [Site.INDEED, Site.NAUKRI]                    │
│  - search_term, location, results_wanted, filters...        │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌────────────────────────┐      ┌────────────────────────┐
│   Indeed Scraper       │      │   Naukri Scraper       │
│   (GraphQL API)        │      │   (REST API)           │
│   - 100 jobs/page      │      │   - 20 jobs/page       │
│   - Cursor pagination  │      │   - Page pagination    │
│   - Rich company data  │      │   - Indian salary fmt  │
│   - Global coverage    │      │   - AmbitionBox data   │
└────────────────────────┘      └────────────────────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  JobPost[] (Unified)                        │
│  - Core fields: id, title, company, location, etc.          │
│  - Platform-specific: skills, company_revenue, etc.         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               pandas DataFrame                              │
│  - Flatten nested objects                                   │
│  - Convert lists to strings                                 │
│  - Sort by site, date_posted                                │
│  - Add missing columns                                      │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌────────────────────────┐      ┌────────────────────────┐
│   CSV Export           │      │   Excel Export         │
│   - Single file        │      │   - Per-platform sheets│
│   - All columns        │      │   - Summary sheet      │
└────────────────────────┘      └────────────────────────┘
```

## Dependencies

### Core (existing)
- `playwright` - LinkedIn browser automation
- `requests` - HTTP requests
- `pydantic` - Data validation
- `beautifulsoup4` - HTML parsing
- `python-dotenv` - Environment variables

### New (for Indeed/Naukri)
- `tls_client` - TLS fingerprinting (Indeed)
- `numpy` - Numerical operations
- `markdownify` - HTML to Markdown conversion
- `regex` - Advanced regex patterns
- `pandas` - Data manipulation

## Configuration

Environment variables (`.env`):

```bash
# Job boards
DEFAULT_JOB_BOARDS=naukri,indeed,linkedin

# Search defaults
DEFAULT_CITIES=Chennai,Mumbai,Pune,Gurugram,Bangalore,Hyderabad
DEFAULT_RESULTS_PER_CITY=30
DEFAULT_HOURS_OLD=48
DEFAULT_JOB_TYPE=fulltime

# Output
OUTPUT_DIR=output/india_consulting
USE_GOOGLE_SHEETS=true
USE_LOCAL_FILES=true

# Advanced
MAX_WORKERS=3
VERBOSE_LEVEL=2
```

## Error Handling

### Indeed
- Check response status codes
- Log API errors
- Continue on empty pages
- Return partial results

### Naukri
- Handle 406 (Recaptcha) gracefully
- Timeout after 15 seconds
- Stop after 3 consecutive failures
- Return partial results on error
- Random delays between requests

## Rate Limiting Mitigation

### Indeed
- 100 jobs per page (efficient)
- Cursor-based pagination
- API key may need rotation

### Naukri
- Built-in 2-5 second delays
- Random request IDs (UUID)
- User-agent rotation
- 406 error detection and handling
- Recommendation: <= 100 results per platform

## Future Enhancements

Potential improvements:

1. **LinkedIn Integration**: Add LinkedIn API scraper to `jobspy` (currently browser-based)
2. **More Job Boards**: Add Glassdoor, ZipRecruiter, Google Jobs, Bayt, BDJobs
3. **Database Storage**: Add SQLite/PostgreSQL output option
4. **API Endpoint**: Create REST API for scraping requests
5. **Dashboard**: Web UI for configuring and monitoring scrapes
6. **Scheduling**: Cron-like job scheduling
7. **Alerts**: Email/Slack notifications for new jobs
8. **Advanced Filtering**: Skills, experience level, company size
9. **Batch Processing**: Scrape multiple cities/search terms
10. **Data Enrichment**: Company research, salary analysis

## Troubleshooting

### Common Issues

**Module import errors:**
```bash
pip install tls_client numpy markdownify regex pandas
```

**Indeed API 403:**
- API key may be expired
- Check `jobspy/indeed/constant.py`
- Try rotating IP/proxy

**Naukri 406:**
- Add more delay
- Use proxies
- Reduce request frequency

**Empty results:**
- Broaden search terms
- Check location spelling
- Increase `hours_old`

## Conclusion

The Indeed and Naukri integration is now complete and fully functional. The implementation:

- ✅ Follows the reference project architecture
- ✅ Provides unified interface for multi-platform scraping
- ✅ Includes comprehensive documentation
- ✅ Has working examples and tests
- ✅ Supports configuration via environment variables
- ✅ Handles errors gracefully
- ✅ Includes rate limiting mitigation
- ✅ Ready for production use

Users can now scrape jobs from Indeed, Naukri, and LinkedIn using a single, consistent API.

---

**Implementation Date**: 2026-04-03
**Status**: ✅ Complete
**Test Coverage**: 9 tests (imports, models, API connections, integration)
