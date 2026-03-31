#!/usr/bin/env python3
"""
LinkedIn Job Scraper to Google Sheets - Complete Workflow

This script scrapes job listings from LinkedIn and automatically uploads them to Google Sheets.

Usage:
    python jobs_to_sheets.py --keywords "software engineer" --location "San Francisco" --limit 10

Features:
    - Searches for jobs on LinkedIn
    - Scrapes detailed job information
    - Cleans and parses data
    - Uploads to Google Sheets
    - Skips duplicate jobs
    - Provides progress feedback
"""
import asyncio
import argparse
import logging
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

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


class JobScraperWorkflow:
    """
    Complete workflow for scraping LinkedIn jobs and uploading to Google Sheets.
    """
    
    def __init__(
        self,
        session_file: str = "linkedin_session.json",
        credentials_file: Optional[str] = None,
        sheet_id: Optional[str] = None,
        worksheet_name: str = "Jobs_v2",
        headless: bool = True
    ):
        """
        Initialize the workflow.
        
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
    
    async def run(
        self,
        keywords: str,
        location: Optional[str] = None,
        limit: int = 10,
        skip_duplicates: bool = True,
        max_days_old: int = 14
    ) -> Dict[str, Any]:
        """
        Run the complete job scraping workflow.
        
        Args:
            keywords: Job search keywords
            location: Job location (optional)
            limit: Maximum number of jobs to scrape
            skip_duplicates: Skip jobs already in the sheet
            max_days_old: Maximum age of jobs to add (default: 14 days)
            
        Returns:
            Dictionary with workflow results
        """
        results = {
            "success": False,
            "jobs_found": 0,
            "jobs_scraped": 0,
            "jobs_uploaded": 0,
            "duplicates_skipped": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "="*70)
        print("🚀 LinkedIn Job Scraper → Google Sheets")
        print("="*70)
        print(f"📍 Keywords: {keywords}")
        print(f"📍 Location: {location or 'Any'}")
        print(f"📍 Limit: {limit} jobs")
        print(f"📍 Headless: {self.headless}")
        print("="*70 + "\n")
        
        # Connect to Google Sheets
        print("📊 Connecting to Google Sheets...")
        if not self.sheets.connect(worksheet_name=self.worksheet_name):
            error_msg = "Failed to connect to Google Sheets. Check credentials."
            results["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            print("\n📖 Follow GOOGLE_SHEETS_SETUP.md to set up Google Sheets API")
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
            
            # Search for jobs
            print("🔍 Searching for jobs on LinkedIn...")
            search_scraper = JobSearchScraper(browser.page, callback=self.callback)
            try:
                job_urls = await search_scraper.search(
                    keywords=keywords,
                    location=location,
                    limit=limit
                )
                results["jobs_found"] = len(job_urls)
                print(f"✓ Found {len(job_urls)} job listings\n")
            except Exception as e:
                error_msg = f"Failed to search jobs: {e}"
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                return results
            
            if not job_urls:
                print("⚠️ No jobs found matching your criteria")
                results["success"] = True
                return results
            
            # Scrape and upload each job
            job_scraper = JobScraper(browser.page, callback=self.callback)
            print(f"📄 Scraping job details and uploading to Google Sheets...\n")
            
            for i, job_url in enumerate(job_urls, 1):
                print(f"[{i}/{len(job_urls)}] Processing: {job_url}")
                
                # Check for duplicates
                if skip_duplicates and self.sheets.check_duplicate(job_url):
                    print("  ⚠️ Skipping duplicate job")
                    results["duplicates_skipped"] += 1
                    continue
                
                # Scrape job details
                try:
                    job = await job_scraper.scrape(job_url)
                    results["jobs_scraped"] += 1
                    print(f"  ✓ Scraped: {job.job_title} at {job.company}")
                except ScrapingError as e:
                    print(f"  ⚠️ Failed to scrape: {e}")
                    results["errors"].append(f"Scraping error for {job_url}: {e}")
                    continue
                except AuthenticationError as e:
                    print(f"  ❌ Authentication error: {e}")
                    results["errors"].append(f"Auth error: {e}")
                    break
                
                # Check if job is too old (older than max_days_old)
                if not self._is_job_recent(job.posted_date, max_days_old):
                    print(f"  ⏰ Skipping - Job older than {max_days_old} days ({job.posted_date})")
                    results["jobs_old_skipped"] += 1
                    continue
                
                # Clean and prepare data
                job_data = self._clean_job_data(job)
                
                # Upload to Google Sheets
                if self.sheets.upload_job(job_data):
                    results["jobs_uploaded"] += 1
                    print(f"  ✓ Uploaded to Google Sheets")
                else:
                    print(f"  ⚠️ Failed to upload to Google Sheets")
                    results["errors"].append(f"Upload failed for {job_url}")
                
                # Small delay to avoid rate limiting
                if i < len(job_urls):
                    await asyncio.sleep(2)
            
            print("\n" + "="*70)

        # Print summary
        results["success"] = results["jobs_uploaded"] > 0
        self._print_summary(results)

        return results
    
    def _is_job_recent(self, posted_date: Optional[str], max_days: int = 14) -> bool:
        """
        Check if a job is recent enough (not older than max_days).
        
        Args:
            posted_date: Posted date string from LinkedIn (e.g., "2 hours ago", "3 days ago", "2 weeks ago")
            max_days: Maximum age in days (default: 14)
            
        Returns:
            True if job is recent, False if too old
        """
        if not posted_date:
            # If no date, assume it's recent to be safe
            return True
        
        posted_lower = posted_date.lower().strip()
        
        # Parse the time unit
        try:
            # Extract number from string like "2 hours ago", "3 days ago", "1 week ago"
            import re
            match = re.search(r'(\d+)\s*(minute|hour|day|week|month)', posted_lower)
            
            if not match:
                # If can't parse, assume recent
                return True
            
            value = int(match.group(1))
            unit = match.group(2)
            
            # Convert to days
            days_ago = 0
            if unit == 'minute' or unit == 'hour':
                days_ago = value / (24 * 60) if unit == 'minute' else value / 24
            elif unit == 'day':
                days_ago = value
            elif unit == 'week':
                days_ago = value * 7
            elif unit == 'month':
                days_ago = value * 30
            
            # Check if within max_days
            return days_ago <= max_days
            
        except Exception as e:
            # If parsing fails, assume recent to be safe
            return True

    def _clean_job_data(self, job) -> Dict[str, Any]:
        """
        Clean and format job data for Google Sheets.
        
        Args:
            job: Job object from scraper
            
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
            
            # Remove excessive whitespace but preserve line breaks for readability
            lines = description.split('\n')
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            description = '\n'.join(cleaned_lines)
            # Truncate if too long (Google Sheets limit is ~50,000 chars)
            if len(description) > 45000:
                description = description[:45000] + "..."
        
        # Clean location
        location = job.location or ""
        if location:
            location = location.strip()
        
        # Clean job title
        job_title = job.job_title or ""
        if job_title:
            job_title = job_title.strip()
        
        # Clean employment type
        employment_type = job.employment_type or ""
        if employment_type:
            employment_type = employment_type.strip()
        
        return {
            "job_title": job_title,
            "company": job.company or "",
            "employment_type": employment_type,
            "location": location,
            "posted_date": job.posted_date or "",
            "linkedin_url": job.linkedin_url,
            "job_description": description,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print workflow summary."""
        print("📊 WORKFLOW SUMMARY")
        print("="*70)
        print(f"✅ Success: {results['success']}")
        print(f"📍 Jobs Found: {results['jobs_found']}")
        print(f"📄 Jobs Scraped: {results['jobs_scraped']}")
        print(f"📊 Jobs Uploaded: {results['jobs_uploaded']}")
        print(f"⚠️ Duplicates Skipped: {results['duplicates_skipped']}")
        if 'jobs_old_skipped' in results and results['jobs_old_skipped'] > 0:
            print(f"⏰ Jobs Too Old (>14 days): {results['jobs_old_skipped']}")

        if results["errors"]:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results["errors"][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(results["errors"]) > 5:
                print(f"   ... and {len(results['errors']) - 5} more")

        print("="*70)
        print(f"⏰ Completed at: {results['timestamp']}")
        print("="*70 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape LinkedIn jobs and upload to Google Sheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python jobs_to_sheets.py --keywords "software engineer" --location "San Francisco"
  python jobs_to_sheets.py -k "data scientist" -l "Remote" --limit 20
  python jobs_to_sheets.py -k "product manager" --headless False
        """
    )
    
    parser.add_argument(
        "-k", "--keywords",
        required=True,
        help="Job search keywords (e.g., 'software engineer')"
    )
    parser.add_argument(
        "-l", "--location",
        default=None,
        help="Job location (e.g., 'San Francisco, CA' or 'Remote')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of jobs to scrape (default: 10)"
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
        help="Path to LinkedIn session file (default: linkedin_session.json)"
    )
    parser.add_argument(
        "--worksheet",
        default="Jobs",
        help="Name of Google Sheet worksheet (default: Jobs)"
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable duplicate checking (upload all jobs)"
    )
    
    args = parser.parse_args()
    
    # Create and run workflow
    workflow = JobScraperWorkflow(
        session_file=args.session_file,
        headless=args.headless
    )
    
    results = await workflow.run(
        keywords=args.keywords,
        location=args.location,
        limit=args.limit,
        skip_duplicates=not args.no_dedup
    )
    
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
