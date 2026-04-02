#!/usr/bin/env python3
"""
LinkedIn Consulting Jobs Scraper - India
⚡ FRESH CONSULTING JOBS - 48 HOURS ONLY ⚡

Automatically scrapes consulting roles from major Indian cities posted in the PAST 2 DAYS
and uploads to Google Sheets.

Target Cities:
- Chennai, Mumbai, Pune, Gurugram, New Delhi, Noida
- Bangalore, Hyderabad, Kolkata, Ahmedabad
- And other major IT/consulting hubs

Target Roles:
- Management Consultant
- Business Consultant
- Strategy Consultant
- IT Consultant
- Financial Consultant
- HR Consultant
- And all other consulting roles

⚡ CRITICAL: Only jobs posted in past 48 hours are included!

Usage:
    python scrape_consulting_india.py

    # With options
    python scrape_consulting_india.py --limit-per-city 10
    python scrape_consulting_india.py --headless False
    python scrape_consulting_india.py --max-days 2
"""
import asyncio
import argparse
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

from linkedin_scraper import BrowserManager, ConsoleCallback
from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration
from linkedin_scraper.core.exceptions import ScrapingError, AuthenticationError

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
# CONFIGURATION - CONSULTING ROLES & CITIES
# ============================================================================

# Consulting-related keywords to search
CONSULTING_KEYWORDS = [
    "Management Consultant",
    "Business Consultant",
    "Strategy Consultant",
    "IT Consultant",
    "Technology Consultant",
    "Digital Consultant",
    "Financial Consultant",
    "Finance Consultant",
    "HR Consultant",
    "Human Resources Consultant",
    "Operations Consultant",
    "Process Consultant",
    "SAP Consultant",
    "Oracle Consultant",
    "Salesforce Consultant",
    "Cloud Consultant",
    "Cybersecurity Consultant",
    "Security Consultant",
    "Data Consultant",
    "Analytics Consultant",
    "Business Intelligence Consultant",
    "ERP Consultant",
    "CRM Consultant",
    "Risk Consultant",
    "Compliance Consultant",
    "Tax Consultant",
    "Audit Consultant",
    "Legal Consultant",
    "Corporate Consultant",
    "Executive Consultant",
    "Senior Consultant",
    "Principal Consultant",
    "Lead Consultant",
    "Consulting Analyst",
    "Business Analyst",  # Often part of consulting firms
    "Management Analyst",
]

# Major Indian cities for consulting jobs
INDIAN_CITIES = [
    # Tier 1 - Major metros
    "Bangalore",
    "Mumbai",
    "Chennai",
    "Pune",
    "Hyderabad",
    "Gurugram",
    "Gurgaon",  # Alternative spelling
    "New Delhi",
    "Delhi",
    "Noida",
    
    # Tier 2 - IT/Consulting hubs
    "Kolkata",
    "Ahmedabad",
    "Kochi",
    "Coimbatore",
    "Chandigarh",
    "Jaipur",
    "Thiruvananthapuram",
    "Visakhapatnam",
    "Nagpur",
    "Indore",
    
    # Other important cities
    "Bhopal",
    "Lucknow",
    "Surat",
    "Vadodara",
    "Bhubaneswar",
    "Mangalore",
    "Nashik",
]

# Optional: Add "Remote" for India-based remote roles
INCLUDE_REMOTE = True


# ============================================================================
# MAIN WORKFLOW CLASS
# ============================================================================

class ConsultingJobsScraper:
    """
    Specialized scraper for consulting jobs in India.
    """
    
    def __init__(
        self,
        session_file: str = "linkedin_session.json",
        credentials_file: Optional[str] = None,
        sheet_id: Optional[str] = None,
        worksheet_name: str = "Consulting_Jobs_India",
        headless: bool = True
    ):
        """
        Initialize the consulting jobs scraper.
        
        Args:
            session_file: Path to LinkedIn session file
            credentials_file: Path to Google credentials JSON
            sheet_id: Google Sheet ID
            worksheet_name: Name of worksheet tab
            headless: Run browser in headless mode
        """
        self.session_file = session_file
        self.headless = headless
        
        # Initialize Google Sheets integration
        self.sheets = GoogleSheetsIntegration(
            credentials_file=credentials_file,
            sheet_id=sheet_id
        )
        self.worksheet_name = worksheet_name
        
        # Callbacks for progress
        self.callback = ConsoleCallback()
    
    async def scrape_city(
        self,
        browser,
        city: str,
        keywords: List[str],
        limit_per_keyword: int = 5,
        skip_duplicates: bool = True,
        max_days_old: int = 2  # CRITICAL: Only 2 days (48 hours)
    ) -> Dict[str, Any]:
        """
        Scrape consulting jobs from a specific city.

        Args:
            browser: Browser manager instance
            city: City name
            keywords: List of consulting keywords
            limit_per_keyword: Jobs to scrape per keyword
            skip_duplicates: Skip jobs already in sheet
            max_days_old: Maximum job age in days (default: 2)

        Returns:
            Dictionary with scraping results
        """
        results = {
            "city": city,
            "jobs_found": 0,
            "jobs_scraped": 0,
            "jobs_fresh": 0,  # Jobs from past 2 days
            "jobs_uploaded": 0,
            "duplicates_skipped": 0,
            "jobs_old_skipped": 0,
            "errors": []
        }
        
        search_scraper = JobSearchScraper(browser.page, callback=self.callback)
        job_scraper = JobScraper(browser.page, callback=self.callback)
        
        for keyword in keywords:
            try:
                # Search for jobs
                search_query = f"{keyword}"
                logger.info(f"Searching: {keyword} in {city}")
                
                job_urls = await search_scraper.search(
                    keywords=search_query,
                    location=city,
                    limit=limit_per_keyword
                )
                
                results["jobs_found"] += len(job_urls)
                
                if not job_urls:
                    continue
                
                # Scrape and upload each job
                for job_url in job_urls:
                    # Check for duplicates
                    if skip_duplicates and self.sheets.check_duplicate(job_url):
                        results["duplicates_skipped"] += 1
                        continue
                    
                    # Scrape job details
                    try:
                        job = await job_scraper.scrape(job_url)
                        results["jobs_scraped"] += 1

                        # Check if job is too old
                        if not self._is_job_recent(job.posted_date, max_days_old):
                            results["jobs_old_skipped"] += 1
                            logger.debug(f"  ⏰ Excluded (older than {max_days_old} days): {job.job_title}")
                            continue

                        results["jobs_fresh"] += 1

                        # Clean and prepare data
                        job_data = self._clean_job_data(job, city)

                        # Upload to Google Sheets
                        if self.sheets.upload_job(job_data):
                            results["jobs_uploaded"] += 1
                            print(f"  ✓ {job.job_title} at {job.company} ({city})")
                        else:
                            results["errors"].append(f"Upload failed for {job_url}")

                    except ScrapingError as e:
                        results["errors"].append(f"Scraping error: {e}")
                        continue
                    except AuthenticationError as e:
                        results["errors"].append(f"Auth error: {e}")
                        break
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                
                # Delay between keywords
                await asyncio.sleep(2)
                
            except Exception as e:
                results["errors"].append(f"Search error for {keyword}: {e}")
                continue
        
        return results
    
    def _clean_job_data(self, job, city: str = "") -> Dict[str, Any]:
        """
        Clean and format job data for Google Sheets.
        
        Args:
            job: Job object from scraper
            city: City where job was searched

        Returns:
            Cleaned dictionary of job data
        """
        # Clean job description
        description = job.job_description or ""
        if description:
            # Remove LinkedIn artifacts
            description = description.replace("… more", "")
            description = description.replace("... more", "")
            description = description.replace("Show less", "")
            description = description.replace("Show more", "")
            description = description.replace("See less", "")

            # Remove excessive whitespace
            lines = description.split('\n')
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            description = '\n'.join(cleaned_lines)

            # Truncate if too long
            if len(description) > 45000:
                description = description[:45000] + "..."

        # Clean job title
        job_title = job.job_title or ""
        if job_title:
            job_title = job_title.strip()

        # Clean employment type
        employment_type = job.employment_type or ""
        if employment_type:
            employment_type = employment_type.strip()

        # Clean location
        location = job.location or city
        if location:
            location = location.strip()

        return {
            "job_title": job_title,
            "company": job.company or "",
            "company_logo": job.company_logo or "",  # NEW: Company logo URL
            "employment_type": employment_type,
            "location": location,
            "posted_date": job.posted_date or "",
            "linkedin_url": job.linkedin_url,
            "job_description": description,
            "search_city": city,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _is_job_recent(self, posted_date: Optional[str], max_days: int = 2) -> bool:
        """
        Check if a job is recent enough (not older than max_days).
        CRITICAL: Default is 2 DAYS (48 hours) for fresh jobs only!

        Args:
            posted_date: Posted date string from LinkedIn
            max_days: Maximum age in days (default: 2)

        Returns:
            True if job is recent, False if too old
        """
        if not posted_date:
            return False

        posted_lower = posted_date.lower().strip()

        try:
            import re
            match = re.search(r'(\d+)\s*(minute|hour|day|week|month)', posted_lower)

            if not match:
                return False

            value = int(match.group(1))
            unit = match.group(2)

            days_ago = 0
            if unit == 'minute':
                days_ago = value / (24 * 60)
            elif unit == 'hour':
                days_ago = value / 24
            elif unit == 'day':
                # "1 day ago" could be 24-48 hours
                # "2 days ago" is definitely > 48 hours
                if value >= 3:
                    return False
                days_ago = value
            elif unit == 'week':
                days_ago = value * 7
            elif unit == 'month':
                days_ago = value * 30

            return days_ago <= max_days

        except Exception:
            return False
    
    async def run(
        self,
        cities: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        limit_per_city: int = 10,
        skip_duplicates: bool = True,
        include_remote: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete consulting jobs scraping workflow.
        
        Args:
            cities: List of cities to scrape (default: all Indian cities)
            keywords: List of keywords (default: all consulting keywords)
            limit_per_city: Max jobs per city
            skip_duplicates: Skip jobs already in sheet
            include_remote: Include remote India jobs
            
        Returns:
            Dictionary with workflow results
        """
        results = {
            "success": False,
            "cities_searched": 0,
            "total_jobs_found": 0,
            "total_jobs_scraped": 0,
            "total_jobs_fresh": 0,  # Jobs from past 2 days
            "total_jobs_uploaded": 0,
            "total_duplicates_skipped": 0,
            "total_jobs_old_skipped": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }

        # Use defaults if not specified
        cities = cities or INDIAN_CITIES
        keywords = keywords or CONSULTING_KEYWORDS

        print("\n" + "="*70)
        print("⚡ FRESH CONSULTING JOBS - India (48 HOURS ONLY)")
        print("="*70)
        print(f"📍 Cities: {len(cities)}")
        print(f"📍 Keywords: {len(keywords)} consulting roles")
        print(f"📍 Limit per city: {limit_per_city} jobs")
        print(f"📍 Include Remote: {include_remote}")
        print(f"⚡ Time Filter: PAST 2 DAYS ONLY")
        print("="*70 + "\n")
        
        # Connect to Google Sheets
        print("📊 Connecting to Google Sheets...")
        if not self.sheets.connect(worksheet_name=self.worksheet_name):
            error_msg = "Failed to connect to Google Sheets. Check credentials."
            results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return results
        print("✓ Connected to Google Sheets\n")
        
        async with BrowserManager(headless=self.headless) as browser:
            # Load LinkedIn session
            print("🔑 Loading LinkedIn session...")
            try:
                await browser.load_session(self.session_file)
                print("✓ Session loaded\n")
            except Exception as e:
                error_msg = f"Failed to load LinkedIn session: {e}"
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                print("\n💡 Run 'python samples/create_session.py' to create a session")
                return results
            
            # Scrape each city
            for i, city in enumerate(cities, 1):
                print(f"\n{'='*70}")
                print(f"🏙️  City {i}/{len(cities)}: {city}")
                print(f"{'='*70}")
                
                city_results = await self.scrape_city(
                    browser=browser,
                    city=city,
                    keywords=keywords,
                    limit_per_keyword=max(1, limit_per_city // len(keywords)),
                    skip_duplicates=skip_duplicates
                )
                
                results["cities_searched"] += 1
                results["total_jobs_found"] += city_results["jobs_found"]
                results["total_jobs_scraped"] += city_results["jobs_scraped"]
                results["total_jobs_fresh"] += city_results["jobs_fresh"]
                results["total_jobs_uploaded"] += city_results["jobs_uploaded"]
                results["total_duplicates_skipped"] += city_results["duplicates_skipped"]
                results["total_jobs_old_skipped"] += city_results["jobs_old_skipped"]
                results["errors"].extend(city_results["errors"])
                
                print(f"\n📊 City Summary: {city}")
                print(f"   Found: {city_results['jobs_found']}")
                print(f"   Scraped: {city_results['jobs_scraped']}")
                print(f"   ⚡ Fresh Jobs (<2 days): {city_results['jobs_fresh']}")
                print(f"   Uploaded: {city_results['jobs_uploaded']}")
                print(f"   Skipped (dupes): {city_results['duplicates_skipped']}")
                print(f"   Skipped (old): {city_results['jobs_old_skipped']}")
                
                # Delay between cities to avoid rate limiting
                if i < len(cities):
                    print(f"\n⏳ Waiting 5 seconds before next city...")
                    await asyncio.sleep(5)
            
            # Scrape remote India jobs if enabled
            if include_remote:
                print(f"\n{'='*70}")
                print(f"🏠 Remote Jobs (India-based)")
                print(f"{'='*70}")
                
                remote_results = await self.scrape_city(
                    browser=browser,
                    city="India",
                    keywords=[f"{k} Remote" for k in keywords[:10]],  # Top 10 keywords
                    limit_per_keyword=2,
                    skip_duplicates=skip_duplicates
                )
                
                results["total_jobs_found"] += remote_results["jobs_found"]
                results["total_jobs_scraped"] += remote_results["jobs_scraped"]
                results["total_jobs_fresh"] += remote_results.get("jobs_fresh", 0)
                results["total_jobs_uploaded"] += remote_results["jobs_uploaded"]
                results["total_duplicates_skipped"] += remote_results["duplicates_skipped"]
                results["total_jobs_old_skipped"] += remote_results.get("jobs_old_skipped", 0)
        
        # Print summary
        results["success"] = results["total_jobs_uploaded"] > 0
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print workflow summary."""
        print("\n" + "="*70)
        print("📊 WORKFLOW SUMMARY")
        print("="*70)
        print(f"✅ Success: {results['success']}")
        print(f"🏙️  Cities Searched: {results['cities_searched']}")
        print(f"📍 Total Jobs Found: {results['total_jobs_found']}")
        print(f"📄 Total Jobs Scraped: {results['total_jobs_scraped']}")
        print(f"⚡ FRESH JOBS (<2 days): {results['total_jobs_fresh']}")
        print(f"📊 Total Jobs Uploaded: {results['total_jobs_uploaded']}")
        print(f"⚠️  Duplicates Skipped: {results['total_duplicates_skipped']}")
        print(f"❌ Old Jobs Skipped: {results['total_jobs_old_skipped']}")

        if results["errors"]:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results["errors"][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(results["errors"]) > 5:
                print(f"   ... and {len(results['errors']) - 5} more")

        print("="*70)
        print(f"⏰ Completed at: {results['timestamp']}")
        print(f"💡 Tip: Run every 12-24 hours for freshest jobs")
        print("="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape consulting jobs from major Indian cities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape_consulting_india.py
  python scrape_consulting_india.py --limit-per-city 15
  python scrape_consulting_india.py --include-internships
  python scrape_consulting_india.py --headless False
  python scrape_consulting_india.py --cities "Bangalore" "Mumbai" "Chennai"
        """
    )
    
    parser.add_argument(
        "--limit-per-city",
        type=int,
        default=10,
        help="Maximum jobs to scrape per city (default: 10)"
    )
    parser.add_argument(
        "--headless",
        type=bool,
        default=True,
        help="Run browser in headless mode (default: True)"
    )
    parser.add_argument(
        "--session-file",
        default="linkedin_session.json",
        help="Path to LinkedIn session file"
    )
    parser.add_argument(
        "--worksheet",
        default="Consulting_Jobs_India",
        help="Name of Google Sheet worksheet"
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable duplicate checking"
    )
    parser.add_argument(
        "--include-remote",
        action="store_true",
        default=True,
        help="Include remote India jobs (default: True)"
    )
    parser.add_argument(
        "--exclude-remote",
        action="store_true",
        help="Exclude remote jobs"
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        help="Specific cities to search (default: all major Indian cities)"
    )
    parser.add_argument(
        "--tier-1-only",
        action="store_true",
        help="Search only Tier 1 cities (metros)"
    )
    
    args = parser.parse_args()
    
    # Determine cities to search
    cities = args.cities
    if not cities and args.tier_1_only:
        cities = [
            "Bangalore", "Mumbai", "Chennai", "Pune",
            "Hyderabad", "Gurugram", "New Delhi", "Noida"
        ]
    
    # Create and run workflow
    workflow = ConsultingJobsScraper(
        session_file=args.session_file,
        headless=args.headless,
        worksheet_name=args.worksheet
    )
    
    results = await workflow.run(
        cities=cities,
        limit_per_city=args.limit_per_city,
        skip_duplicates=not args.no_dedup,
        include_remote=not args.exclude_remote
    )
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
