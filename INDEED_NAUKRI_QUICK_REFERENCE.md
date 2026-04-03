# Indeed & Naukri Scraper - Quick Reference

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_indeed_naukri.py
```

## Quick Start

### Scrape from Indeed and Naukri

```python
from linkedin_scraper.integrations import scrape_multi_platform

df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="software engineer",
    location="Bangalore",
    results_wanted=50
)
```

### Save Results

```python
from linkedin_scraper.integrations import save_jobs_to_csv, save_jobs_to_excel

# CSV
save_jobs_to_csv(df, "jobs.csv")

# Excel
save_jobs_to_excel(df, "jobs.xlsx")
```

## Function Signatures

### scrape_multi_platform()

```python
scrape_multi_platform(
    sites=["indeed", "naukri"],      # Platform(s)
    search_term="python developer",  # Job keyword
    location="Mumbai",               # Location
    results_wanted=50,               # Number of jobs
    hours_old=48,                    # Freshness (hours)
    is_remote=False,                 # Remote only
    job_type="fulltime",             # fulltime/parttime/contract/internship
    country="india",                 # Country for Indeed
    verbose=2                        # 0=error, 1=warning, 2=info
)
```

### scrape_indeed()

```python
scrape_indeed(
    search_term="data scientist",
    location="Bangalore",
    results_wanted=30,
    hours_old=72,
    is_remote=True,
    job_type="fulltime"
)
```

### scrape_naukri()

```python
scrape_naukri(
    search_term="full stack developer",
    location="Pune",
    results_wanted=30,
    hours_old=48,
    is_remote=False
)
```

### scrape_linkedin_indeed_naukri()

```python
scrape_linkedin_indeed_naukri(
    search_term="consultant",
    location="Gurugram",
    results_wanted_per_site=20
)
```

## DataFrame Columns

### Core Columns (All Platforms)
- `id` - Unique job identifier
- `site` - Platform name (indeed/naukri/linkedin)
- `job_url` - Job posting URL
- `job_url_direct` - Direct application URL
- `title` - Job title
- `company` - Company name
- `location` - Job location
- `date_posted` - Posting date
- `job_type` - Employment type
- `min_amount` - Minimum salary
- `max_amount` - Maximum salary
- `currency` - Salary currency
- `is_remote` - Remote flag
- `description` - Job description

### Indeed-Specific
- `company_addresses`
- `company_num_employees`
- `company_revenue`
- `company_description`
- `company_logo`

### Naukri-Specific
- `skills`
- `experience_range`
- `company_rating`
- `company_reviews_count`
- `vacancy_count`
- `work_from_home_type`

## Examples

### Example 1: Basic Search

```python
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="python developer",
    location="Bangalore",
    results_wanted=50
)
print(f"Found {len(df)} jobs")
```

### Example 2: Remote Jobs Only

```python
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="software engineer",
    is_remote=True,
    results_wanted=30
)
```

### Example 3: Recent Jobs

```python
# Last 24 hours
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="data analyst",
    hours_old=24,
    results_wanted=20
)

# Last week
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="data analyst",
    hours_old=168,
    results_wanted=20
)
```

### Example 4: Filter by Job Type

```python
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="intern",
    job_type="internship",
    location="Mumbai",
    results_wanted=20
)
```

### Example 5: Multiple Locations

```python
cities = ["Bangalore", "Mumbai", "Pune"]
all_jobs = []

for city in cities:
    df = scrape_multi_platform(
        sites=["indeed", "naukri"],
        search_term="software engineer",
        location=city,
        results_wanted=20
    )
    all_jobs.append(df)

combined_df = pd.concat(all_jobs, ignore_index=True)
```

### Example 6: Save and Export

```python
df = scrape_multi_platform(
    sites=["indeed", "naukri"],
    search_term="machine learning",
    location="Hyderabad",
    results_wanted=50
)

# Save to CSV
save_jobs_to_csv(df, "ml_jobs.csv")

# Save to Excel with separate sheets
save_jobs_to_excel(df, "ml_jobs_report.xlsx", sheet_name="Jobs")
```

### Example 7: Access Platform-Specific Fields

```python
df = scrape_naukri(
    search_term="java developer",
    location="Chennai",
    results_wanted=20
)

# Access Naukri-specific fields
if 'skills' in df.columns:
    print(df[['title', 'company', 'skills', 'experience_range']].head())

df = scrape_indeed(
    search_term="product manager",
    location="Delhi",
    results_wanted=20
)

# Access Indeed-specific fields
if 'company_revenue' in df.columns:
    print(df[['title', 'company', 'company_revenue', 'company_num_employees']].head())
```

## Environment Variables (.env)

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

## Testing

```bash
# Run all tests
python test_indeed_naukri.py

# Run specific test
python test_indeed_naukri.py --test 1

# Run examples
python scrape_indeed_naukri_example.py

# Run specific example
python scrape_indeed_naukri_example.py --example 1
```

## Troubleshooting

### Import Error
```bash
pip install tls_client numpy markdownify regex pandas
```

### Indeed Returns Empty
- Check API key in `jobspy/indeed/constant.py`
- Verify country code
- Try different search term

### Naukri Returns 406
- Add delay between requests
- Use proxies
- Reduce results_wanted
- Wait and retry

### No Results
- Broaden search terms
- Check location spelling
- Increase hours_old
- Try different platform

## Tips

1. **Start Small**: Test with `results_wanted=10` first
2. **Use Verbose Logging**: Set `verbose=2` for debugging
3. **Save Results**: Export to CSV/Excel for persistence
4. **Respect Rate Limits**: Keep results <= 100 per platform
5. **Use Proxies**: For large-scale scraping
6. **Check Logs**: Look for API errors in console

## API Comparison

| Feature | Indeed | Naukri |
|---------|--------|--------|
| Jobs/Page | 100 | 20 |
| API Type | GraphQL | REST |
| Region | Global | India |
| Salary | Estimated | Indian format |
| Company Data | Rich | AmbitionBox |
| Skills | No | Yes |

## Common Searches

```python
# Tech jobs
scrape_multi_platform(sites=["indeed", "naukri"], 
                      search_term="software engineer", 
                      location="Bangalore")

# Data science
scrape_multi_platform(sites=["indeed", "naukri"], 
                      search_term="data scientist", 
                      location="Mumbai")

# Remote jobs
scrape_multi_platform(sites=["indeed", "naukri"], 
                      search_term="python developer", 
                      is_remote=True)

# Internships
scrape_multi_platform(sites=["indeed", "naukri"], 
                      search_term="intern", 
                      job_type="internship")

# Contract work
scrape_multi_platform(sites=["indeed", "naukri"], 
                      search_term="consultant", 
                      job_type="contract")
```

---

For complete documentation, see `INDEED_NAUKRI_INTEGRATION.md`
