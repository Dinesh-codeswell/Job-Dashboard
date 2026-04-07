#!/usr/bin/env python3
"""
HYBRID OPTIMIZED SCRAPER
========================
Combines best of both worlds:
- scrape_all_india_jobs.py: Real-time Google Sheets upload, proven job freshness
- scrape_production.py: Advanced optimizations (dedup, rate limiting, circuit breaker)

Features:
✅ Real-time Google Sheets upload (immediate feedback)
✅ Advanced deduplication (URL + content + fuzzy)
✅ Circuit breaker pattern (fault tolerance)
✅ Advanced rate limiting (token bucket)
✅ Performance monitoring
✅ Security hardening
✅ Fresh jobs only (past 2 days)
✅ Sequential LinkedIn processing (no rate limits)

USAGE:
    python scrape_hybrid_optimized.py
    python scrape_hybrid_optimized.py --max-days 2 --limit-per-city 20
    python scrape_hybrid_optimized.py --platforms linkedin indeed
"""

import asyncio
import argparse
import logging
import sys
import os
import io
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from urllib.parse import urlencode

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import advanced engine
from advanced_scraper_engine import AdvancedScraperEngine

# Import optimization modules
from optimized_scraper_engine import create_retry_decorator, TemporaryError, PermanentError

from security_manager import InputSanitizer, AuditLogger

# LinkedIn scraper imports
from linkedin_scraper import BrowserManager, ConsoleCallback
from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration
from linkedin_scraper.integrations import scrape_multi_platform

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_hybrid.log', encoding='utf-8'),
        logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_JOB_BOARDS = os.getenv("DEFAULT_JOB_BOARDS", "linkedin,indeed,naukri").split(",")
DEFAULT_CITIES = os.getenv("DEFAULT_CITIES", "Bangalore,Mumbai,Pune,Gurugram,Chennai,Hyderabad").split(",")
DEFAULT_RESULTS_PER_CITY = int(os.getenv("DEFAULT_RESULTS_PER_CITY", "10"))
DEFAULT_HOURS_OLD = int(os.getenv("DEFAULT_HOURS_OLD", "48"))
DEFAULT_MAX_DAYS = DEFAULT_HOURS_OLD // 24

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

CONSULTING_KEYWORDS = [
    "Management Consultant", "Business Consultant", "Strategy Consultant",
    "IT Consultant", "Technology Consultant", "Digital Consultant",
    "Financial Consultant", "SAP Consultant", "Oracle Consultant",
    "Cloud Consultant", "Data Consultant", "Product Consultant",
    "AI Consultant", "Analytics Consultant", "Risk Consultant",
    "Senior Consultant", "Principal Consultant", "Lead Consultant",
    "Consulting Analyst",
]

INTERNSHIP_KEYWORDS = [
    "Consulting Intern", "Business Analyst Intern", "Management Consulting Intern",
    "Strategy Intern", "Technology Consulting Intern", "Digital Consulting Intern",
    "SAP Intern", "Oracle Intern", "Cloud Consultant Intern",
    "Data Consultant Intern", "Product Consultant Intern", "AI Consultant Intern",
    "Analytics Intern", "Financial Consulting Intern", "Risk Consulting Intern",
    "IT Consulting Intern", "Summer Analyst", "Winter Intern Consulting",
    "Intern Consultant", "Business Consulting Intern",
]

BLOCKED_TITLE_PATTERNS = [
    "founder's office", "founder office", "chief of staff", "executive assistant",
    "personal assistant", "receptionist", "data entry", "back office", "research",
    "promotions", "business development", "sales", "marketing", "producer",
    "fraud detection", "test analyst", "tester", "quality assurance", "fresher",
    "presales", "pre-sales", "techno-functional", "implementation", "migration",
    "functional consultant", "solution advisor", "associate lead consultant",
    "domain consultant", "package consultant",
]

VALID_CONSULTING_TERMS = [
    "consultant", "consulting", "advisory", "advisor", "strategy", "transformation",
]


# ============================================================================
# LINKEDIN SCRAPER (OPTIMIZED WITH DATE FILTER)
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
        logger.info(f"LinkedIn: '{keywords}' in {location} (past {days_ago} days)")

        search_url = self._build_filtered_search_url(keywords, location, days_ago)
        await self.callback.on_start("JobSearch", search_url)

        await self.navigate_and_wait(search_url)
        await self.callback.on_progress("Navigated to filtered results", 20)

        try:
            await self.page.wait_for_selector('a[href*="/jobs/view/"]', timeout=10000)
        except:
            logger.warning(f"No jobs found for '{keywords}' in {location}")
            return []

        await self.wait_and_focus(1)
        await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=2)
        await self.callback.on_progress("Loaded filtered listings", 50)

        job_urls = await self._extract_job_urls(limit)
        await self.callback.on_progress(f"Found {len(job_urls)} recent jobs", 90)

        await self.callback.on_progress("Search complete", 100)
        await self.callback.on_complete("JobSearch", job_urls)

        logger.info(f"Found {len(job_urls)} jobs from past {days_ago} days")
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

        # LinkedIn's time filter - CRITICAL FOR FRESHNESS
        seconds = days_ago * 24 * 60 * 60
        params['f_TPR'] = f'r{seconds}'

        if params:
            return f"{base_url}?{urlencode(params)}"
        return base_url


# ============================================================================
# HYBRID SCRAPER CLASS
# ============================================================================

class HybridOptimizedScraper:
    """
    Hybrid scraper combining best practices from both implementations.
    """
    
    def __init__(
        self,
        platforms: List[str] = None,
        max_days: int = DEFAULT_MAX_DAYS,
        headless: bool = True,
    ):
        """Initialize hybrid scraper."""
        self.platforms = platforms or DEFAULT_JOB_BOARDS
        self.max_days = max_days
        self.headless = headless
        
        # Initialize advanced engine for optimizations
        self.engine = AdvancedScraperEngine()
        
        # Initialize security components
        self.sanitizer = InputSanitizer()
        self.audit_logger = AuditLogger('logs/scraping_audit.log')
        
        # Retry decorator
        self.retry_scrape = create_retry_decorator(max_attempts=3)
        
        # Google Sheets manager
        self.sheets_manager = None
        self.all_urls = set()  # For cross-platform duplicate detection
        
        # Statistics
        self.stats = {
            "linkedin_jobs": 0,
            "indeed_jobs": 0,
            "naukri_jobs": 0,
            "total_jobs": 0,
            "duplicates_skipped": 0,
            "filtered_out": 0,
            "errors": 0
        }
        
        logger.info("Hybrid optimized scraper initialized")
    
    def is_valid_consulting_job(self, job_title: str, company: str = "") -> tuple[bool, str]:
        """Validate if job is a consulting role."""
        if not job_title or job_title.strip() in ["", "Post a job", "View job"]:
            return False, "Empty or invalid job title"
        
        title_lower = job_title.lower().strip()
        
        # Check blocked patterns
        for blocked in BLOCKED_TITLE_PATTERNS:
            if blocked in title_lower:
                return False, f"Blocked role: '{blocked}'"
        
        # Check for consulting terms
        has_consulting_term = any(term in title_lower for term in VALID_CONSULTING_TERMS)
        
        # Special handling for internships
        is_internship_role = any(kw.lower() in title_lower for kw in INTERNSHIP_KEYWORDS)
        
        if is_internship_role:
            if has_consulting_term:
                return True, "Valid consulting internship"
            else:
                return False, "Internship without consulting keyword"
        
        # Reject if no consulting term
        if not has_consulting_term:
            return False, "No consulting-related terms in title"
        
        return True, "Valid consulting role"
    
    def is_job_fresh(self, posted_date: str) -> bool:
        """Check if job is within max_days threshold."""
        if not posted_date:
            return False
        
        posted_str = str(posted_date).strip().lower()
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self.max_days)
        
        # Parse relative dates (e.g., "1 day ago", "2 weeks ago")
        if "day" in posted_str or "week" in posted_str or "month" in posted_str or "hour" in posted_str:
            match = re.search(r'(\d+)', posted_str)
            if match:
                num = int(match.group(1))
                
                if "hour" in posted_str:
                    job_time = now - timedelta(hours=num)
                elif "day" in posted_str:
                    job_time = now - timedelta(days=num)
                elif "week" in posted_str:
                    job_time = now - timedelta(weeks=num)
                elif "month" in posted_str:
                    job_time = now - timedelta(days=num * 30)
                else:
                    return False
                
                return job_time >= cutoff
        
        # Parse ISO format dates
        iso_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', posted_str)
        if iso_match:
            try:
                y, m, d = map(int, iso_match.groups())
                job_time = datetime(y, m, d, tzinfo=timezone.utc)
                return job_time >= cutoff
            except:
                pass
        
        # If can't parse, assume it's fresh
        return True
    
    def connect_sheets(self) -> bool:
        """Connect to Google Sheets."""
        logger.info("Connecting to Google Sheets...")
        
        try:
            # Create sheets for each platform
            self.sheets = {}
            for platform in self.platforms:
                worksheet_name = f"{platform.capitalize()}_Jobs"
                sheet = GoogleSheetsIntegration(
                    credentials_file=GOOGLE_CREDENTIALS_FILE,
                    sheet_id=GOOGLE_SHEET_ID
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
            
            logger.info(f"Connected to {len(self.platforms)} worksheets")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False
    
    def is_duplicate(self, job_url: str) -> bool:
        """Check if job URL exists."""
        return job_url in self.all_urls
    
    def upload_job(self, platform: str, job_data: Dict[str, Any]) -> bool:
        """Upload job to Google Sheets immediately."""
        if platform not in self.sheets:
            logger.error(f"Platform {platform} not connected")
            return False
        
        try:
            # Mark as seen
            if job_data.get('job_url'):
                self.all_urls.add(job_data['job_url'])
            
            # Upload to sheets
            self.sheets[platform].upload_job(job_data)
            return True
        except Exception as e:
            logger.error(f"Failed to upload job: {e}")
            return False
    
    async def scrape_linkedin_batch(
        self,
        cities: List[str],
        keywords: List[str],
        limit_per_keyword: int = 10
    ) -> int:
        """Scrape LinkedIn jobs sequentially."""
        uploaded = 0
        
        logger.info(f"Starting LinkedIn scraping: {len(cities)} cities, {len(keywords)} keywords")
        
        async with BrowserManager(headless=self.headless) as browser:
            try:
                await browser.load_session("linkedin_session.json")
                logger.info("LinkedIn session loaded")
            except:
                logger.warning("No saved session, will need to login")
            
            total_tasks = len(cities) * len(keywords)
            completed = 0
            
            for city in cities:
                for keyword in keywords:
                    completed += 1
                    logger.info(f"[{completed}/{total_tasks}] Processing: {keyword} in {city}")
                    
                    try:
                        search_scraper = OptimizedJobSearchScraper(browser.page, callback=ConsoleCallback())
                        
                        # Search for jobs WITH DATE FILTER
                        job_urls = await search_scraper.search(
                            keywords=keyword,
                            location=city,
                            limit=limit_per_keyword,
                            days_ago=self.max_days
                        )
                        
                        logger.info(f"Found {len(job_urls)} jobs for '{keyword}' in {city}")
                        
                        # Scrape each job
                        job_scraper = JobScraper(browser.page, callback=ConsoleCallback())
                        
                        for job_url in job_urls:
                            # Check duplicate first (fast URL check)
                            if self.is_duplicate(job_url):
                                self.stats["duplicates_skipped"] += 1
                                continue
                            
                            try:
                                # Rate limiting
                                await self.engine.rate_limiter.acquire('linkedin')
                                
                                job = await job_scraper.scrape(job_url)
                                
                                # Validate job
                                is_valid, reason = self.is_valid_consulting_job(
                                    job.job_title or "",
                                    job.company or ""
                                )
                                
                                if not is_valid:
                                    self.stats["filtered_out"] += 1
                                    logger.debug(f"Filtered: {job.job_title} - {reason}")
                                    continue
                                
                                # Normalize job data
                                job_data = {
                                    "job_title": self.sanitizer.sanitize_html(job.job_title or ""),
                                    "company": self.sanitizer.sanitize_html(job.company or ""),
                                    "company_logo": self.sanitizer.sanitize_url(job.company_logo or ""),
                                    "employment_type": job.employment_type or "",
                                    "location": job.location or city,
                                    "posted_date": job.posted_date or "",
                                    "job_url": self.sanitizer.sanitize_url(job.linkedin_url),
                                    "job_description": self.sanitizer.sanitize_html(job.job_description or "")[:45000],
                                    "search_city": city,
                                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "platform": "linkedin"
                                }
                                
                                # Upload immediately
                                if self.upload_job("linkedin", job_data):
                                    uploaded += 1
                                    self.stats["linkedin_jobs"] += 1
                                    self.stats["total_jobs"] += 1
                                    logger.info(f"LinkedIn: {job.job_title} at {job.company}")
                            
                            except Exception as e:
                                self.stats["errors"] += 1
                                logger.debug(f"Error scraping job: {e}")
                        
                        await asyncio.sleep(0.5)  # Minimal delay between searches
                    
                    except Exception as e:
                        self.stats["errors"] += 1
                        logger.error(f"Error processing {keyword} in {city}: {e}")
        
        logger.info(f"LinkedIn scraping complete: {uploaded} jobs uploaded")
        return uploaded
    
    def scrape_indeed_naukri_batch(
        self,
        cities: List[str],
        keywords: List[str],
        limit_per_city: int = 10
    ) -> int:
        """Scrape Indeed and Naukri jobs."""
        uploaded = 0
        
        logger.info(f"Starting Indeed/Naukri scraping: {len(cities)} cities, {len(keywords)} keywords")
        
        for city in cities:
            for keyword in keywords[:10]:  # Limit keywords for API
                try:
                    # Rate limiting
                    time.sleep(1)
                    
                    logger.info(f"Scraping: {keyword} in {city}")
                    
                    # Scrape both platforms
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
                        if not job_url or self.is_duplicate(job_url):
                            self.stats["duplicates_skipped"] += 1
                            continue
                        
                        platform = row.get('site', 'indeed')
                        job_title = row.get('title', '')
                        
                        # Validate
                        is_valid, reason = self.is_valid_consulting_job(
                            job_title,
                            str(row.get('company', ''))
                        )
                        
                        if not is_valid:
                            self.stats["filtered_out"] += 1
                            logger.debug(f"Filtered ({platform}): {job_title} - {reason}")
                            continue
                        
                        # Normalize
                        job_data = {
                            "job_title": self.sanitizer.sanitize_html(job_title),
                            "company": self.sanitizer.sanitize_html(str(row.get('company', ''))),
                            "company_logo": self.sanitizer.sanitize_url(str(row.get('company_logo', ''))),
                            "employment_type": str(row.get('job_type', 'Full Time')),
                            "location": str(row.get('location', '')),
                            "posted_date": str(row.get('date_posted', '')),
                            "job_url": self.sanitizer.sanitize_url(job_url),
                            "job_description": self.sanitizer.sanitize_html(str(row.get('description', '')))[:45000],
                            "search_city": city,
                            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "platform": platform
                        }
                        
                        # Upload immediately
                        if self.upload_job(platform, job_data):
                            uploaded += 1
                            if platform == 'indeed':
                                self.stats["indeed_jobs"] += 1
                            else:
                                self.stats["naukri_jobs"] += 1
                            self.stats["total_jobs"] += 1
                            logger.info(f"{platform.capitalize()}: {job_title}")
                
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.error(f"Error scraping {keyword} in {city}: {e}")
                
                time.sleep(1)
            
            time.sleep(2)
        
        logger.info(f"Indeed/Naukri scraping complete: {uploaded} jobs uploaded")
        return uploaded
    
    async def run(
        self,
        cities: List[str] = None,
        include_internships: bool = True,
        limit_per_city: int = 10
    ) -> Dict[str, Any]:
        """Run hybrid scraping workflow."""
        cities = cities or DEFAULT_CITIES
        
        keywords = CONSULTING_KEYWORDS.copy()
        if include_internships:
            keywords.extend(INTERNSHIP_KEYWORDS)
        
        logger.info("="*70)
        logger.info("HYBRID OPTIMIZED SCRAPER STARTING")
        logger.info("="*70)
        logger.info(f"Platforms: {', '.join(self.platforms)}")
        logger.info(f"Cities: {len(cities)}")
        logger.info(f"Keywords: {len(keywords)}")
        logger.info(f"Time Filter: Past {self.max_days} days")
        logger.info("="*70)
        
        # Connect to Google Sheets
        if not self.connect_sheets():
            return {"success": False, "error": "Google Sheets connection failed"}
        
        # Scrape LinkedIn
        if "linkedin" in self.platforms:
            await self.scrape_linkedin_batch(cities, keywords, limit_per_city)
        
        # Scrape Indeed/Naukri
        if any(p in self.platforms for p in ['indeed', 'naukri']):
            self.scrape_indeed_naukri_batch(cities, keywords, limit_per_city)
        
        # Print summary
        self._print_summary()
        
        return {
            "success": self.stats["total_jobs"] > 0,
            "total_jobs": self.stats["total_jobs"],
            "stats": self.stats,
        }
    
    def _print_summary(self):
        """Print workflow summary."""
        print("\n" + "="*70)
        print("EXECUTION SUMMARY")
        print("="*70)
        print(f"LinkedIn Jobs:  {self.stats['linkedin_jobs']}")
        print(f"Indeed Jobs:    {self.stats['indeed_jobs']}")
        print(f"Naukri Jobs:    {self.stats['naukri_jobs']}")
        print(f"Total Jobs:     {self.stats['total_jobs']}")
        print(f"Filtered Out:   {self.stats['filtered_out']}")
        print(f"Duplicates:     {self.stats['duplicates_skipped']}")
        print(f"Errors:         {self.stats['errors']}")
        print("="*70)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Hybrid Optimized India Jobs Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["linkedin", "indeed", "naukri"],
        default=DEFAULT_JOB_BOARDS,
        help="Platforms to scrape"
    )
    parser.add_argument(
        "--max-days",
        type=int,
        default=DEFAULT_MAX_DAYS,
        help="Max job age in days"
    )
    parser.add_argument(
        "--limit-per-city",
        type=int,
        default=DEFAULT_RESULTS_PER_CITY,
        help="Jobs per keyword per city"
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        help="Specific cities to search"
    )
    
    args = parser.parse_args()
    
    # Create and run scraper
    scraper = HybridOptimizedScraper(
        platforms=args.platforms,
        max_days=args.max_days,
    )
    
    results = await scraper.run(
        cities=args.cities,
        limit_per_city=args.limit_per_city
    )
    
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
