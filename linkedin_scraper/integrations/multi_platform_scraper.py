"""
Multi-Platform Job Scraper

Integrates LinkedIn, Indeed, and Naukri job scraping capabilities.
Provides a unified interface for scraping jobs from multiple platforms.

Example:
    from linkedin_scraper.integrations.multi_platform_scraper import scrape_multi_platform
    
    df = scrape_multi_platform(
        sites=["linkedin", "indeed", "naukri"],
        search_term="software engineer",
        location="Bangalore",
        results_wanted=50,
        auto_save=True,  # Auto-save to files
        output_dir="output/jobs"
    )
"""

import logging
from typing import Optional, List, Union, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)


def scrape_multi_platform(
    sites: Union[str, List[str]] = None,
    search_term: Optional[str] = None,
    location: Optional[str] = None,
    results_wanted: int = 15,
    hours_old: Optional[int] = 48,
    is_remote: bool = False,
    job_type: Optional[str] = None,
    description_format: str = "markdown",
    country: str = "india",
    proxies: Optional[Union[str, List[str]]] = None,
    verbose: int = 2,
    auto_save: bool = False,
    output_dir: Optional[str] = None,
    save_formats: Optional[List[str]] = None,
    google_sheet_id: Optional[str] = None,
    google_credentials_file: Optional[str] = None,
    **kwargs
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Scrape jobs from multiple platforms (LinkedIn, Indeed, Naukri) concurrently.

    Args:
        sites: Platform(s) to scrape - "linkedin", "indeed", "naukri", or list
        search_term: Job search keyword (e.g., "software engineer", "data analyst")
        location: Geographic location (e.g., "Bangalore", "Mumbai", "New York")
        results_wanted: Number of job results to fetch per platform (default: 15)
        hours_old: Filter jobs posted within last X hours (default: 48)
        is_remote: Filter for remote jobs only (default: False)
        job_type: Job type filter - "fulltime", "parttime", "contract", "internship"
        description_format: Format for job description - "markdown", "html", "plain"
        country: Country code for Indeed (default: "india")
        proxies: Proxy server(s) to use for requests
        verbose: Logging verbosity (0=error, 1=warning, 2=info)
        auto_save: Automatically save results to files (default: False)
        output_dir: Output directory for saved files (default: "output/jobs")
        save_formats: List of formats to save: ['csv', 'excel', 'json', 'parquet', 'sqlite']
        google_sheet_id: Google Spreadsheet ID (optional, for auto-save to Sheets)
        google_credentials_file: Path to Google credentials JSON (optional)
        **kwargs: Additional platform-specific arguments
    
    Returns:
        If auto_save=False: Pandas DataFrame with job data
        If auto_save=True: Dictionary with DataFrame and save results:
            {
                'dataframe': pd.DataFrame,
                'saved_files': {'csv': 'path/to/file.csv', 'excel': 'path/to/file.xlsx'},
                'total_jobs': int
            }
    
    Raises:
        ImportError: If jobspy package is not installed
        ValueError: If invalid site name provided
    
    Example:
        >>> df = scrape_multi_platform(
        ...     sites=["indeed", "naukri"],
        ...     search_term="python developer",
        ...     location="Bangalore",
        ...     results_wanted=30,
        ...     hours_old=168,
        ...     is_remote=True
        ... )
        >>> print(f"Found {len(df)} jobs")
        >>> print(df[['site', 'title', 'company', 'location']].head())
    """
    try:
        from jobspy import scrape_jobs as jobspy_scrape
        from jobspy.model import Site
    except ImportError as e:
        logger.error(f"jobspy package not installed. Run: pip install -r requirements.txt")
        raise ImportError(
            "jobspy package required. Install with: pip install tls_client numpy markdownify regex pandas"
        ) from e
    
    # Normalize sites input
    if sites is None:
        sites = ["indeed", "naukri"]
    elif isinstance(sites, str):
        sites = [sites]
    
    # Validate and convert site names
    site_mapping = {
        "linkedin": Site.LINKEDIN,
        "indeed": Site.INDEED,
        "naukri": Site.NAUKRI,
    }
    
    site_enums = []
    for site in sites:
        site_lower = site.lower()
        if site_lower not in site_mapping:
            raise ValueError(
                f"Invalid site: '{site}'. Valid options: {list(site_mapping.keys())}"
            )
        site_enums.append(site_mapping[site_lower])
    
    logger.info(f"Starting multi-platform scrape: sites={sites}, search_term='{search_term}', location='{location}'")
    
    # Call jobspy scrape function
    df = jobspy_scrape(
        site_name=site_enums,
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        is_remote=is_remote,
        job_type=job_type,
        description_format=description_format,
        country_indeed=country,
        proxies=proxies,
        verbose=verbose,
        **kwargs
    )
    
    logger.info(f"Scraping complete. Found {len(df)} total jobs across {len(sites)} platforms")
    
    # Auto-save if requested
    if auto_save and len(df) > 0:
        from .job_storage import JobStorage
        
        storage = JobStorage(
            output_dir=output_dir or "output/jobs",
            google_sheet_id=google_sheet_id,
            google_credentials_file=google_credentials_file
        )
        
        # Default formats if not specified
        if save_formats is None:
            save_formats = ['csv', 'excel']
        
        saved_files = storage.save_all(
            df,
            save_csv='csv' in save_formats,
            save_excel='excel' in save_formats,
            save_json='json' in save_formats,
            save_parquet='parquet' in save_formats,
            save_google_sheets='google_sheets' in save_formats,
            save_sqlite='sqlite' in save_formats
        )
        
        logger.info(f"Auto-saved jobs to: {', '.join(saved_files.keys())}")
        
        return {
            'dataframe': df,
            'saved_files': saved_files,
            'total_jobs': len(df)
        }
    
    return df


def scrape_indeed(
    search_term: str,
    location: Optional[str] = None,
    results_wanted: int = 15,
    hours_old: Optional[int] = 48,
    is_remote: bool = False,
    job_type: Optional[str] = None,
    country: str = "india",
    **kwargs
) -> pd.DataFrame:
    """
    Scrape jobs from Indeed only.
    
    Args:
        search_term: Job search keyword
        location: Geographic location
        results_wanted: Number of results (default: 15)
        hours_old: Filter by freshness in hours (default: 48)
        is_remote: Remote jobs only (default: False)
        job_type: Job type filter
        country: Country code (default: "india")
        **kwargs: Additional arguments
    
    Returns:
        DataFrame with Indeed jobs
    
    Example:
        >>> df = scrape_indeed("software engineer", "Bangalore", results_wanted=50)
    """
    return scrape_multi_platform(
        sites=["indeed"],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        is_remote=is_remote,
        job_type=job_type,
        country=country,
        **kwargs
    )


def scrape_naukri(
    search_term: str,
    location: Optional[str] = None,
    results_wanted: int = 15,
    hours_old: Optional[int] = 48,
    is_remote: bool = False,
    job_type: Optional[str] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Scrape jobs from Naukri.com only.
    
    Args:
        search_term: Job search keyword
        location: Geographic location (India cities preferred)
        results_wanted: Number of results (default: 15)
        hours_old: Filter by freshness in hours (default: 48)
        is_remote: Remote jobs only (default: False)
        job_type: Job type filter
        **kwargs: Additional arguments
    
    Returns:
        DataFrame with Naukri jobs
    
    Example:
        >>> df = scrape_naukri("python developer", "Mumbai", results_wanted=30)
    """
    return scrape_multi_platform(
        sites=["naukri"],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        is_remote=is_remote,
        job_type=job_type,
        country="india",
        **kwargs
    )


def scrape_linkedin_indeed_naukri(
    search_term: str,
    location: Optional[str] = None,
    results_wanted_per_site: int = 15,
    hours_old: Optional[int] = 48,
    is_remote: bool = False,
    job_type: Optional[str] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Scrape jobs from LinkedIn, Indeed, and Naukri simultaneously.
    
    Note: LinkedIn scraping requires browser automation (Playwright) and
    may need authentication. Ensure you have proper credentials configured.
    
    Args:
        search_term: Job search keyword
        location: Geographic location
        results_wanted_per_site: Number of results per platform (default: 15)
        hours_old: Filter by freshness in hours (default: 48)
        is_remote: Remote jobs only (default: False)
        job_type: Job type filter
        **kwargs: Additional arguments
    
    Returns:
        DataFrame with jobs from all three platforms
    
    Example:
        >>> df = scrape_linkedin_indeed_naukri(
        ...     "data scientist",
        ...     "Bangalore",
        ...     results_wanted_per_site=25
        ... )
        >>> print(df['site'].value_counts())
    """
    return scrape_multi_platform(
        sites=["linkedin", "indeed", "naukri"],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted_per_site,
        hours_old=hours_old,
        is_remote=is_remote,
        job_type=job_type,
        **kwargs
    )


def save_jobs_to_csv(
    df: pd.DataFrame,
    filename: str,
    include_all_columns: bool = False
) -> str:
    """
    Save scraped jobs to CSV file.
    
    Args:
        df: DataFrame from scrape functions
        filename: Output filename (will add .csv extension if not present)
        include_all_columns: Include all columns or just essential ones
    
    Returns:
        Path to saved file
    
    Example:
        >>> df = scrape_multi_platform(["indeed", "naukri"], "python developer")
        >>> save_jobs_to_csv(df, "jobs_export")
    """
    if not filename.endswith('.csv'):
        filename = f"{filename}.csv"
    
    # Select essential columns if not including all
    if not include_all_columns:
        essential_cols = [
            'site', 'title', 'company', 'location', 'job_url',
            'date_posted', 'job_type', 'is_remote',
            'min_amount', 'max_amount', 'currency',
            'description'
        ]
        available_cols = [col for col in essential_cols if col in df.columns]
        df = df[available_cols]
    
    df.to_csv(filename, index=False, encoding='utf-8')
    logger.info(f"Saved {len(df)} jobs to {filename}")
    
    return filename


def save_jobs_to_excel(
    df: pd.DataFrame,
    filename: str,
    sheet_name: str = "Jobs"
) -> str:
    """
    Save scraped jobs to Excel file with separate sheets per platform.
    
    Args:
        df: DataFrame from scrape functions
        filename: Output filename (will add .xlsx extension if not present)
        sheet_name: Base sheet name (platforms will be suffixed)
    
    Returns:
        Path to saved file
    
    Example:
        >>> df = scrape_multi_platform(["indeed", "naukri"], "software engineer")
        >>> save_jobs_to_excel(df, "jobs_report.xlsx")
    """
    if not filename.endswith('.xlsx'):
        filename = f"{filename}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Summary sheet
        summary = df.groupby('site').size().reset_index(name='count')
        summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Per-platform sheets
        for site in df['site'].unique():
            site_df = df[df['site'] == site]
            site_sheet = f"{sheet_name}_{site.title()}"[:31]  # Excel limit
            site_df.to_excel(writer, sheet_name=site_sheet, index=False)
    
    logger.info(f"Saved {len(df)} jobs to {filename} with {len(df['site'].unique())} sheets")
    
    return filename


__all__ = [
    "scrape_multi_platform",
    "scrape_indeed",
    "scrape_naukri",
    "scrape_linkedin_indeed_naukri",
    "save_jobs_to_csv",
    "save_jobs_to_excel",
]
