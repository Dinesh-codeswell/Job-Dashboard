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
import random
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

# Keywords for consulting jobs (pure consultant roles)
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
    "Data Consultant",
    "Product Consultant",
    "AI Consultant",
    "Analytics Consultant",
    "Risk Consultant",
    "Senior Consultant",
    "Principal Consultant",
    "Lead Consultant",
    "Consulting Analyst",
]

# Internship keywords for consulting roles (pure consultant internships)
INTERNSHIP_KEYWORDS = [
    "Consulting Intern",
    "Business Analyst Intern",
    "Management Consulting Intern",
    "Strategy Intern",
    "Technology Consulting Intern",
    "Digital Consulting Intern",
    "SAP Intern",
    "Oracle Intern",
    "Cloud Consultant Intern",
    "Data Consultant Intern",
    "Product Consultant Intern",
    "AI Consultant Intern",
    "Analytics Intern",
    "Financial Consulting Intern",
    "Risk Consulting Intern",
    "IT Consulting Intern",
    "Summer Analyst",
    "Winter Intern Consulting",
    "Intern Consultant",
    "Business Consulting Intern",
]

# Roles that are NEVER consulting roles (hard blocklist)
BLOCKED_TITLE_PATTERNS = [
    "founder's office",
    "founder office",
    "chief of staff",
    "executive assistant",
    "personal assistant",
    "receptionist",
    "data entry",
    "back office",
    "research",
    "promotions",
    "business development",
    "sales",
    "marketing",
    "producer",
    "fraud detection",
    "test analyst",
    "tester",
    "quality assurance",
    "fresher",
    "presales",
    "pre-sales",
    "techno-functional",
    "implementation",
    "migration",
    "functional consultant",
    "solution advisor",
    "associate lead consultant",
    "domain consultant",
    "package consultant",
]

# Roles that require "consultant/consulting" explicitly in title
# These roles need actual consulting keyword, not just tech skills
REQUIRES_CONSULTANT_KEYWORD = [
    "analyst",
    "associate",
    "manager",
    "director",
    "architect",
    "engineer",
    "developer",
    "administrator",
    "admin",
    "specialist",
    "coordinator",
    "lead",
    "head",
    "principal",
    "senior",
    "junior",
    "staff",
    "officer",
    "executive",
    "founder",
    "sap",
    "oracle",
    "erp",
    "crm",
    "functional",
    "technical",
    "techno",
    "implementation",
    "migration",
    "package",
    "domain",
]

# Valid consulting-related keywords that can stand alone
# NOTE: "intern" removed - internships handled via INTERNSHIP_KEYWORDS check only
VALID_CONSULTING_TERMS = [
    "consultant",
    "consulting",
    "advisory",
    "advisor",
    "strategy",
    "transformation",
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
            "filtered_out": 0,
            "errors": 0
        }
        
        # Sheets manager
        self.sheets_manager = None
    
    def clean_job_description(self, description: str) -> str:
        """
        Clean job description to remove ONLY the topmost heading artifact.

        Removes:
        - ONLY the very first heading if it's "About the job", "Job Description", etc.
        - Preserves ALL subheadings within the JD (About Us, Responsibilities, etc.)
        - Cleans excessive whitespace
        """
        if not description:
            return ""

        # Topmost headings to remove (ONLY at the very start)
        top_headings_to_remove = [
            "about the job",
            "job description",
            "company description",
            "about us",
            "about our company",
            "about the role",
            "role description",
            "position summary",
            "job summary",
            "overview",
            "the role",
            "the opportunity",
        ]

        desc = description

        # ONLY remove the first heading if it matches
        lines = desc.split('\n')
        cleaned_lines = []
        first_heading_removed = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # ONLY check for heading at the very beginning (first few non-empty lines)
            if not first_heading_removed and stripped:
                is_top_heading = any(
                    stripped.lower() == heading or
                    stripped.lower().startswith(heading + ':') or
                    stripped.lower().startswith('**' + heading + '**')
                    for heading in top_headings_to_remove
                )

                if is_top_heading:
                    # Skip this heading and the empty line after it
                    first_heading_removed = True
                    continue

            cleaned_lines.append(line)

        desc = '\n'.join(cleaned_lines)

        # Clean up excessive whitespace (max 2 consecutive newlines)
        desc = desc.strip()
        desc = desc.replace('\n\n\n', '\n\n')

        return desc

    def _normalize_linkedin_job(self, job, city: str) -> Dict[str, Any]:
        """Normalize LinkedIn job data to unified format with pixel-perfect description."""
        description = job.job_description or ""
        
        # Description is already formatted by the new extractor in job.py
        # Just clean up any remaining artifacts
        if description:
            description = description.replace("… more", "").replace("... more", "")
            description = description.replace("Show less", "").replace("Show more", "")
            # Truncate if too long
            if len(description) > 45000:
                description = description[:45000]

        return {
            "job_title": (job.job_title or "").strip(),
            "company": job.company or "",
            "company_logo": job.company_logo or "",
            "employment_type": (job.employment_type or "").strip(),
            "location": (job.location or city).strip(),
            "posted_date": job.posted_date or "",
            "job_url": job.linkedin_url,
            "job_description": description,
            "search_city": city,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "platform": "linkedin"
        }

    def is_valid_consulting_job(self, job_title: str, company: str = "") -> tuple[bool, str]:
        """
        Validate if a job title is actually a consulting role.

        Returns:
            (is_valid: bool, reason: str)
        """
        if not job_title or job_title.strip() in ["", "Post a job", "View job"]:
            return False, "Empty or invalid job title"

        title_lower = job_title.lower().strip()

        # 1. Check blocked patterns (hard reject)
        for blocked in BLOCKED_TITLE_PATTERNS:
            if blocked in title_lower:
                return False, f"Blocked role: '{blocked}'"

        # 2. Check if title has any consulting-related keyword
        has_consulting_term = any(term in title_lower for term in VALID_CONSULTING_TERMS)

        # 3. Special handling for internships - must match INTERNSHIP_KEYWORDS AND have consulting term
        is_internship_role = any(kw.lower() in title_lower for kw in INTERNSHIP_KEYWORDS)
        
        if is_internship_role:
            if has_consulting_term:
                return True, "Valid consulting internship"
            else:
                return False, "Internship without consulting keyword"

        # 4. For non-internship roles that could be non-consulting, require explicit consulting keyword
        for role_keyword in REQUIRES_CONSULTANT_KEYWORD:
            if role_keyword in title_lower:
                # This role type needs "consultant/consulting" explicitly
                if not has_consulting_term:
                    return False, f"Role '{role_keyword}' without consulting keyword"
                break

        # 5. Reject if no consulting term found at all
        if not has_consulting_term:
            return False, "No consulting-related terms in title"

        return True, "Valid consulting role"
    
    def normalize_employment_type(self, raw_type: str) -> str:
        """
        Normalize employment type from Indeed/Naukri to match LinkedIn format.
        Handles lowercase, NaN, and various formats.
        """
        if not raw_type or str(raw_type).lower() in ['nan', 'none', 'null', '']:
            return 'Full Time'  # Default for missing/NaN values
        
        raw_lower = str(raw_type).lower().strip()
        
        # Map Indeed/Naukri formats to standard format
        type_mapping = {
            'fulltime': 'Full Time',
            'full-time': 'Full Time',
            'full time': 'Full Time',
            'parttime': 'Part Time',
            'part-time': 'Part Time',
            'part time': 'Part Time',
            'contract': 'Contract',
            'contractor': 'Contract',
            'temporary': 'Contract',
            'internship': 'Internship',
            'intern': 'Internship',
            'summer analyst': 'Internship',
            'summer intern': 'Internship',
            'remote': 'Remote',
            'work from home': 'Remote',
        }
        
        # Check for exact match first
        if raw_lower in type_mapping:
            return type_mapping[raw_lower]
        
        # Check for partial matches
        if 'full' in raw_lower:
            return 'Full Time'
        if 'part' in raw_lower:
            return 'Part Time'
        if 'contract' in raw_lower:
            return 'Contract'
        if 'intern' in raw_lower or 'summer analyst' in raw_lower:
            return 'Internship'
        if 'remote' in raw_lower or 'work from home' in raw_lower:
            return 'Remote'
        
        # Return original with proper capitalization if no match
        return raw_lower.title()

    def _normalize_indeed_naukri_job(self, row: Dict, platform: str) -> Dict[str, Any]:
        """Normalize Indeed/Naukri job data from DataFrame to unified format with pixel-perfect description."""
        # Import the extractor
        from job_description_extractor import extract_indeed_description, extract_naukri_description, extract_from_text
        
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

        # Normalize employment type to match LinkedIn format
        raw_type = job_data.get('employment_type', '')
        job_data['employment_type'] = self.normalize_employment_type(raw_type)

        # Extract pixel-perfect description
        raw_desc = job_data.get('job_description', '')
        if raw_desc:
            try:
                # Try platform-specific extraction first
                if platform == 'indeed':
                    formatted_desc = extract_indeed_description(raw_desc)
                elif platform == 'naukri':
                    formatted_desc = extract_naukri_description(raw_desc)
                else:
                    formatted_desc = extract_from_text(raw_desc)
                
                # Fallback to plain text extraction if platform-specific fails
                if not formatted_desc:
                    formatted_desc = extract_from_text(raw_desc)
                
                # Use formatted description if available, otherwise use raw
                if formatted_desc:
                    job_data['job_description'] = formatted_desc[:45000] if len(formatted_desc) > 45000 else formatted_desc
                else:
                    # Last resort: clean the raw description
                    desc = self.clean_job_description(raw_desc)
                    job_data['job_description'] = desc[:45000] if len(desc) > 45000 else desc
            except Exception as e:
                logger.debug(f"Description extraction error: {e}")
                # Fallback to basic cleaning
                desc = self.clean_job_description(raw_desc)
                job_data['job_description'] = desc[:45000] if len(desc) > 45000 else desc

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
                            
                            # Validate job title before processing
                            job_title = job.job_title or ""
                            is_valid, reason = self.is_valid_consulting_job(job_title, job.company or "")
                            
                            if not is_valid:
                                self.stats["filtered_out"] += 1
                                logger.debug(f"  ✗ Filtered: {job_title} - {reason}")
                                continue
                            
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
                        job_title = row.get('title', '')
                        
                        # Validate job title before processing
                        is_valid, reason = self.is_valid_consulting_job(job_title, str(row.get('company', '')))
                        
                        if not is_valid:
                            self.stats["filtered_out"] += 1
                            logger.debug(f"  ✗ Filtered ({platform}): {job_title} - {reason}")
                            continue
                        
                        job_data = self._normalize_indeed_naukri_job(row, platform)

                        if self.sheets_manager.upload_job(platform, job_data):
                            uploaded += 1
                            if platform == 'indeed':
                                self.stats["indeed_jobs"] += 1
                            else:
                                self.stats["naukri_jobs"] += 1

                            logger.info(f"  ✓ {platform.capitalize()}: {job_title} at {row.get('company')}")

                except Exception as e:
                    self.stats["errors"] += 1
                    logger.debug(f"API scraping error: {e}")

                time.sleep(1)  # Use sync sleep for non-async function

            time.sleep(2)  # Use sync sleep for non-async function

        return uploaded
    
    def _generate_task_pool(
        self,
        platforms: List[str],
        cities: List[str],
        keywords: List[str],
        limit_per_keyword: int
    ) -> List[Dict[str, Any]]:
        """
        Generate a randomized task pool with all combinations of platform, city, and keyword.
        
        This eliminates bias by shuffling all possible combinations and executing them
        in randomized order instead of sequential platform → city → keyword order.
        """
        tasks = []
        
        for platform in platforms:
            for city in cities:
                for keyword in keywords:
                    tasks.append({
                        'platform': platform,
                        'city': city,
                        'keyword': keyword,
                        'limit': limit_per_keyword,
                        'attempt': 0
                    })
        
        # Shuffle to remove all bias
        random.shuffle(tasks)
        
        logger.info(f"📋 Generated {len(tasks)} tasks with randomized order")
        logger.info(f"🎯 Platforms: {len(platforms)} | Cities: {len(cities)} | Keywords: {len(keywords)}")
        
        return tasks

    async def _execute_linkedin_task(
        self,
        browser,
        task: Dict[str, Any]
    ) -> int:
        """Execute a single LinkedIn scraping task."""
        uploaded = 0
        
        try:
            search_scraper = OptimizedJobSearchScraper(browser.page, callback=ConsoleCallback())
            job_scraper = JobScraper(browser.page, callback=ConsoleCallback())
            
            logger.info(f"🔍 LinkedIn: '{task['keyword']}' in {task['city']}")
            
            job_urls = await search_scraper.search(
                keywords=task['keyword'],
                location=task['city'],
                limit=task['limit'],
                days_ago=self.max_days
            )
            
            for job_url in job_urls:
                if self.sheets_manager.is_duplicate(job_url):
                    self.stats["duplicates_skipped"] += 1
                    continue
                
                try:
                    job = await job_scraper.scrape(job_url)
                    
                    # Validate job title before processing
                    job_title = job.job_title or ""
                    is_valid, reason = self.is_valid_consulting_job(job_title, job.company or "")
                    
                    if not is_valid:
                        self.stats["filtered_out"] += 1
                        logger.debug(f"  ✗ Filtered: {job_title} - {reason}")
                        continue
                    
                    job_data = self._normalize_linkedin_job(job, task['city'])

                    if self.sheets_manager.upload_job("linkedin", job_data):
                        uploaded += 1
                        self.stats["linkedin_jobs"] += 1
                        logger.info(f"  ✓ LinkedIn: {job.job_title} at {job.company}")
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.debug(f"LinkedIn job scrape error: {e}")
            
            logger.info(f"  ✅ LinkedIn: {uploaded} jobs from '{task['keyword']}' in {task['city']}")
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.debug(f"LinkedIn task error: {e}")
        
        return uploaded

    def _execute_api_task(
        self,
        task: Dict[str, Any]
    ) -> int:
        """Execute a single Indeed/Naukri scraping task."""
        import time
        
        uploaded = 0
        
        try:
            logger.info(f"🔍 API: '{task['keyword']}' in {task['city']}")
            
            # Scrape both Indeed and Naukri together
            df = scrape_multi_platform(
                sites=["indeed", "naukri"],
                search_term=task['keyword'],
                location=task['city'],
                results_wanted=task['limit'],
                hours_old=self.max_days * 24,
                verbose=0
            )
            
            if len(df) == 0:
                logger.info(f"  ⚠️  API: No jobs found for '{task['keyword']}' in {task['city']}")
                return 0
            
            for _, row in df.iterrows():
                job_url = row.get('job_url', '')
                if not job_url or self.sheets_manager.is_duplicate(job_url):
                    self.stats["duplicates_skipped"] += 1
                    continue

                platform = row.get('site', 'indeed')
                job_title = row.get('title', '')
                
                # Validate job title before processing
                is_valid, reason = self.is_valid_consulting_job(job_title, str(row.get('company', '')))
                
                if not is_valid:
                    self.stats["filtered_out"] += 1
                    logger.debug(f"  ✗ Filtered ({platform}): {job_title} - {reason}")
                    continue
                
                job_data = self._normalize_indeed_naukri_job(row, platform)

                if self.sheets_manager.upload_job(platform, job_data):
                    uploaded += 1
                    if platform == 'indeed':
                        self.stats["indeed_jobs"] += 1
                    else:
                        self.stats["naukri_jobs"] += 1
                    
                    logger.info(f"  ✓ {platform.capitalize()}: {job_title} at {row.get('company')}")
            
            logger.info(f"  ✅ API: {uploaded} jobs from '{task['keyword']}' in {task['city']}")
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.debug(f"API task error: {e}")
        
        time.sleep(1)  # Rate limiting
        return uploaded

    async def run_round_robin(
        self,
        cities: List[str] = None,
        include_internships: bool = True,
        limit_per_city: int = 10,
        tier_1_only: bool = False,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Run scraping with round-robin strategy for maximum diversity.
        
        This method:
        1. Generates all possible platform × city × keyword combinations
        2. Shuffles them to eliminate bias
        3. Executes in small batches to prevent rate limiting
        4. Uploads jobs immediately for real-time mixing
        """
        cities = cities or DEFAULT_CITIES
        if tier_1_only:
            cities = cities[:6]
        
        # Combine keywords
        keywords = CONSULTING_KEYWORDS.copy()
        if include_internships:
            keywords.extend(INTERNSHIP_KEYWORDS)
            print(f"📚 Including {len(INTERNSHIP_KEYWORDS)} internship keywords")

        print("\n" + "="*70)
        print("🚀 UNIFIED INDIA JOBS SCRAPER (ROUND-ROBIN MODE)")
        print("="*70)
        print(f"📍 Platforms: {', '.join(self.platforms)}")
        print(f"📍 Cities: {len(cities)}")
        print(f"📍 Keywords: {len(keywords)}")
        print(f"📍 Limit per search: {limit_per_city}")
        print(f"📍 Batch size: {batch_size} tasks")
        print(f"📍 Time Filter: PAST {self.max_days} DAYS")
        print(f"🎯 Strategy: Round-Robin (Maximum Diversity)")
        print("="*70 + "\n")
        
        # Initialize Google Sheets
        self.sheets_manager = UnifiedSheetsManager(
            sheet_id=self.sheet_id,
            credentials_file=self.credentials_file
        )
        
        if not self.sheets_manager.connect(self.platforms):
            return {"success": False, "error": "Google Sheets connection failed"}
        
        # Generate randomized task pool
        task_pool = self._generate_task_pool(
            platforms=self.platforms,
            cities=cities,
            keywords=keywords,
            limit_per_keyword=limit_per_city
        )
        
        total_uploaded = 0
        tasks_completed = 0
        
        # Execute tasks in batches
        for i in range(0, len(task_pool), batch_size):
            batch = task_pool[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(task_pool) + batch_size - 1) // batch_size
            
            print(f"\n{'='*70}")
            print(f"📦 BATCH {batch_num}/{total_batches} ({len(batch)} tasks)")
            print(f"{'='*70}")
            
            # Separate LinkedIn and API tasks
            linkedin_tasks = [t for t in batch if t['platform'] == 'linkedin']
            api_tasks = [t for t in batch if t['platform'] in ['indeed', 'naukri']]
            
            # Execute LinkedIn tasks (requires browser)
            if linkedin_tasks and "linkedin" in self.platforms:
                async with BrowserManager(headless=self.headless) as browser:
                    try:
                        await browser.load_session("linkedin_session.json")
                        print("✓ LinkedIn session loaded\n")
                        
                        for task in linkedin_tasks:
                            uploaded = await self._execute_linkedin_task(browser, task)
                            total_uploaded += uploaded
                            tasks_completed += 1
                            await asyncio.sleep(1)  # Brief pause between tasks
                            
                    except Exception as e:
                        logger.error(f"LinkedIn batch error: {e}")
                        tasks_completed += len(linkedin_tasks)
            
            # Execute API tasks (Indeed/Naukri)
            if api_tasks:
                api_platforms = [p for p in self.platforms if p in ["indeed", "naukri"]]
                if api_platforms:
                    for task in api_tasks:
                        uploaded = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda t=task: self._execute_api_task(t)
                        )
                        total_uploaded += uploaded
                        tasks_completed += 1
            
            # Progress update
            progress = (tasks_completed / len(task_pool)) * 100
            print(f"\n✅ Progress: {tasks_completed}/{len(task_pool)} tasks ({progress:.1f}%)")
            print(f"📊 Total jobs uploaded: {total_uploaded}")
            
            # Pause between batches to prevent rate limiting
            if i + batch_size < len(task_pool):
                pause_time = 5
                print(f"⏸️  Pausing {pause_time}s before next batch...")
                await asyncio.sleep(pause_time)
        
        # Update statistics
        self.stats["total_jobs"] = total_uploaded
        
        # Upload summary
        self.sheets_manager.upload_summary(self.stats)
        
        # Print summary
        self._print_summary()
        
        return {
            "success": total_uploaded > 0,
            "total_jobs": total_uploaded,
            "stats": self.stats,
            "strategy": "round_robin"
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
        print(f"🚫 Filtered Out:  {self.stats['filtered_out']}")
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

    # Create and run unified scraper with round-robin strategy
    scraper = UnifiedIndiaJobsScraper(
        platforms=args.platforms,
        max_days=args.max_days,
        headless=args.headless
    )

    # Use round-robin strategy for maximum diversity
    results = await scraper.run_round_robin(
        cities=args.cities,
        limit_per_city=args.limit_per_city,
        tier_1_only=args.tier_1_only,
        batch_size=10  # Process 10 tasks at a time
    )

    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
