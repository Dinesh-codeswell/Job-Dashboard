#!/usr/bin/env python3
"""
Unified India Jobs Scraper - LinkedIn + Indeed + Naukri

🚀 COMPLETE SOLUTION: Combines LinkedIn, Indeed, and Naukri scraping
   into a single script with Google Sheets storage.

FEATURES:
✅ LinkedIn scraping (browser automation) - 48 hours filter
✅ Indeed scraping (API) - GraphQL API
✅ Naukri scraping (API) - REST API
✅ Google Sheets storage (unified format)
✅ Duplicate detection across all platforms
✅ Smart job data normalization
✅ Comprehensive logging and statistics

USAGE:
    python scrape_all_india_jobs.py

CONFIGURATION:
    Edit .env file to configure:
    - LINKEDIN_EMAIL / LINKEDIN_PASSWORD
    - GOOGLE_SHEET_ID / GOOGLE_CREDENTIALS_FILE
    - DEFAULT_JOB_BOARDS, DEFAULT_CITIES, etc.

OUTPUT:
    Google Sheets tabs:
    - LinkedIn_Jobs
    - Indeed_Jobs
    - Naukri_Jobs
    - Summary (statistics)
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlencode
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# LinkedIn scraper imports
from linkedin_scraper import BrowserManager, ConsoleCallback
from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration
from linkedin_scraper.core.exceptions import ScrapingError, AuthenticationError

# Indeed/Naukri imports
from linkedin_scraper.integrations import (
    scrape_multi_platform,
    JobStorage
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION - Loaded from .env
# ============================================================================

# Job boards to scrape
DEFAULT_JOB_BOARDS = os.getenv("DEFAULT_JOB_BOARDS", "linkedin,indeed,naukri").split(",")

# Cities to search
DEFAULT_CITIES = os.getenv("DEFAULT_CITIES", "Bangalore,Mumbai,Pune,Gurugram,Chennai,Hyderabad").split(",")

# Search parameters
DEFAULT_RESULTS_PER_CITY = int(os.getenv("DEFAULT_RESULTS_PER_CITY", "10"))
DEFAULT_HOURS_OLD = int(os.getenv("DEFAULT_HOURS_OLD", "48"))
DEFAULT_MAX_DAYS = DEFAULT_HOURS_OLD // 24

# Google Sheets
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# LinkedIn credentials
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Keywords for consulting jobs
CONSULTING_KEYWORDS = [
    "Management Consultant",
    "Business Consultant",
    "Strategy Consultant",
    "IT Consultant",
    "Technology Consultant",
    "Digital Consultant",
    "Financial Consultant",
    "SAP Consultant",
    "Oracle Consultant",
    "Cloud Consultant",
    "Cybersecurity Consultant",
    "Data Consultant",
    "ERP Consultant",
    "CRM Consultant",
    "Risk Consultant",
    "Senior Consultant",
    "Principal Consultant",
    "Lead Consultant",
    "Consulting Analyst",
    "Business Analyst",
]

# Internship keywords
INTERNSHIP_KEYWORDS = [
    "Consulting Intern",
    "Business Analyst Intern",
    "Management Consulting Intern",
    "Strategy Intern",
    "IT Consultant Intern",
    "Technology Intern",
    "Digital Consulting Intern",
    "Financial Analyst Intern",
    "SAP Intern",
    "Oracle Intern",
    "Cloud Consultant Intern",
    "Cybersecurity Intern",
    "Data Analyst Intern",
    "ERP Intern",
    "CRM Intern",
    "Risk Analyst Intern",
    "Business Intern",
    "Consulting Summer Intern",
    "Winter Intern Consulting",
    "Intern Consultant",
]


# ============================================================================
# UNIFIED GOOGLE SHEETS MANAGER
# ============================================================================

class UnifiedSheetsManager:
    """
    Manages Google Sheets for all three platforms.
    
    Creates separate worksheets for each platform with unified format.
    """
    
    def __init__(self, sheet_id: str, credentials_file: str):
        """Initialize sheets manager."""
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file
        self.sheets = {}  # platform -> GoogleSheetsIntegration
        self.all_urls = set()  # For cross-platform duplicate detection
        
    def connect(self, platforms: List[str]) -> bool:
        """
        Connect to Google Sheets for all platforms.
        
        Args:
            platforms: List of platforms ('linkedin', 'indeed', 'naukri')
            
        Returns:
            True if all connections successful
        """
        print("\n📊 Connecting to Google Sheets...")
        
        for platform in platforms:
            worksheet_name = f"{platform.capitalize()}_Jobs"
            
            sheet = GoogleSheetsIntegration(
                credentials_file=self.credentials_file,
                sheet_id=self.sheet_id
            )
            
            if not sheet.connect(worksheet_name=worksheet_name):
                logger.error(f"Failed to connect to {worksheet_name}")
                return False
            
            self.sheets[platform] = sheet
            
            # Load existing URLs for duplicate detection
            try:
                existing_jobs = sheet.get_all_jobs()
                for job in existing_jobs:
                    if 'Job URL' in job:
                        self.all_urls.add(job['Job URL'])
            except Exception as e:
                logger.debug(f"Could not load existing jobs: {e}")
        
        print(f"✅ Connected to {len(platforms)} worksheets\n")
        return True
    
    def is_duplicate(self, job_url: str) -> bool:
        """Check if job URL exists in any platform sheet."""
        return job_url in self.all_urls
    
    def upload_job(self, platform: str, job_data: Dict[str, Any]) -> bool:
        """
        Upload job to appropriate platform sheet.
        
        Args:
            platform: 'linkedin', 'indeed', or 'naukri'
            job_data: Job data dictionary
            
        Returns:
            True if upload successful
        """
        if platform not in self.sheets:
            logger.error(f"Platform {platform} not connected")
            return False
        
        # Mark as duplicate
        if job_data.get('job_url'):
            self.all_urls.add(job_data['job_url'])
        
        return self.sheets[platform].upload_job(job_data)
    
    def upload_summary(self, stats: Dict[str, Any]):
        """Upload summary statistics to Summary worksheet."""
        try:
            summary_sheet = GoogleSheetsIntegration(
                credentials_file=self.credentials_file,
                sheet_id=self.sheet_id
            )
            
            if summary_sheet.connect(worksheet_name="Summary"):
                # Create summary row
                row_data = [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    stats.get('linkedin_jobs', 0),
                    stats.get('indeed_jobs', 0),
                    stats.get('naukri_jobs', 0),
                    stats.get('total_jobs', 0),
                    stats.get('duplicates_skipped', 0),
                    stats.get('errors', 0)
                ]
                
                # Check if headers exist
                try:
                    headers = summary_sheet.worksheet.row_values(1)
                    if not headers or headers[0] != "Timestamp":
                        # Add headers
                        summary_sheet.worksheet.append_row([
                            "Timestamp",
                            "LinkedIn Jobs",
                            "Indeed Jobs",
                            "Naukri Jobs",
                            "Total Jobs",
                            "Duplicates Skipped",
                            "Errors"
                        ], value_input_option="USER_ENTERED")
                except:
                    pass
                
                summary_sheet.worksheet.append_row(row_data)
                logger.info("Summary uploaded to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to upload summary: {e}")


# ============================================================================
# LINKEDIN SCRAPER (OPTIMIZED)
# ============================================================================

class OptimizedJobSearchScraper(JobSearchScraper):
    """Enhanced job search scraper with LinkedIn date filters."""

    async def search(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 25,
        days_ago: int = 2
    ) -> List[str]:
        """Search for jobs with LinkedIn's native date filter."""
        logger.info(f"🔍 LinkedIn: '{keywords}' in {location} (past {days_ago} days)")

        search_url = self._build_filtered_search_url(keywords, location, days_ago)
        await self.callback.on_start("JobSearch", search_url)

        await self.navigate_and_wait(search_url)
        await self.callback.on_progress("Navigated to filtered results", 20)

        try:
            await self.page.wait_for_selector('a[href*="/jobs/view/"]', timeout=10000)
        except:
            logger.warning(f"⚠️  No jobs found for '{keywords}' in {location}")
            return []

        await self.wait_and_focus(1)
        await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=2)
        await self.callback.on_progress("Loaded filtered listings", 50)

        job_urls = await self._extract_job_urls(limit)
        await self.callback.on_progress(f"Found {len(job_urls)} recent jobs", 90)

        await self.callback.on_progress("Search complete", 100)
        await self.callback.on_complete("JobSearch", job_urls)

        logger.info(f"✅ LinkedIn: Found {len(job_urls)} jobs from past {days_ago} days")
        return job_urls

    def _build_filtered_search_url(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        days_ago: int = 2
    ) -> str:
        """Build LinkedIn search URL with native date filters."""
        base_url = "https://www.linkedin.com/jobs/search/"
        params = {}

        if keywords:
            params['keywords'] = keywords
        if location:
            params['location'] = location

        # LinkedIn's time filter
        seconds = days_ago * 24 * 60 * 60
        params['f_TPR'] = f'r{seconds}'

        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url


# ============================================================================
# UNIFIED JOBS SCRAPER
# ============================================================================

class UnifiedIndiaJobsScraper:
    """
    Unified scraper for LinkedIn, Indeed, and Naukri.
    
    Combines all three platforms into a single workflow.
    """
    
    def __init__(
        self,
        platforms: List[str] = None,
        sheet_id: str = None,
        credentials_file: str = None,
        max_days: int = 2,
        headless: bool = True
    ):
        """Initialize unified scraper."""
        self.platforms = platforms or DEFAULT_JOB_BOARDS
        self.max_days = max_days
        self.headless = headless
        self.sheet_id = sheet_id or GOOGLE_SHEET_ID
        self.credentials_file = credentials_file or GOOGLE_CREDENTIALS_FILE
        
        # Statistics
        self.stats = {
            "linkedin_jobs": 0,
            "indeed_jobs": 0,
            "naukri_jobs": 0,
            "total_jobs": 0,
            "duplicates_skipped": 0,
            "errors": 0
        }
        
        # Sheets manager
        self.sheets_manager = None
    
    def _normalize_linkedin_job(self, job, city: str) -> Dict[str, Any]:
        """Normalize LinkedIn job data to unified format."""
        description = job.job_description or ""
        description = description.replace("… more", "").replace("... more", "")
        description = description.replace("Show less", "").replace("Show more", "")
        
        return {
            "job_title": (job.job_title or "").strip(),
            "company": job.company or "",
            "company_logo": job.company_logo or "",
            "employment_type": (job.employment_type or "").strip(),
            "location": (job.location or city).strip(),
            "posted_date": job.posted_date or "",
            "job_url": job.linkedin_url,
            "job_description": description[:45000] if len(description) > 45000 else description,
            "search_city": city,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "platform": "linkedin"
        }
    
    def _normalize_indeed_naukri_job(self, row: Dict, platform: str) -> Dict[str, Any]:
        """Normalize Indeed/Naukri job data from DataFrame to unified format."""
        # Map DataFrame columns to unified format
        mapping = {
            'title': 'job_title',
            'company': 'company',
            'company_logo': 'company_logo',
            'job_type': 'employment_type',
            'location': 'location',
            'date_posted': 'posted_date',
            'job_url': 'job_url',
            'description': 'job_description',
        }
        
        job_data = {}
        for df_col, unified_col in mapping.items():
            job_data[unified_col] = str(row.get(df_col, ''))
        
        job_data['search_city'] = row.get('location', '').split(',')[0].strip()
        job_data['date_added'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        job_data['platform'] = platform
        
        # Clean description
        desc = job_data.get('job_description', '')
        if desc and len(desc) > 45000:
            job_data['job_description'] = desc[:45000] + "..."
        
        return job_data
    
    async def scrape_linkedin(
        self,
        browser,
        cities: List[str],
        keywords: List[str],
        limit_per_keyword: int = 10
    ) -> int:
        """Scrape LinkedIn jobs."""
        uploaded = 0
        search_scraper = OptimizedJobSearchScraper(browser.page, callback=ConsoleCallback())
        job_scraper = JobScraper(browser.page, callback=ConsoleCallback())
        
        for city in cities:
            for keyword in keywords:
                try:
                    job_urls = await search_scraper.search(
                        keywords=keyword,
                        location=city,
                        limit=limit_per_keyword,
                        days_ago=self.max_days
                    )
                    
                    for job_url in job_urls:
                        if self.sheets_manager.is_duplicate(job_url):
                            self.stats["duplicates_skipped"] += 1
                            continue
                        
                        try:
                            job = await job_scraper.scrape(job_url)
                            job_data = self._normalize_linkedin_job(job, city)
                            
                            if self.sheets_manager.upload_job("linkedin", job_data):
                                uploaded += 1
                                self.stats["linkedin_jobs"] += 1
                                logger.info(f"  ✓ LinkedIn: {job.job_title} at {job.company}")
                        except Exception as e:
                            self.stats["errors"] += 1
                            logger.debug(f"LinkedIn scraping error: {e}")
                    
                    await asyncio.sleep(0.5)
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.debug(f"LinkedIn search error: {e}")
                
                await asyncio.sleep(1)
            
            await asyncio.sleep(2)
        
        return uploaded
    
    def scrape_indeed_naukri(
        self,
        cities: List[str],
        keywords: List[str],
        limit_per_city: int = 10
    ) -> int:
        """Scrape Indeed and Naukri using jobspy."""
        import time
        
        uploaded = 0
        
        # Combine keywords
        search_terms = keywords[:10]  # Limit to top 10 for API

        for city in cities:
            for keyword in search_terms:
                try:
                    logger.info(f"🔍 API: '{keyword}' in {city}")

                    # Scrape Indeed and Naukri
                    df = scrape_multi_platform(
                        sites=["indeed", "naukri"],
                        search_term=keyword,
                        location=city,
                        results_wanted=limit_per_city,
                        hours_old=self.max_days * 24,
                        verbose=0
                    )

                    if len(df) == 0:
                        continue

                    # Process each job
                    for _, row in df.iterrows():
                        job_url = row.get('job_url', '')
                        if not job_url or self.sheets_manager.is_duplicate(job_url):
                            self.stats["duplicates_skipped"] += 1
                            continue

                        platform = row.get('site', 'indeed')
                        job_data = self._normalize_indeed_naukri_job(row, platform)

                        if self.sheets_manager.upload_job(platform, job_data):
                            uploaded += 1
                            if platform == 'indeed':
                                self.stats["indeed_jobs"] += 1
                            else:
                                self.stats["naukri_jobs"] += 1

                            logger.info(f"  ✓ {platform.capitalize()}: {row.get('title')} at {row.get('company')}")

                except Exception as e:
                    self.stats["errors"] += 1
                    logger.debug(f"API scraping error: {e}")

                time.sleep(1)  # Use sync sleep for non-async function

            time.sleep(2)  # Use sync sleep for non-async function

        return uploaded
    
    async def run(
        self,
        cities: List[str] = None,
        include_internships: bool = True,
        limit_per_city: int = 10,
        tier_1_only: bool = False
    ) -> Dict[str, Any]:
        """Run unified scraping workflow."""

        cities = cities or DEFAULT_CITIES
        if tier_1_only:
            cities = cities[:6]  # Top 6 Tier 1 cities

        # Combine keywords
        keywords = CONSULTING_KEYWORDS.copy()
        if include_internships:
            keywords.extend(INTERNSHIP_KEYWORDS)

        print("\n" + "="*70)
        print("🚀 UNIFIED INDIA JOBS SCRAPER")
        print("="*70)
        print(f"📍 Platforms: {', '.join(self.platforms)}")
        print(f"📍 Cities: {len(cities)}")
        print(f"📍 Keywords: {len(keywords)}")
        print(f"📍 Limit per city: {limit_per_city}")
        print(f"📍 Time Filter: PAST {self.max_days} DAYS")
        print("="*70 + "\n")

        # Initialize and connect to Google Sheets
        self.sheets_manager = UnifiedSheetsManager(
            sheet_id=self.sheet_id,
            credentials_file=self.credentials_file
        )
        
        if not self.sheets_manager.connect(self.platforms):
            return {"success": False, "error": "Google Sheets connection failed"}

        total_uploaded = 0
        
        # Scrape LinkedIn if requested
        if "linkedin" in self.platforms:
            print("\n" + "="*70)
            print("🔗 LINKEDIN SCRAPING")
            print("="*70)
            
            async with BrowserManager(headless=self.headless) as browser:
                # Load session
                try:
                    await browser.load_session("linkedin_session.json")
                    print("✓ LinkedIn session loaded\n")
                except Exception as e:
                    logger.error(f"Failed to load LinkedIn session: {e}")
                    return {"success": False, "error": str(e)}
                
                linkedin_uploaded = await self.scrape_linkedin(
                    browser,
                    cities,
                    keywords,
                    limit_per_keyword=limit_per_city
                )
                total_uploaded += linkedin_uploaded
                print(f"\n✅ LinkedIn: {linkedin_uploaded} jobs uploaded\n")
        
        # Scrape Indeed and Naukri if requested
        api_platforms = [p for p in self.platforms if p in ["indeed", "naukri"]]
        if api_platforms:
            print("\n" + "="*70)
            print(f"📡 API SCRAPING ({', '.join(api_platforms).upper()})")
            print("="*70)
            
            api_uploaded = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.scrape_indeed_naukri(cities, keywords, limit_per_city)
            )
            total_uploaded += api_uploaded
            print(f"\n✅ API Platforms: {api_uploaded} jobs uploaded\n")
        
        # Update statistics
        self.stats["total_jobs"] = total_uploaded
        
        # Upload summary
        self.sheets_manager.upload_summary(self.stats)
        
        # Print summary
        self._print_summary()
        
        return {
            "success": total_uploaded > 0,
            "total_jobs": total_uploaded,
            "stats": self.stats
        }
    
    def _print_summary(self):
        """Print workflow summary."""
        print("\n" + "="*70)
        print("📊 WORKFLOW SUMMARY")
        print("="*70)
        print(f"🔗 LinkedIn Jobs:  {self.stats['linkedin_jobs']}")
        print(f"📡 Indeed Jobs:   {self.stats['indeed_jobs']}")
        print(f"🇮🇳  Naukri Jobs:    {self.stats['naukri_jobs']}")
        print(f"📈 Total Jobs:    {self.stats['total_jobs']}")
        print(f"⚠️  Duplicates:     {self.stats['duplicates_skipped']}")
        print(f"❌ Errors:         {self.stats['errors']}")
        print("="*70)
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified India Jobs Scraper - LinkedIn + Indeed + Naukri",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape_all_india_jobs.py
  python scrape_all_india_jobs.py --platforms linkedin indeed
  python scrape_all_india_jobs.py --max-days 3
  python scrape_all_india_jobs.py --tier-1-only
  python scrape_all_india_jobs.py --no-internships
        """
    )

    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["linkedin", "indeed", "naukri"],
        default=DEFAULT_JOB_BOARDS,
        help="Platforms to scrape (default: all three)"
    )
    parser.add_argument(
        "--max-days",
        type=int,
        default=2,
        help="Max job age in days (default: 2)"
    )
    parser.add_argument(
        "--limit-per-city",
        type=int,
        default=DEFAULT_RESULTS_PER_CITY,
        help="Jobs per keyword per city (default: 10)"
    )
    parser.add_argument(
        "--headless",
        type=bool,
        default=True,
        help="Headless mode for LinkedIn (default: True)"
    )
    parser.add_argument(
        "--no-internships",
        action="store_true",
        help="Exclude internship keywords"
    )
    parser.add_argument(
        "--tier-1-only",
        action="store_true",
        help="Search only Tier 1 cities"
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        help="Specific cities to search"
    )

    args = parser.parse_args()

    # Create and run unified scraper
    scraper = UnifiedIndiaJobsScraper(
        platforms=args.platforms,
        max_days=args.max_days,
        headless=args.headless
    )

    results = await scraper.run(
        cities=args.cities,
        include_internships=not args.no_internships,
        limit_per_city=args.limit_per_city,
        tier_1_only=args.tier_1_only
    )

    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
