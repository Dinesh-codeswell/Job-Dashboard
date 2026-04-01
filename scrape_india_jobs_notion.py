#!/usr/bin/env python3
"""
LinkedIn Jobs Scraper - India (Core Technical & Business Roles)
⚡ FRESH JOBS DASHBOARD - 24 Hours Only ⚡

Scrapes LinkedIn jobs posted in the PAST 24 HOURS ONLY in India for core technical and
business roles (SDE, Analyst, APM, PM, Growth, etc.) and stores them in Notion.

DESIGNED FOR: Being the FASTEST to surface fresh job opportunities
- Scrape every 3-4 hours for best results
- Catch jobs within hours of posting
- Beat other job boards to fresh listings

Excludes basic roles like accountant, copywriter, video editor, etc.

Target Roles:
✓ Software Development Engineer (SDE)
✓ Product Manager (PM) / Associate Product Manager (APM)
✓ Data Analyst / Business Analyst
✓ Growth roles
✓ Technical Program Manager
✓ Solutions Architect
✓ DevOps Engineer
✓ Machine Learning Engineer
✓ Data Scientist
✓ Product Designer
✓ Strategy roles

Excluded Roles:
✗ Accountant
✗ Copywriter
✗ Video Editor
✗ Basic data entry
✗ Content writer (unless technical)
✗ Basic customer support

Usage:
    python scrape_india_jobs_notion.py

    # Run every 3-4 hours for freshest jobs
    python scrape_india_jobs_notion.py --limit 50
    python scrape_india_jobs_notion.py --keywords "SDE" "Product Manager"
"""
import asyncio
import argparse
import logging
import sys
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set

from linkedin_scraper import BrowserManager, ConsoleCallback
from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.integrations.notion import NotionIntegration
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
# CONFIGURATION - CORE TECHNICAL & BUSINESS ROLES
# ============================================================================

# Keywords for core technical and business roles (24hr focus)
TARGET_KEYWORDS = [
    # Software Engineering
    "Software Development Engineer",
    "SDE",
    "Software Engineer",
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "DevOps Engineer",
    "Site Reliability Engineer",
    "SRE",
    
    # Product Management
    "Product Manager",
    "PM",
    "Associate Product Manager",
    "APM",
    "Senior Product Manager",
    "Group Product Manager",
    "Technical Product Manager",
    
    # Analyst Roles
    "Data Analyst",
    "Business Analyst",
    "Product Analyst",
    "Financial Analyst",
    "Strategy Analyst",
    "Operations Analyst",
    "Research Analyst",
    "Investment Analyst",
    "Equity Research Analyst",
    "Business Intelligence Analyst",
    "Data Science Analyst",
    
    # Data Science & ML
    "Data Scientist",
    "Machine Learning Engineer",
    "ML Engineer",
    "AI Engineer",
    "Deep Learning Engineer",
    "NLP Engineer",
    "Computer Vision Engineer",
    
    # Growth & Business
    "Growth Manager",
    "Growth Hacker",
    "Business Development Manager",
    "Strategy Manager",
    "Operations Manager",
    "Program Manager",
    "Technical Program Manager",
    "TPM",
    "Project Manager",
    "Scrum Master",
    
    # Architecture & Consulting
    "Solutions Architect",
    "Cloud Architect",
    "Enterprise Architect",
    "Staff Engineer",
    "Principal Engineer",
    
    # Design
    "Product Designer",
    "UX Designer",
    "UI Designer",
    "Interaction Designer",
    "Design Lead",
    
    # Technical Consulting
    "Technology Consultant",
    "Digital Consultant",
    "IT Consultant",
    "Management Consultant",
    "Strategy Consultant",
]

# Keywords to EXCLUDE (basic/non-core roles)
EXCLUDE_KEYWORDS = [
    "Accountant",
    "Accounting",
    "Copywriter",
    "Copy Writer",
    "Video Editor",
    "Video Editing",
    "Data Entry",
    "Content Writer",
    "Content Writing",
    "Technical Writer",  # Often basic documentation
    "Customer Support",
    "Customer Service",
    "Call Center",
    "Telecaller",
    "Sales Executive",  # Basic sales roles
    "Business Development Executive",  # Often basic sales
    "HR Executive",  # Basic HR
    "Recruiter",
    "Talent Acquisition",  # Unless specified as technical
    "Graphic Designer",  # Unless product designer
    "Marketing Executive",  # Basic marketing
    "Social Media Manager",
    "SEO Executive",
    "Digital Marketing Executive",
]

# India locations to target
INDIA_LOCATIONS = [
    "Bangalore",
    "Bengaluru",
    "Mumbai",
    "Pune",
    "Hyderabad",
    "Chennai",
    "Gurugram",
    "Gurgaon",
    "New Delhi",
    "Delhi",
    "Noida",
    "Kolkata",
    "Ahmedabad",
    "Remote",  # India remote
]


# ============================================================================
# JOB FILTERING UTILITIES
# ============================================================================

def is_job_posted_within_24h(posted_date: Optional[str]) -> bool:
    """
    Check if job was posted within the last 24 hours.
    CRITICAL: This is the core filter for the fresh jobs dashboard.

    Args:
        posted_date: Date string from LinkedIn (e.g., "3 hours ago", "1 day ago")

    Returns:
        True if posted within 24 hours
    """
    if not posted_date:
        return False

    posted_lower = posted_date.lower().strip()

    try:
        # Match patterns like "3 hours ago", "1 day ago", "2 weeks ago"
        match = re.search(r'(\d+)\s*(minute|hour|day|week|month)', posted_lower)

        if not match:
            return False

        value = int(match.group(1))
        unit = match.group(2)

        # Convert to hours
        hours_ago = 0
        if unit == 'minute':
            hours_ago = value / 60
        elif unit == 'hour':
            hours_ago = value
        elif unit == 'day':
            # "1 day ago" could mean 24-48 hours
            # "2 days ago" is definitely > 24 hours
            if value >= 2:
                return False
            # "1 day ago" - check if it's actually < 24 hours
            hours_ago = value * 24
        elif unit == 'week':
            hours_ago = value * 7 * 24
        elif unit == 'month':
            hours_ago = value * 30 * 24

        return hours_ago <= 24

    except Exception:
        return False


def should_exclude_job(job_title: str, job_description: str = "") -> bool:
    """
    Check if job should be excluded based on title/description.

    Args:
        job_title: Job title
        job_description: Job description

    Returns:
        True if job should be excluded
    """
    title_lower = job_title.lower() if job_title else ""
    desc_lower = job_description.lower() if job_description else ""

    for exclude_term in EXCLUDE_KEYWORDS:
        if exclude_term.lower() in title_lower:
            return True
        if exclude_term.lower() in desc_lower:
            # Only exclude if it appears prominently in description
            # (not just mentioned in passing)
            if desc_lower.count(exclude_term.lower()) > 2:
                return True

    return False


def is_core_role(job_title: str) -> bool:
    """
    Check if job title matches core technical/business roles.

    Args:
        job_title: Job title to check

    Returns:
        True if it's a core role
    """
    title_lower = job_title.lower() if job_title else ""

    # Check for target keywords
    for target in TARGET_KEYWORDS:
        if target.lower() in title_lower:
            return True

    # Additional patterns for core roles
    core_patterns = [
        r'\bsde\b',  # SDE as whole word
        r'\bpm\b',   # PM as whole word (but be careful)
        r'\bapm\b',
        r'\btpm\b',
        r'\bsre\b',
        r'\bml\b.*engineer',
        r'engineer\b',
        r'\bdeveloper\b',
        r'\barchitect\b',
        r'\bscientist\b',
        r'\banalyst\b',
        r'\bconsultant\b',
        r'\bmanager\b',
        r'\blead\b',
        r'\bhead\b',
        r'\bdirector\b',
        r'\bvp\b',
        r'\bchief\b',
    ]

    for pattern in core_patterns:
        if re.search(pattern, title_lower):
            # Double check it's not an excluded role
            if not should_exclude_job(job_title):
                return True

    return False


# ============================================================================
# MAIN SCRAPER CLASS
# ============================================================================

class IndiaJobsScraper:
    """
    Specialized scraper for India core technical/business jobs - 24 HOUR FRESH JOBS ONLY.
    Designed to run every 3-4 hours to catch jobs as soon as they're posted.
    """

    def __init__(
        self,
        session_file: str = "linkedin_session.json",
        notion_api_key: Optional[str] = None,
        notion_database_id: Optional[str] = None,
        headless: bool = True
    ):
        """
        Initialize the India jobs scraper.

        Args:
            session_file: Path to LinkedIn session file
            notion_api_key: Notion integration API key
            notion_database_id: Notion database ID
            headless: Run browser in headless mode
        """
        self.session_file = session_file
        self.headless = headless

        # Initialize Notion integration
        self.notion = NotionIntegration(
            api_key=notion_api_key,
            database_id=notion_database_id
        ) if notion_api_key and notion_database_id else None

        # Callbacks for progress
        self.callback = ConsoleCallback()

        # Track statistics
        self.stats = {
            "jobs_found": 0,
            "jobs_scraped": 0,
            "jobs_24h": 0,
            "jobs_core_role": 0,
            "jobs_excluded": 0,
            "jobs_added": 0,
            "duplicates_skipped": 0,
            "errors": 0
        }

    async def scrape_keyword(
        self,
        browser,
        keyword: str,
        location: str = "India",
        limit: int = 25,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape jobs for a specific keyword.

        Args:
            browser: Browser manager instance
            keyword: Job keyword to search
            location: Location to search
            limit: Max jobs to scrape
            skip_duplicates: Skip jobs already in Notion

        Returns:
            Dictionary with scraping results
        """
        results = {
            "keyword": keyword,
            "location": location,
            "jobs_found": 0,
            "jobs_scraped": 0,
            "jobs_24h": 0,
            "jobs_added": 0,
            "duplicates_skipped": 0,
            "excluded": 0,
            "errors": []
        }

        search_scraper = JobSearchScraper(browser.page, callback=self.callback)
        job_scraper = JobScraper(browser.page, callback=self.callback)

        try:
            # Search for jobs
            search_query = f"{keyword}"
            logger.info(f"🔍 Searching: {keyword} in {location}")

            job_urls = await search_scraper.search(
                keywords=search_query,
                location=location,
                limit=limit
            )

            results["jobs_found"] = len(job_urls)
            self.stats["jobs_found"] += len(job_urls)

            if not job_urls:
                return results

            # Scrape each job
            for job_url in job_urls:
                # Check for duplicates
                if skip_duplicates and self.notion and self.notion.check_duplicate(job_url):
                    results["duplicates_skipped"] += 1
                    self.stats["duplicates_skipped"] += 1
                    continue

                # Scrape job details
                try:
                    job = await job_scraper.scrape(job_url)
                    results["jobs_scraped"] += 1
                    self.stats["jobs_scraped"] += 1

                    # Check if posted within 24 hours (CRITICAL FILTER)
                    if not is_job_posted_within_24h(job.posted_date):
                        results["excluded"] += 1
                        self.stats["jobs_excluded"] += 1
                        logger.debug(f"  ⏰ Excluded (older than 24h): {job.job_title}")
                        continue

                    results["jobs_24h"] += 1
                    self.stats["jobs_24h"] += 1

                    # Check if it's a core role (not excluded)
                    if should_exclude_job(job.job_title, job.job_description):
                        results["excluded"] += 1
                        self.stats["jobs_excluded"] += 1
                        logger.debug(f"  ❌ Excluded (non-core role): {job.job_title}")
                        continue

                    if not is_core_role(job.job_title):
                        results["excluded"] += 1
                        self.stats["jobs_excluded"] += 1
                        logger.debug(f"  ❌ Excluded (not core role): {job.job_title}")
                        continue

                    results["jobs_core_role"] = results.get("jobs_core_role", 0) + 1
                    self.stats["jobs_core_role"] += 1

                    # Prepare job data for Notion
                    job_data = {
                        "company": job.company or "Unknown",
                        "role": job.job_title or "Unknown",
                        "date_added": datetime.now().strftime("%Y-%m-%d"),
                        "location": job.location or location,
                        "url": job_url
                    }

                    # Add to Notion
                    if self.notion:
                        if self.notion.add_job(job_data):
                            results["jobs_added"] += 1
                            self.stats["jobs_added"] += 1
                            print(f"  ✓ {job.job_title} at {job.company} ({job.location})")
                        else:
                            results["errors"].append(f"Failed to add {job_url}")
                    else:
                        # Just log if no Notion integration
                        print(f"  ✓ {job.job_title} at {job.company} ({job.location}) - [Notion not configured]")

                except ScrapingError as e:
                    results["errors"].append(f"Scraping error: {e}")
                    self.stats["errors"] += 1
                    continue
                except AuthenticationError as e:
                    results["errors"].append(f"Auth error: {e}")
                    break

                # Small delay to avoid rate limiting
                await asyncio.sleep(1)

        except Exception as e:
            results["errors"].append(f"Search error: {e}")

        return results

    async def run(
        self,
        keywords: Optional[List[str]] = None,
        location: str = "India",
        limit_per_keyword: int = 10,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Run the complete scraping workflow.

        Args:
            keywords: List of keywords (default: TARGET_KEYWORDS)
            location: Location to search
            limit_per_keyword: Max jobs per keyword
            skip_duplicates: Skip jobs already in Notion

        Returns:
            Dictionary with workflow results
        """
        results = {
            "success": False,
            "keywords_searched": 0,
            "total_jobs_found": 0,
            "total_jobs_scraped": 0,
            "total_jobs_24h": 0,
            "total_jobs_core": 0,
            "total_jobs_added": 0,
            "total_duplicates_skipped": 0,
            "total_excluded": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }

        keywords = keywords or TARGET_KEYWORDS

        print("\n" + "="*70)
        print("⚡ FRESH JOBS DASHBOARD - India (24 HOURS ONLY)")
        print("="*70)
        print(f"📍 Location: {location}")
        print(f"📍 Keywords: {len(keywords)} core technical/business roles")
        print(f"📍 Limit per keyword: {limit_per_keyword} jobs")
        print(f"📍 Time Filter: PAST 24 HOURS ONLY ⚡")
        print(f"📍 Excluded: Accountant, Copywriter, Video Editor, etc.")
        print(f"💡 Tip: Run every 3-4 hours for best results")
        print("="*70 + "\n")

        # Connect to Notion
        if self.notion:
            print("📊 Connecting to Notion...")
            if not self.notion.connect():
                error_msg = "Failed to connect to Notion. Check credentials."
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                print("\n💡 Make sure you've set up Notion integration correctly.")
                print("   See NOTION_SETUP.md for instructions.")
                return results
            print("✓ Connected to Notion\n")
        else:
            print("⚠️  Notion not configured - will scrape but not store jobs\n")

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

            # Scrape each keyword
            for i, keyword in enumerate(keywords, 1):
                print(f"\n{'='*70}")
                print(f"📝 Keyword {i}/{len(keywords)}: {keyword}")
                print(f"{'='*70}")

                keyword_results = await self.scrape_keyword(
                    browser=browser,
                    keyword=keyword,
                    location=location,
                    limit=limit_per_keyword,
                    skip_duplicates=skip_duplicates
                )

                results["keywords_searched"] += 1
                results["total_jobs_found"] += keyword_results["jobs_found"]
                results["total_jobs_scraped"] += keyword_results["jobs_scraped"]
                results["total_jobs_24h"] += keyword_results["jobs_24h"]
                results["total_jobs_core"] += keyword_results.get("jobs_core_role", 0)
                results["total_jobs_added"] += keyword_results["jobs_added"]
                results["total_duplicates_skipped"] += keyword_results["duplicates_skipped"]
                results["total_excluded"] += keyword_results["excluded"]
                results["errors"].extend(keyword_results["errors"])

                print(f"\n📊 Keyword Summary: {keyword}")
                print(f"   Found: {keyword_results['jobs_found']}")
                print(f"   Scraped: {keyword_results['jobs_scraped']}")
                print(f"   24h Jobs: {keyword_results['jobs_24h']}")
                print(f"   Added: {keyword_results['jobs_added']}")
                print(f"   Skipped: {keyword_results['duplicates_skipped']}")
                print(f"   Excluded: {keyword_results['excluded']}")

                # Delay between keywords
                if i < len(keywords):
                    print(f"\n⏳ Waiting 3 seconds before next keyword...")
                    await asyncio.sleep(3)

        # Print summary
        results["success"] = results["total_jobs_added"] > 0 or (not self.notion and results["total_jobs_24h"] > 0)
        self._print_summary(results)

        return results

    def _print_summary(self, results: Dict[str, Any]):
        """Print workflow summary."""
        print("\n" + "="*70)
        print("📊 WORKFLOW SUMMARY")
        print("="*70)
        print(f"✅ Success: {results['success']}")
        print(f"📝 Keywords Searched: {results['keywords_searched']}")
        print(f"🔍 Total Jobs Found: {results['total_jobs_found']}")
        print(f"📄 Total Jobs Scraped: {results['total_jobs_scraped']}")
        print(f"⚡ FRESH JOBS (24h): {results['total_jobs_24h']}")
        print(f"🎯 Core Technical/Business Roles: {results['total_jobs_core']}")
        print(f"➕ Jobs Added to Notion: {results['total_jobs_added']}")
        print(f"⚠️  Duplicates Skipped: {results['total_duplicates_skipped']}")
        print(f"❌ Excluded (non-core/old): {results['total_excluded']}")
        print("="*70)
        print(f"⏰ Completed at: {results['timestamp']}")
        print(f"💡 Next run: In 3-4 hours for more fresh jobs")
        print("="*70 + "\n")

        if results["errors"]:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results["errors"][:5]:
                print(f"   - {error}")
            if len(results["errors"]) > 5:
                print(f"   ... and {len(results['errors']) - 5} more")

        print("="*70)
        print(f"⏰ Completed at: {results['timestamp']}")
        print("="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="⚡ FRESH JOBS DASHBOARD - Scrape India jobs posted in past 24 hours",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape_india_jobs_notion.py
  python scrape_india_jobs_notion.py --limit 50
  python scrape_india_jobs_notion.py --headless False
  python scrape_india_jobs_notion.py --keywords "SDE" "Product Manager"
  python scrape_india_jobs_notion.py --location Bangalore

💡 BEST PRACTICES:
  - Run every 3-4 hours for freshest jobs (9 AM, 12 PM, 3 PM, 6 PM)
  - Higher limits catch more jobs but take longer
  - Use --headless False to debug issues
        """
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum jobs to scrape per keyword (default: 50)"
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
        "--no-dedup",
        action="store_true",
        help="Disable duplicate checking"
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        help="Specific keywords to search (default: all core roles)"
    )
    parser.add_argument(
        "--location",
        default="India",
        help="Location to search (default: India)"
    )

    args = parser.parse_args()

    # Load environment variables
    from dotenv import load_dotenv
    import os

    load_dotenv()

    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")

    # Create and run workflow
    workflow = IndiaJobsScraper(
        session_file=args.session_file,
        notion_api_key=notion_api_key,
        notion_database_id=notion_database_id,
        headless=args.headless
    )

    results = await workflow.run(
        keywords=args.keywords,
        location=args.location,
        limit_per_keyword=args.limit,
        skip_duplicates=not args.no_dedup
    )

    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
