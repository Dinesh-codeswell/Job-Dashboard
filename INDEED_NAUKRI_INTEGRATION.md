# Indeed & Naukri Integration Guide

## Overview

This project now supports multi-platform job scraping with integration of **Indeed** and **Naukri** APIs alongside the existing LinkedIn scraper.

## Features

### Indeed Scraper
- ✅ GraphQL API integration
- ✅ 100 jobs per page
- ✅ Cursor-based pagination
- ✅ Rich company data (industry, employees, revenue, description)
- ✅ Salary estimation support
- ✅ Remote detection (multiple signals)
- ✅ Company logo extraction

### Naukri Scraper
- ✅ REST API integration
- ✅ 20 jobs per page
- ✅ India-focused job market
- ✅ Indian salary format support (Lakhs/Crores)
- ✅ AmbitionBox integration (ratings, reviews)
- ✅ Skills extraction
- ✅ Experience range
- ✅ Work-from-home type inference

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `tls_client` - TLS fingerprinting for Indeed
- `numpy` - Data processing
- `markdownify` - HTML to Markdown conversion
- `regex` - Advanced regex patterns
- `pandas` - Data manipulation

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Job Boards to scrape
DEFAULT_JOB_BOARDS=naukri,indeed,linkedin

# Default search parameters
DEFAULT_CITIES=Chennai,Mumbai,Pune,Gurugram,Bangalore,Hyderabad
DEFAULT_RESULTS_PER_CITY=30
DEFAULT_HOURS_OLD=48
DEFAULT_JOB_TYPE=fulltime

# Output Configuration
OUTPUT_DIR=output/india_consulting
USE_GOOGLE_SHEETS=true
USE_LOCAL_FILES=true
```

## Quick Start

### Basic Usage

```python
from linkedin_scraper.integrations import scrape_multi_platform

# Scrape from Indeed and Naukri
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="software engineer",
    location="Bangalore",
    results_wanted=50,
    hours_old=48
)

print(f"Found {len(df)} jobs")
print(df[['site', 'title', 'company', 'location']].head())
```

### Platform-Specific Scraping

```python
from linkedin_scraper.integrations import scrape_indeed, scrape_naukri

# Indeed only
indeed_df = scrape_indeed(
    search_term="python developer",
    location="Mumbai",
    results_wanted=30
)

# Naukri only
naukri_df = scrape_naukri(
    search_term="data scientist",
    location="Pune",
    results_wanted=30
)
```

### All Three Platforms

```python
from linkedin_scraper.integrations import scrape_linkedin_indeed_naukri

# Scrape from all platforms
df = scrape_linkedin_indeed_naukri(
    search_term="consultant",
    location="Gurugram",
    results_wanted_per_site=20
)
```

## Advanced Usage

### Remote Jobs Only

```python
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="full stack developer",
    is_remote=True,
    results_wanted=50
)
```

### Filter by Job Type

```python
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="intern",
    job_type="internship",
    location="Bangalore"
)
```

### Fresh Jobs Only

```python
# Jobs posted in last 24 hours
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="machine learning",
    hours_old=24
)

# Jobs posted in last week
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="machine learning",
    hours_old=168
)
```

### Save Results

```python
from linkedin_scraper.integrations import save_jobs_to_csv, save_jobs_to_excel

# Save to CSV
save_jobs_to_csv(df, "jobs_export.csv")

# Save to Excel with separate sheets per platform
save_jobs_to_excel(df, "jobs_report.xlsx")
```

## API Reference

### `scrape_multi_platform()`

Main function for multi-platform scraping.

**Parameters:**
- `sites` (str | list): Platform(s) - "linkedin", "indeed", "naukri"
- `search_term` (str): Job keyword (e.g., "software engineer")
- `location` (str): Geographic location
- `results_wanted` (int): Number of results (default: 15)
- `hours_old` (int): Filter by freshness in hours
- `is_remote` (bool): Remote jobs only (default: False)
- `job_type` (str): "fulltime", "parttime", "contract", "internship"
- `description_format` (str): "markdown", "html", "plain"
- `country` (str): Country code for Indeed (default: "india")
- `proxies` (str | list): Proxy server(s)
- `verbose` (int): Logging level 0-2 (default: 2)

**Returns:**
- `pd.DataFrame`: Job listings with columns:
  - `id`: Unique identifier
  - `site`: Platform name
  - `job_url`: Job posting URL
  - `title`: Job title
  - `company`: Company name
  - `location`: Job location
  - `date_posted`: Posting date
  - `job_type`: Employment type
  - `min_amount`, `max_amount`: Salary range
  - `currency`: Salary currency
  - `is_remote`: Remote flag
  - `description`: Job description
  - `company_logo`: Logo URL

### Platform-Specific Fields

#### Indeed Fields
- `company_addresses`: Company address
- `company_num_employees`: Company size
- `company_revenue`: Company revenue
- `company_description`: Company description
- `company_industry`: Industry sector

#### Naukri Fields
- `skills`: Required skills (comma-separated)
- `experience_range`: Experience required
- `company_rating`: Company rating (from AmbitionBox)
- `company_reviews_count`: Number of reviews
- `vacancy_count`: Number of openings
- `work_from_home_type`: "Remote", "Hybrid", or "Work from office"

## Examples

See `scrape_indeed_naukri_example.py` for complete examples:

```bash
# Run all examples
python scrape_indeed_naukri_example.py

# Run specific example
python scrape_indeed_naukri_example.py --example 1

# Available examples:
# 1 - Basic scraping
# 2 - Remote jobs only
# 3 - Single platform
# 4 - Save results
# 5 - All three platforms
# 6 - Naukri-specific fields
# 7 - Indeed-specific fields
```

## Architecture

```
linkedin_scraper/
├── integrations/
│   ├── multi_platform_scraper.py  # Unified interface
│   ├── google_sheets.py
│   └── notion.py
└── ...

jobspy/                              # Job scraping engine
├── __init__.py                      # scrape_jobs() function
├── model.py                         # Data models
├── util.py                          # Utilities
├── config.py                        # Configuration
├── exception.py                     # Exceptions
├── indeed/
│   ├── __init__.py                  # Indeed scraper
│   ├── constant.py                  # API headers, GraphQL
│   └── util.py                      # Indeed utilities
└── naukri/
    ├── __init__.py                  # Naukri scraper
    ├── constant.py                  # API headers
    └── util.py                      # Naukri utilities
```

## Data Flow

```
User Request → scrape_multi_platform()
                    ↓
        ScraperInput (unified)
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
  Indeed Scraper          Naukri Scraper
  (GraphQL API)           (REST API)
        ↓                       ↓
        └───────────┬───────────┘
                    ↓
            JobPost[] (unified)
                    ↓
            pandas DataFrame
                    ↓
            CSV/Excel/Sheets
```

## Error Handling

### Common Issues

**Indeed returns empty results:**
- Check API key validity (in `jobspy/indeed/constant.py`)
- Verify country code
- Increase timeout

**Naukri returns 406 (Recaptcha):**
- Add more delay between requests
- Rotate user-agent
- Use proxies
- Reduce request frequency

**Salary not parsing:**
- Indeed: Check compensation object structure
- Naukri: Verify Indian format regex (Lakhs/Crores)

### Logging

Set verbose level for debugging:

```python
# Verbose logging
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="python",
    verbose=2  # 0=error, 1=warning, 2=info
)
```

## Rate Limiting

### Indeed
- 100 jobs per page
- Cursor-based pagination
- API key may need rotation if rate-limited

### Naukri
- 20 jobs per page
- Built-in delay (2-5 seconds)
- Random request IDs to avoid detection
- 406 error handling

**Recommendation:** Use `results_wanted <= 100` per platform to avoid detection.

## Proxy Support

```python
# Single proxy
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="developer",
    proxies="http://proxy-server:port"
)

# Multiple proxies
proxies = [
    "http://proxy1:port",
    "http://proxy2:port"
]
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="developer",
    proxies=proxies
)
```

## Comparison: LinkedIn vs Indeed vs Naukri

| Feature | LinkedIn | Indeed | Naukri |
|---------|----------|--------|--------|
| API Type | Browser automation | GraphQL | REST |
| Jobs/Page | ~25 | 100 | 20 |
| Region | Global | Global | India-focused |
| Auth Required | Yes | No | No |
| Rate Limit | Strict | Moderate | Moderate |
| Salary Data | Rare | Estimated | Indian format |
| Company Data | Rich | Rich | AmbitionBox |
| Skills | No | No | Yes |
| Remote Detection | Description | Multi-signal | Multi-signal |

## Troubleshooting

### ModuleNotFoundError: No module named 'jobspy'

Install dependencies:
```bash
pip install tls_client numpy markdownify regex pandas
```

### Indeed API returns 403

- API key may be expired
- Check `jobspy/indeed/constant.py` for key
- Try rotating IP/proxy

### Naukri returns empty results

- Search term may be too specific
- Location may not be recognized
- Try broader search terms

### Import errors

Ensure you're importing from the correct module:
```python
# Correct
from linkedin_scraper.integrations import scrape_multi_platform

# Also correct (direct access)
from jobspy import scrape_jobs
```

## Best Practices

1. **Start small**: Test with `results_wanted=10` first
2. **Use delays**: Built-in delays prevent rate limiting
3. **Save results**: Use CSV/Excel for persistence
4. **Monitor logs**: Set `verbose=2` for debugging
5. **Respect ToS**: Use for personal/research purposes only

## Contributing

To add new job boards:

1. Create scraper module in `jobspy/<platform>/`
2. Implement `Scraper` base class
3. Add to `SCRAPER_MAPPING` in `jobspy/__init__.py`
4. Update `Site` enum in `jobspy/model.py`

## License

This integration is for educational and research purposes. Respect the terms of service of each platform.

## Support

For issues:
1. Check logs with `verbose=2`
2. Review error messages
3. Test with different search terms
4. Try with proxies if rate-limited

---

**Happy Scraping! 🚀**
