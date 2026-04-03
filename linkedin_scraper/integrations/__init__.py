"""Integrations for external services."""

from .google_sheets import GoogleSheetsIntegration
from .notion import NotionIntegration
from .multi_platform_scraper import (
    scrape_multi_platform,
    scrape_indeed,
    scrape_naukri,
    scrape_linkedin_indeed_naukri,
    save_jobs_to_csv,
    save_jobs_to_excel,
)
from .job_storage import JobStorage, auto_save_jobs

__all__ = [
    "GoogleSheetsIntegration",
    "NotionIntegration",
    "scrape_multi_platform",
    "scrape_indeed",
    "scrape_naukri",
    "scrape_linkedin_indeed_naukri",
    "save_jobs_to_csv",
    "save_jobs_to_excel",
    "JobStorage",
    "auto_save_jobs",
]
