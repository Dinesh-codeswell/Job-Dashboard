#!/usr/bin/env python3
"""
DELOITTE JOBS SCRAPER
=====================
Optimized scraper for Deloitte jobs on LinkedIn (last 48 hours)

USAGE:
    python scrape_deloitte_jobs.py
    python scrape_deloitte_jobs.py --max-days 2 --limit 50
    python scrape_deloitte_jobs.py --cities "Bangalore" "Mumbai" "Pune"
"""

import asyncio
import argparse
import logging
import sys
import io
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from urllib.parse import urlencode

from dotenv import load_dotenv
load_dotenv()

from linkedin_scraper import BrowserManager, ConsoleCallback
from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration
from security_manager import InputSanitizer
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deloitte_scraper.log', encoding='utf-8'),
        logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
    ]
)
logger = logging.getLogger(__name__)

# Configuration
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# Deloitte-specific keywords (consulting roles)
DELOITTE_KEYWORDS = [
    "Consultant",
    "Senior Consultant",
    "Manager",
    "Senior Manager",
    "Analyst",
    "Senior Analyst",
    "Associate",
    "Strategy Consultant",
    "Management Consultant",
    "Business Analyst",
]

DEFAULT_CITIES = ["Bangalore", "Mumbai", "Pune", "Gurugram", "Hyderabad", "Chennai"]


class DeloitteJobSearchScraper(JobSearchScraper):
    """Enhanced job search scraper with company filter for Deloitte."""

    async def search(
        self,
        keywords: str = None,
        location: str = None,
        company: str = "Deloitte",
        limit: int = 25,
        days_ago: int = 2
    ) -> List[str]:
        """Search for Deloitte jobs with LinkedIn's native filters."""
        logger.info(f"LinkedIn: '{keywords}' at {company} in {location} (past {days_ago} days)")

        search_url = self._build_company_search_url(keywords, location, company, days_ago)
        await self.callback.on_start("JobSearch", search_url)

        await self.navigate_and_wait(search_url)
        await self.callback.on_progress("Navigated to filtered results", 20)

        try:
            await self.page.wait_for_selector('a[href*="/jobs/view/"]', timeout=10000)
        except:
            logger.warning(f"No jobs found for '{keywords}' at {company} in {location}")
            return []

        await self.wait_and_focus(1)
        await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=5)
        await self.callback.on_progress("Loaded filtered listings", 50)

        job_urls = await self._extract_job_urls(limit)
        await self.callback.on_progress(f"Found {len(job_urls)} recent jobs", 90)

        await self.callback.on_complete("JobSearch", job_urls)

        logger.info(f"Found {len(job_urls)} Deloitte jobs from past {days_ago} days")
        return job_urls

    def _build_company_search_url(
        self,
        keywords: str = None,
        location: str = None,
        company: str = "Deloitte",
        days_ago: int = 2
    ) -> str:
        """Build LinkedIn search URL with company filter."""
        base_url = "https://www.linkedin.com/jobs/search/"
        params = {}

        # Combine keywords with company name for better results
        if keywords:
            params['keywords'] = f"{keywords} {company}"
        else:
            params['keywords'] = company
        
        if location:
            params['location'] = location

        # Time filter (past X days)
        seconds = days_ago * 24 * 60 * 60
        params['f_TPR'] = f'r{seconds}'
        
        # Company filter (Deloitte's LinkedIn company ID)
        # Note: You may need to find Deloitte's exact company ID
        # For now, we'll rely on keyword matching
        
        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url


class DeloitteScraper:
    """Scraper optimized for Deloitte jobs only."""
    
    def __init__(self, max_days: int = 2, headless: bool = True):
        self.max_days = max_days
        self.headless = headless
        self.sanitizer = InputSanitizer()
        self.sheets_manager = None
        self.all_urls = set()
        
        self.stats = {
            "total_jobs": 0,
            "duplicates_skipped": 0,
            "filtered_out": 0,
            "errors": 0,
        }
    
    def connect_sheets(self) -> bool:
        """Connect to Google Sheets."""
        logger.info("Connecting to Google Sheets...")
        
        try:
            self.sheets_manager = GoogleSheetsIntegration(
                credentials_file=GOOGLE_CREDENTIALS_FILE,
                sheet_id=GOOGLE_SHEET_ID
            )
            
            if not self.sheets_manager.connect(worksheet_name="Deloitte_Jobs"):
                logger.error("Failed to connect to Deloitte_Jobs worksheet")
                return False
            
            # Load existing URLs
            try:
                existing_jobs = self.sheets_manager.get_all_jobs()
                for job in existing_jobs:
                    if 'Job URL' in job:
                        self.all_urls.add(job['Job URL'])
                logger.info(f"Loaded {len(self.all_urls)} existing job URLs")
            except Exception as e:
                logger.debug(f"Could not load existing jobs: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False
    
    def is_duplicate(self, job_url: str) -> bool:
        """Check if job URL exists."""
        return job_url in self.all_urls
    
    def is_deloitte_job(self, company: str) -> bool:
        """Verify job is from Deloitte."""
        if not company:
            return False
        
        company_lower = company.lower().strip()
        
        # Match Deloitte and its subsidiaries
        deloitte_variants = [
            "deloitte",
            "deloitte consulting",
            "deloitte touche tohmatsu",
            "deloitte & touche",
            "deloitte us",
            "deloitte india",
            "deloitte usi",
        ]
        
        return any(variant in company_lower for variant in deloitte_variants)
    
    def upload_job(self, job_data: Dict[str, Any]) -> bool:
        """Upload job to Google Sheets."""
        try:
            if job_data.get('job_url'):
                self.all_urls.add(job_data['job_url'])
            
            self.sheets_manager.upload_job(job_data)
            return True
        except Exception as e:
            logger.error(f"Failed to upload job: {e}")
            return False
    
    async def scrape_deloitte_jobs(
        self,
        cities: List[str],
        keywords: List[str],
        limit_per_keyword: int = 10,
        max_jobs: int = None
    ) -> int:
        """Scrape Deloitte jobs from LinkedIn."""
        uploaded = 0
        
        logger.info("="*70)
        logger.info("🔵 DELOITTE JOBS SCRAPING STARTED")
        logger.info(f"Cities: {len(cities)}, Keywords: {len(keywords)}")
        if max_jobs:
            logger.info(f"Target: {max_jobs} jobs")
        logger.info("="*70)
        
        async with BrowserManager(headless=self.headless) as browser:
            try:
                await browser.load_session("linkedin_session.json")
                logger.info("LinkedIn session loaded")
            except:
                logger.warning("No saved session, will need to login")
            
            total_tasks = len(cities) * len(keywords)
            completed = 0
            
            for city in cities:
                if max_jobs and uploaded >= max_jobs:
                    break
                
                for keyword in keywords:
                    if max_jobs and uploaded >= max_jobs:
                        break
                    
                    completed += 1
                    remaining = max_jobs - uploaded if max_jobs else limit_per_keyword
                    actual_limit = min(limit_per_keyword, remaining) if max_jobs else limit_per_keyword
                    
                    logger.info(f"[{completed}/{total_tasks}] {keyword} in {city} [{uploaded}/{max_jobs or '∞'}]")
                    
                    try:
                        search_scraper = DeloitteJobSearchScraper(browser.page, callback=ConsoleCallback())
                        
                        job_urls = await search_scraper.search(
                            keywords=keyword,
                            location=city,
                            company="Deloitte",
                            limit=actual_limit,
                            days_ago=self.max_days
                        )
                        
                        logger.info(f"Found {len(job_urls)} jobs")
                        
                        job_scraper = JobScraper(browser.page, callback=ConsoleCallback())
                        
                        for job_url in job_urls:
                            if max_jobs and uploaded >= max_jobs:
                                break
                            
                            if self.is_duplicate(job_url):
                                self.stats["duplicates_skipped"] += 1
                                continue
                            
                            try:
                                job = await job_scraper.scrape(job_url)
                                
                                # Verify it's actually a Deloitte job
                                if not self.is_deloitte_job(job.company):
                                    self.stats["filtered_out"] += 1
                                    logger.info(f"❌ Not Deloitte: {job.company}")
                                    continue
                                
                                # Process description with proper extraction
                                description = job.job_description or ""
                                
                                # CRITICAL: Extract clean text from LinkedIn HTML
                                if description:
                                    try:
                                        from job_description_extractor import extract_job_description, extract_from_text
                                        
                                        # Extract clean text from HTML (synchronous function)
                                        description = extract_job_description(description, platform="linkedin") or extract_from_text(description) or description
                                        
                                        # Clean up artifacts
                                        description = description.replace("… more", "").replace("... more", "")
                                        description = description.replace("Show less", "").replace("Show more", "")
                                        
                                        if len(description) > 45000:
                                            description = description[:45000]
                                    except Exception as e:
                                        logger.debug(f"Description extraction error: {e}")
                                        # Fallback: basic cleanup
                                        description = description.replace("… more", "").replace("... more", "")
                                        if len(description) > 45000:
                                            description = description[:45000]
                                
                                # VALIDATION: Ensure extraction succeeded
                                if not description or len(description.strip()) < 200:
                                    self.stats["filtered_out"] += 1
                                    logger.info(f"❌ Rejected: '{job.job_title}' - JD extraction failed or too short")
                                    continue
                                
                                # Check for unpaid roles
                                if any(keyword in description.lower() for keyword in ['unpaid', 'no compensation', 'no pay', 'volunteer']):
                                    self.stats["filtered_out"] += 1
                                    logger.info(f"❌ Rejected: '{job.job_title}' - Unpaid role detected")
                                    continue
                                
                                job_data = {
                                    "job_title": self.sanitizer.sanitize_html(job.job_title or ""),
                                    "company": self.sanitizer.sanitize_html(job.company or ""),
                                    "company_logo": self.sanitizer.sanitize_url(job.company_logo or ""),
                                    "employment_type": job.employment_type or "Full Time",
                                    "location": job.location or city,
                                    "posted_date": job.posted_date or "",
                                    "job_url": self.sanitizer.sanitize_url(job.linkedin_url),
                                    "job_description": description,
                                    "search_city": city,
                                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "platform": "linkedin",
                                }
                                
                                if self.upload_job(job_data):
                                    uploaded += 1
                                    self.stats["total_jobs"] += 1
                                    logger.info(f"✓ Deloitte: {job.job_title} [{uploaded}/{max_jobs or '∞'}]")
                            
                            except Exception as e:
                                self.stats["errors"] += 1
                                logger.debug(f"Error scraping job: {e}")
                        
                        await asyncio.sleep(0.5)
                    
                    except Exception as e:
                        self.stats["errors"] += 1
                        logger.error(f"Error processing {keyword} in {city}: {e}")
        
        logger.info("="*70)
        logger.info(f"🔵 DELOITTE SCRAPING COMPLETE: {uploaded} jobs uploaded")
        logger.info("="*70)
        return uploaded
    
    async def run(
        self,
        cities: List[str] = None,
        limit_per_keyword: int = 10,
        max_jobs: int = 50,
    ) -> Dict[str, Any]:
        """Run Deloitte scraping workflow."""
        cities = cities or DEFAULT_CITIES
        
        logger.info("="*70)
        logger.info("DELOITTE JOBS SCRAPER")
        logger.info("="*70)
        logger.info(f"Cities: {', '.join(cities)}")
        logger.info(f"Keywords: {len(DELOITTE_KEYWORDS)}")
        logger.info(f"Time Filter: Past {self.max_days} days")
        logger.info(f"Target: {max_jobs} jobs")
        logger.info("="*70)
        
        if not self.connect_sheets():
            return {"success": False, "error": "Google Sheets connection failed"}
        
        await self.scrape_deloitte_jobs(
            cities,
            DELOITTE_KEYWORDS,
            limit_per_keyword,
            max_jobs
        )
        
        self._print_summary()
        
        return {
            "success": self.stats["total_jobs"] > 0,
            "total_jobs": self.stats["total_jobs"],
            "stats": self.stats,
        }
    
    def _print_summary(self):
        """Print summary."""
        print("\n" + "="*70)
        print("DELOITTE JOBS SCRAPING SUMMARY")
        print("="*70)
        print(f"Total Jobs:     {self.stats['total_jobs']}")
        print(f"Duplicates:     {self.stats['duplicates_skipped']}")
        print(f"Filtered Out:   {self.stats['filtered_out']}")
        print(f"Errors:         {self.stats['errors']}")
        print("="*70)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scrape Deloitte jobs from LinkedIn")
    
    parser.add_argument("--max-days", type=int, default=2, help="Max job age in days")
    parser.add_argument("--limit", type=int, default=50, help="Maximum jobs to scrape")
    parser.add_argument("--cities", nargs="+", help="Specific cities to search")
    
    args = parser.parse_args()
    
    scraper = DeloitteScraper(max_days=args.max_days)
    
    try:
        results = await scraper.run(
            cities=args.cities,
            max_jobs=args.limit
        )
        
        sys.exit(0 if results["success"] else 1)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        scraper._print_summary()
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
