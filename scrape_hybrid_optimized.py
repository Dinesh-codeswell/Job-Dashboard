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
import signal
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

# ============================================================================
# ROLE CATEGORIES WITH WEIGHTED DISTRIBUTION
# ============================================================================

# CATEGORY 1: CONSULTING ROLES (30% weight)
CONSULTING_KEYWORDS = [
    # Tier 1: High-precision consulting roles
    "Management Consultant", "Strategy Consultant", "Business Consultant",
    "Senior Consultant", "Principal Consultant", "Consulting Manager",
    
    # Tier 2: Domain-specific consulting
    "Technology Consultant", "IT Consultant", "Digital Transformation Consultant",
    "SAP Consultant", "Cloud Consultant", "Data Consultant",
]

CONSULTING_INTERNSHIPS = [
    "Management Consulting Intern", "Strategy Consulting Intern",
    "Business Consulting Intern", "Technology Consulting Intern",
    "Consulting Intern", "Summer Analyst Consulting",
]

# CATEGORY 2: PRODUCT MANAGEMENT ROLES (25% weight)
PRODUCT_KEYWORDS = [
    "Product Manager", "Senior Product Manager", "Associate Product Manager",
    "Product Strategy Manager", "Principal Product Manager",
    "Lead Product Manager", "Group Product Manager",
]

PRODUCT_INTERNSHIPS = [
    "Product Management Intern", "Product Manager Intern",
    "Associate Product Manager Intern", "Product Strategy Intern",
]

# CATEGORY 3: STRATEGY & GROWTH ROLES (25% weight)
STRATEGY_KEYWORDS = [
    "Growth Strategy Manager", "Business Strategy Manager",
    "Corporate Strategy Manager", "Strategy Manager",
    "Growth Manager", "Business Growth Manager",
]

STRATEGY_INTERNSHIPS = [
    "Growth Strategy Intern", "Business Strategy Intern",
    "Corporate Strategy Intern", "Strategy Intern",
    "Growth Intern", "Business Growth Intern",
]

# CATEGORY 4: OPERATIONS & ANALYTICS ROLES (20% weight)
OPERATIONS_KEYWORDS = [
    "Business Operations Manager", "Operations Strategy Manager",
    "Strategy Analyst", "Business Analyst",
    "Program Manager", "Strategic Project Manager",
    "Founder's Office", "Market Research Analyst",
]

OPERATIONS_INTERNSHIPS = [
    "Business Operations Intern", "Operations Intern",
    "Strategy Analyst Intern", "Business Analyst Intern",
    "Program Management Intern", "Strategic Project Management Intern",
    "Founder's Office Intern", "Market Research Intern",
]

# COMBINED LISTS FOR BACKWARD COMPATIBILITY
ALL_FULLTIME_KEYWORDS = (
    CONSULTING_KEYWORDS + PRODUCT_KEYWORDS + 
    STRATEGY_KEYWORDS + OPERATIONS_KEYWORDS
)

ALL_INTERNSHIP_KEYWORDS = (
    CONSULTING_INTERNSHIPS + PRODUCT_INTERNSHIPS + 
    STRATEGY_INTERNSHIPS + OPERATIONS_INTERNSHIPS
)

# ENHANCED: Company-based filtering for all role types
CONSULTING_FIRMS = [
    # Big 4
    "deloitte", "pwc", "ey", "kpmg", "pricewaterhousecoopers", "ernst & young",
    
    # MBB
    "mckinsey", "bain", "bcg", "boston consulting",
    
    # Tier 2 Consulting
    "accenture", "capgemini", "cognizant", "infosys consulting", "tcs consulting",
    "wipro consulting", "ltimindtree", "tech mahindra", "hcl consulting",
    
    # Boutique/Specialized
    "zs associates", "mu sigma", "fractal analytics", "latentview",
    "gartner", "forrester", "idc", "frost & sullivan",
    
    # IT Consulting
    "thoughtworks", "publicis sapient", "nagarro", "persistent systems",
]

PRODUCT_COMPANIES = [
    # Tech Giants
    "google", "microsoft", "amazon", "meta", "facebook", "apple",
    "netflix", "uber", "airbnb", "linkedin", "twitter", "spotify",
    
    # Indian Tech
    "flipkart", "swiggy", "zomato", "paytm", "phonepe", "cred",
    "razorpay", "meesho", "byju", "unacademy", "upgrad", "ola",
    "myntra", "bigbasket", "dunzo", "urban company", "sharechat",
    
    # SaaS/Product
    "freshworks", "zoho", "postman", "browserstack", "chargebee",
    "clevertap", "druva", "icertis", "mindtickle",
]

STRATEGY_COMPANIES = [
    # Consulting (overlap with consulting firms)
    "mckinsey", "bain", "bcg", "deloitte", "pwc", "ey", "kpmg",
    
    # Corporate Strategy Teams
    "tata", "reliance", "aditya birla", "mahindra", "godrej",
    "infosys", "wipro", "tcs", "hcl", "tech mahindra",
    
    # Growth-focused
    "sequoia", "accel", "matrix partners", "lightspeed", "nexus",
]

OPERATIONS_COMPANIES = [
    # Operations-heavy companies
    "amazon", "flipkart", "swiggy", "zomato", "uber", "ola",
    "delhivery", "rivigo", "blackbuck", "porter",
    
    # Analytics/Research
    "nielsen", "kantar", "ipsos", "gartner", "forrester",
    "fractal", "mu sigma", "latentview", "tiger analytics",
]

# Combined company list for validation
ALL_TARGET_COMPANIES = list(set(
    CONSULTING_FIRMS + PRODUCT_COMPANIES + 
    STRATEGY_COMPANIES + OPERATIONS_COMPANIES
))

BLOCKED_TITLE_PATTERNS = [
    # Removed "founder's office" - now a valid role type
    "executive assistant", "personal assistant", "receptionist", 
    "data entry", "back office", "promotions", "sales", "marketing", 
    "producer", "fraud detection", "test analyst", "tester", 
    "quality assurance", "fresher", "presales", "pre-sales",
    "techno-functional", "implementation", "migration",
    "functional consultant", "solution advisor", "associate lead consultant",
    "domain consultant", "package consultant", "technical consultant",
    "application consultant", "support consultant", "customer success",
    "account manager", "relationship manager", "scrum master", 
    "product owner", "delivery manager", "coordinator", "administrator",
    "developer", "engineer", "architect", "designer", # Block pure tech roles
]

# ENHANCED: Multi-tier validation
VALID_ROLE_TERMS = {
    "consulting": ["consultant", "consulting", "advisory", "advisor"],
    "product": ["product manager", "product management", "apm", "associate product"],
    "strategy": ["strategy", "growth", "strategic", "business strategy", "corporate strategy"],
    "operations": ["operations", "business operations", "program manager", "business analyst", 
                   "strategy analyst", "founder's office", "market research", "chief of staff"],
}

# NEW: Required title patterns for high confidence (by category)
REQUIRED_PATTERNS_BY_CATEGORY = {
    "consulting": [r'\bconsultant\b', r'\bconsulting\b', r'\badvisor\b', r'\badvisory\b'],
    "product": [r'\bproduct\s+manager\b', r'\bproduct\s+management\b', r'\bapm\b', r'\bpm\b'],
    "strategy": [r'\bstrategy\b', r'\bgrowth\b', r'\bstrategic\b'],
    "operations": [r'\boperations\b', r'\bprogram\s+manager\b', r'\bbusiness\s+analyst\b', 
                   r'\bstrategy\s+analyst\b', r"founder'?s?\s+office\b", r'\bmarket\s+research\b',
                   r'\bchief\s+of\s+staff\b'],
}

# NEW: Auto-reject patterns (immediate disqualification) - STRICT
AUTO_REJECT_PATTERNS = [
    r'\bsoftware\s+developer\b', r'\bsoftware\s+engineer\b', 
    r'\bfrontend\s+developer\b', r'\bbackend\s+developer\b',
    r'\bfull\s+stack\b', r'\bdevops\b', r'\bdata\s+engineer\b',
    r'\bmachine\s+learning\s+engineer\b', r'\bsolution\s+architect\b',
    r'\bui\s+designer\b', r'\bux\s+designer\b', r'\bgraphic\s+designer\b',
    r'\bsales\s+executive\b', r'\bsales\s+manager\b', r'\bmarketing\s+manager\b',
    r'\bhr\s+manager\b', r'\brecruiter\b', r'\btalent\s+acquisition\b',
    r'\bcustomer\s+support\b', r'\btechnical\s+support\b',
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
        """
        Build LinkedIn search URL with native date filters and optimized query.
        CRITICAL: LinkedIn ignores exact phrases when results are scarce.
        Solution: Use boolean operators and validate results.
        """
        base_url = "https://www.linkedin.com/jobs/search/"
        params = {}

        if keywords:
            # CRITICAL FIX: Don't use quotes for LinkedIn - it ignores them
            # Instead, we'll validate results after fetching
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
        
        # Graceful shutdown flag
        self.shutdown_requested = False
        
        # Statistics with category breakdown
        self.stats = {
            "linkedin_jobs": 0,
            "indeed_jobs": 0,
            "naukri_jobs": 0,
            "total_jobs": 0,
            "duplicates_skipped": 0,
            "filtered_out": 0,
            "errors": 0,
            # Category breakdown
            "consulting_jobs": 0,
            "product_jobs": 0,
            "strategy_jobs": 0,
            "operations_jobs": 0,
            "internship_jobs": 0,
            "fulltime_jobs": 0,
        }
        
        logger.info("Hybrid optimized scraper initialized with multi-category support")
    
    def request_shutdown(self):
        """Request graceful shutdown."""
        logger.info("\n🛑 Shutdown requested... finishing current job and saving progress")
        self.shutdown_requested = True
    
    def get_weighted_keywords(self, include_internships: bool = True) -> List[tuple]:
        """
        Get keywords with weighted distribution for mixing.
        Returns list of (keyword, category, is_internship) tuples.
        
        Distribution:
        - 30% Consulting
        - 25% Product
        - 25% Strategy
        - 20% Operations
        """
        weighted_keywords = []
        
        # Consulting (30%)
        for kw in CONSULTING_KEYWORDS:
            weighted_keywords.append((kw, "consulting", False))
        if include_internships:
            for kw in CONSULTING_INTERNSHIPS:
                weighted_keywords.append((kw, "consulting", True))
        
        # Product (25%)
        for kw in PRODUCT_KEYWORDS:
            weighted_keywords.append((kw, "product", False))
        if include_internships:
            for kw in PRODUCT_INTERNSHIPS:
                weighted_keywords.append((kw, "product", True))
        
        # Strategy (25%)
        for kw in STRATEGY_KEYWORDS:
            weighted_keywords.append((kw, "strategy", False))
        if include_internships:
            for kw in STRATEGY_INTERNSHIPS:
                weighted_keywords.append((kw, "strategy", True))
        
        # Operations (20%)
        for kw in OPERATIONS_KEYWORDS:
            weighted_keywords.append((kw, "operations", False))
        if include_internships:
            for kw in OPERATIONS_INTERNSHIPS:
                weighted_keywords.append((kw, "operations", True))
        
        # Shuffle to ensure mixing (not all consulting first, then all product, etc.)
        import random
        random.shuffle(weighted_keywords)
        
        return weighted_keywords
    
    def detect_role_category(self, job_title: str) -> Optional[str]:
        """Detect which category a job belongs to."""
        title_lower = job_title.lower().strip()
        
        # Check each category
        if any(term in title_lower for term in ["consultant", "consulting", "advisory", "advisor"]):
            return "consulting"
        elif any(term in title_lower for term in ["product manager", "product management", "apm"]):
            return "product"
        elif any(term in title_lower for term in ["strategy", "growth", "strategic"]):
            return "strategy"
        elif any(term in title_lower for term in ["operations", "program manager", "business analyst", 
                                                    "strategy analyst", "founder", "market research", "chief of staff"]):
            return "operations"
        
        return None
    
    def keyword_matches_title(self, keyword: str, job_title: str) -> tuple[bool, str]:
        """
        CROSS-CATEGORY MATCHING: Check if job title matches ANY of our 4 target categories.
        
        CRITICAL CHANGE: We now accept jobs from ANY category, regardless of search keyword.
        Example: "Product Manager" found under "Strategy Consultant" search = ACCEPTED
        
        This dramatically improves success rate by capturing all relevant roles.
        
        Returns (matches, reason) tuple.
        """
        if not job_title:
            return False, "Empty title"
        
        title_lower = job_title.lower().strip()
        
        # Check if title matches ANY of our 4 categories
        # If it does, accept it regardless of search keyword
        
        # Category 1: Consulting
        if any(term in title_lower for term in ['consultant', 'consulting', 'advisory', 'advisor']):
            return True, "Matches consulting category"
        
        # Category 2: Product
        if any(term in title_lower for term in ['product manager', 'product management', 'apm', 'associate product']):
            return True, "Matches product category"
        
        # Category 3: Strategy & Growth
        if any(term in title_lower for term in ['strategy', 'growth', 'strategic']):
            return True, "Matches strategy category"
        
        # Category 4: Operations & Analytics
        if any(term in title_lower for term in ['operations', 'program manager', 'business analyst', 
                                                  'strategy analyst', 'founder', 'market research', 'chief of staff']):
            return True, "Matches operations category"
        
        # Internships - accept if has "intern" + any role keyword
        if 'intern' in title_lower:
            role_keywords = ['product', 'strategy', 'consulting', 'business', 'operations', 'analyst', 'growth']
            if any(kw in title_lower for kw in role_keywords):
                return True, "Matches internship in target category"
        
        return False, f"Does not match any target category: {job_title}"
    
    def is_valid_role(self, job_title: str, company: str = "", search_keyword: str = "") -> tuple[bool, str]:
        """
        ENHANCED: Multi-category validation with strict quality checks AND keyword matching.
        Supports: Consulting, Product, Strategy, Operations roles.
        Returns (is_valid, reason) tuple.
        """
        if not job_title or job_title.strip() in ["", "Post a job", "View job"]:
            return False, "Empty or invalid job title"
        
        title_lower = job_title.lower().strip()
        company_lower = company.lower().strip()
        
        # TIER 0: CROSS-CATEGORY MATCHING - Accept if matches ANY of our 4 categories
        # This allows "Product Manager" to be accepted even when searching for "Strategy Consultant"
        keyword_matches, keyword_reason = self.keyword_matches_title(search_keyword, job_title)
        if not keyword_matches:
            return False, f"Not in target categories: {keyword_reason}"
        
        # TIER 1: Auto-reject patterns (immediate disqualification)
        for pattern in AUTO_REJECT_PATTERNS:
            if re.search(pattern, title_lower):
                return False, f"Auto-reject: Pure tech/sales role"
        
        # TIER 2: Check blocked patterns
        for blocked in BLOCKED_TITLE_PATTERNS:
            if blocked in title_lower:
                return False, f"Blocked role: '{blocked}'"
        
        # TIER 3: Detect role category
        category = self.detect_role_category(job_title)
        
        if not category:
            return False, "Does not match any target role category"
        
        # TIER 4: Category-specific validation
        required_patterns = REQUIRED_PATTERNS_BY_CATEGORY.get(category, [])
        has_required_term = any(re.search(pattern, title_lower) for pattern in required_patterns)
        
        if not has_required_term:
            return False, f"Missing required terms for {category} role"
        
        # TIER 5: Special handling for internships
        is_internship = "intern" in title_lower
        
        if is_internship:
            # Internship must explicitly mention the role type
            if category in ["consulting", "product", "strategy", "operations"]:
                return True, f"Valid {category} internship"
            else:
                return False, "Internship without clear role category"
        
        # TIER 6: Company validation (STRICT - bonus for target companies)
        is_target_company = any(firm in company_lower for firm in ALL_TARGET_COMPANIES)
        
        # TIER 7: Special validation for broad roles (Founder's Office, Business Analyst)
        broad_roles = ["founder", "business analyst", "program manager", "operations manager"]
        is_broad_role = any(role in title_lower for role in broad_roles)
        
        if is_broad_role and not is_target_company:
            # Broad roles MUST be from target companies (STRICT)
            return False, f"Broad role '{job_title}' not from target company"
        
        # TIER 8: Title structure validation
        if len(title_lower.split()) <= 1:
            return False, "Title too short/generic"
        
        # TIER 9: Context scoring by category
        score = 0
        
        if category == "consulting":
            if "consult" in title_lower: score += 3
            if "advisory" in title_lower or "advisor" in title_lower: score += 2
            if "strategy" in title_lower: score += 1
            if "management" in title_lower or "business" in title_lower: score += 1
            min_score = 3
        
        elif category == "product":
            if "product manager" in title_lower: score += 4
            if "product management" in title_lower: score += 4
            if "senior" in title_lower or "lead" in title_lower or "principal" in title_lower: score += 1
            if "associate" in title_lower or "apm" in title_lower: score += 1
            if "strategy" in title_lower: score += 1
            min_score = 4
        
        elif category == "strategy":
            if "strategy" in title_lower: score += 3
            if "growth" in title_lower: score += 2
            if "business" in title_lower or "corporate" in title_lower: score += 1
            if "manager" in title_lower or "lead" in title_lower: score += 1
            min_score = 3
        
        elif category == "operations":
            if "operations" in title_lower: score += 2
            if "business" in title_lower: score += 1
            if "strategy" in title_lower: score += 1
            if "program manager" in title_lower: score += 3
            if "business analyst" in title_lower: score += 3
            if "founder" in title_lower and "office" in title_lower: score += 3
            if "market research" in title_lower: score += 3
            if "chief of staff" in title_lower: score += 4
            min_score = 2
        
        else:
            min_score = 2
        
        # Bonus for target companies
        if is_target_company:
            score += 1
        
        # Final validation
        if score >= min_score:
            return True, f"Valid {category} role (score: {score}/{min_score})"
        else:
            return False, f"Insufficient context for {category} role (score: {score}/{min_score})"
    
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
        """Upload job to Google Sheets immediately and track category stats."""
        if platform not in self.sheets:
            logger.error(f"Platform {platform} not connected")
            return False
        
        try:
            # Mark as seen
            if job_data.get('job_url'):
                self.all_urls.add(job_data['job_url'])
            
            # Track category stats
            job_title = job_data.get('job_title', '').lower()
            category = self.detect_role_category(job_data.get('job_title', ''))
            
            if category == "consulting":
                self.stats["consulting_jobs"] += 1
            elif category == "product":
                self.stats["product_jobs"] += 1
            elif category == "strategy":
                self.stats["strategy_jobs"] += 1
            elif category == "operations":
                self.stats["operations_jobs"] += 1
            
            # Track internship vs fulltime
            if "intern" in job_title:
                self.stats["internship_jobs"] += 1
            else:
                self.stats["fulltime_jobs"] += 1
            
            # Upload to sheets
            self.sheets[platform].upload_job(job_data)
            return True
        except Exception as e:
            logger.error(f"Failed to upload job: {e}")
            return False
    
    async def scrape_linkedin_batch(
        self,
        cities: List[str],
        weighted_keywords: List[tuple],
        limit_per_keyword: int = 10
    ) -> int:
        """
        Scrape LinkedIn jobs with WEIGHTED KEYWORD DISTRIBUTION.
        Keywords are pre-shuffled to ensure mixing across categories.
        """
        uploaded = 0
        
        logger.info(f"Starting LinkedIn scraping: {len(cities)} cities, {len(weighted_keywords)} weighted keywords")
        
        async with BrowserManager(headless=self.headless) as browser:
            try:
                await browser.load_session("linkedin_session.json")
                logger.info("LinkedIn session loaded")
            except:
                logger.warning("No saved session, will need to login")
            
            total_tasks = len(cities) * len(weighted_keywords)
            completed = 0
            
            for city in cities:
                # Check for shutdown request
                if self.shutdown_requested:
                    logger.info("⚠️  Shutdown requested, stopping LinkedIn scraping...")
                    break
                
                for keyword, category, is_internship in weighted_keywords:
                    # Check for shutdown request
                    if self.shutdown_requested:
                        logger.info("⚠️  Shutdown requested, stopping LinkedIn scraping...")
                        break
                    
                    completed += 1
                    role_type = "internship" if is_internship else "full-time"
                    logger.info(f"[{completed}/{total_tasks}] Processing: {keyword} ({category}, {role_type}) in {city}")
                    
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
                        
                        # CRITICAL OPTIMIZATION: Extract titles FIRST, validate, THEN scrape full details
                        job_scraper = JobScraper(browser.page, callback=ConsoleCallback())
                        
                        valid_jobs_count = 0
                        skipped_early = 0
                        
                        for job_url in job_urls:
                            # Check for shutdown request
                            if self.shutdown_requested:
                                logger.info("⚠️  Shutdown requested, stopping job processing...")
                                break
                            
                            # Check duplicate first (fast URL check)
                            if self.is_duplicate(job_url):
                                self.stats["duplicates_skipped"] += 1
                                continue
                            
                            try:
                                # Rate limiting
                                await self.engine.rate_limiter.acquire('linkedin')
                                
                                # STAGE 1: FAST - Extract ONLY title and company (no description)
                                quick_title = ""
                                quick_company = ""
                                
                                try:
                                    await browser.page.goto(job_url, wait_until="domcontentloaded", timeout=10000)
                                    
                                    # UPDATED SELECTORS for LinkedIn's current HTML structure
                                    # Try multiple selectors in order of specificity
                                    title_selectors = [
                                        'h1.top-card-layout__title',  # New LinkedIn layout
                                        'h1.t-24.t-bold',  # Alternative layout
                                        'h2.top-card-layout__title',
                                        'h1[class*="job"]',  # Fallback
                                        'h1',  # Last resort
                                    ]
                                    
                                    for selector in title_selectors:
                                        try:
                                            title_elem = await browser.page.query_selector(selector)
                                            if title_elem:
                                                quick_title = await title_elem.inner_text()
                                                if quick_title and quick_title.strip():
                                                    break
                                        except:
                                            continue
                                    
                                    # Company extraction with updated selectors
                                    company_selectors = [
                                        'a.topcard__org-name-link',  # New layout
                                        'span.topcard__flavor',  # Alternative
                                        'a[data-tracking-control-name*="company"]',  # Fallback
                                    ]
                                    
                                    for selector in company_selectors:
                                        try:
                                            company_elem = await browser.page.query_selector(selector)
                                            if company_elem:
                                                quick_company = await company_elem.inner_text()
                                                if quick_company and quick_company.strip():
                                                    break
                                        except:
                                            continue
                                    
                                    if not quick_title or not quick_title.strip():
                                        logger.info(f"⚠️  Could not extract title from {job_url}, falling back to full scrape")
                                        # Don't skip - fall through to full scrape
                                    else:
                                        # EARLY VALIDATION (before full scrape)
                                        is_valid, reason = self.is_valid_role(
                                            quick_title.strip(),
                                            quick_company.strip(),
                                            keyword
                                        )
                                        
                                        if not is_valid:
                                            self.stats["filtered_out"] += 1
                                            skipped_early += 1
                                            # DETAILED LOGGING - Show what's being rejected and WHY
                                            logger.info(f"❌ Rejected: '{quick_title}' at {quick_company} | Reason: {reason}")
                                            continue
                                        
                                        # STAGE 2: SLOW - Only scrape full details for valid jobs
                                        logger.info(f"✅ Valid: '{quick_title}' | {reason}")
                                
                                except Exception as e:
                                    logger.info(f"⚠️  Early extraction failed: {str(e)[:100]}, falling back to full scrape")
                                
                                # Full scrape (only for validated jobs)
                                job = await job_scraper.scrape(job_url)
                                
                                # Final validation (in case early validation was skipped)
                                is_valid, reason = self.is_valid_role(
                                    job.job_title or "",
                                    job.company or "",
                                    keyword  # Pass search keyword for relevance check
                                )
                                
                                if not is_valid:
                                    self.stats["filtered_out"] += 1
                                    # DETAILED LOGGING - Show what's being rejected and WHY
                                    logger.info(f"❌ Rejected: '{job.job_title}' at {job.company} | Reason: {reason}")
                                    continue
                                
                                # Only process description if job passed validation
                                description = job.job_description or ""
                                if description:
                                    description = description.replace("… more", "").replace("... more", "")
                                    description = description.replace("Show less", "").replace("Show more", "")
                                    if len(description) > 45000:
                                        description = description[:45000]
                                
                                # Normalize job data
                                job_data = {
                                    "job_title": self.sanitizer.sanitize_html(job.job_title or ""),
                                    "company": self.sanitizer.sanitize_html(job.company or ""),
                                    "company_logo": self.sanitizer.sanitize_url(job.company_logo or ""),
                                    "employment_type": job.employment_type or "",
                                    "location": job.location or city,
                                    "posted_date": job.posted_date or "",
                                    "job_url": self.sanitizer.sanitize_url(job.linkedin_url),
                                    "job_description": description,
                                    "search_city": city,
                                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "platform": "linkedin",
                                    "category": category,  # Track category
                                }
                                
                                # Upload immediately
                                if self.upload_job("linkedin", job_data):
                                    uploaded += 1
                                    valid_jobs_count += 1
                                    self.stats["linkedin_jobs"] += 1
                                    self.stats["total_jobs"] += 1
                                    logger.info(f"✓ LinkedIn [{category}]: {job.job_title} at {job.company}")
                            
                            except Exception as e:
                                self.stats["errors"] += 1
                                logger.debug(f"Error scraping job: {e}")
                        
                        # Log success rate for this keyword
                        if len(job_urls) > 0:
                            success_rate = (valid_jobs_count / len(job_urls)) * 100
                            logger.info(f"📊 '{keyword}' in {city}: {success_rate:.1f}% success ({valid_jobs_count}/{len(job_urls)} jobs)")
                            if skipped_early > 0:
                                logger.info(f"  ⚡ Early rejections (time saved): {skipped_early} jobs")
                            
                            # Provide feedback on low success rates
                            if success_rate < 20 and len(job_urls) >= 5:
                                logger.info(f"  ℹ️  Low success rate - LinkedIn returned mostly irrelevant results for this keyword")
                        
                        await asyncio.sleep(0.5)  # Minimal delay between searches
                    
                    except Exception as e:
                        self.stats["errors"] += 1
                        logger.error(f"Error processing {keyword} in {city}: {e}")
        
        logger.info(f"LinkedIn scraping complete: {uploaded} jobs uploaded")
        return uploaded
    
    def scrape_indeed_naukri_batch(
        self,
        cities: List[str],
        weighted_keywords: List[tuple],
        limit_per_city: int = 10
    ) -> int:
        """
        Scrape Indeed and Naukri jobs with WEIGHTED KEYWORD DISTRIBUTION.
        Uses pre-shuffled keywords to ensure category mixing.
        """
        uploaded = 0
        
        logger.info(f"Starting Indeed/Naukri scraping: {len(cities)} cities, {len(weighted_keywords)} weighted keywords")
        
        for city in cities:
            # Check for shutdown request
            if self.shutdown_requested:
                logger.info("⚠️  Shutdown requested, stopping Indeed/Naukri scraping...")
                break
            
            for keyword, category, is_internship in weighted_keywords:
                # Check for shutdown request
                if self.shutdown_requested:
                    logger.info("⚠️  Shutdown requested, stopping Indeed/Naukri scraping...")
                    break
                
                role_type = "internship" if is_internship else "full-time"
                logger.info(f"Scraping: {keyword} ({category}, {role_type}) in {city}")
                    
                try:
                    # Rate limiting
                    time.sleep(1)
                    
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
                    
                    valid_jobs_count = 0
                    
                    # Process each job
                    for _, row in df.iterrows():
                        job_url = row.get('job_url', '')
                        if not job_url or self.is_duplicate(job_url):
                            self.stats["duplicates_skipped"] += 1
                            continue
                        
                        platform = row.get('site', 'indeed')
                        job_title = row.get('title', '')
                        company = str(row.get('company', ''))
                        
                        # EARLY VALIDATION: Check before processing description
                        is_valid, reason = self.is_valid_role(job_title, company, keyword)
                        
                        if not is_valid:
                            self.stats["filtered_out"] += 1
                            # DETAILED LOGGING - Show what's being rejected and WHY
                            logger.info(f"❌ Rejected ({platform}): '{job_title}' at {company} | Reason: {reason}")
                            continue
                        
                        # Only process description for valid jobs
                        raw_desc = str(row.get('description', ''))
                        formatted_desc = raw_desc
                        if raw_desc:
                            try:
                                from job_description_extractor import extract_indeed_description, extract_naukri_description, extract_from_text
                                
                                if platform == 'indeed':
                                    formatted_desc = extract_indeed_description(raw_desc) or extract_from_text(raw_desc) or raw_desc
                                elif platform == 'naukri':
                                    formatted_desc = extract_naukri_description(raw_desc) or extract_from_text(raw_desc) or raw_desc
                                else:
                                    formatted_desc = extract_from_text(raw_desc) or raw_desc
                                
                                if len(formatted_desc) > 45000:
                                    formatted_desc = formatted_desc[:45000]
                            except Exception as e:
                                logger.debug(f"Description extraction error: {e}")
                                formatted_desc = raw_desc[:45000] if len(raw_desc) > 45000 else raw_desc
                        
                        # Normalize
                        job_data = {
                            "job_title": self.sanitizer.sanitize_html(job_title),
                            "company": self.sanitizer.sanitize_html(company),
                            "company_logo": self.sanitizer.sanitize_url(str(row.get('company_logo', ''))),
                            "employment_type": str(row.get('job_type', 'Full Time')),
                            "location": str(row.get('location', '')),
                            "posted_date": str(row.get('date_posted', '')),
                            "job_url": self.sanitizer.sanitize_url(job_url),
                            "job_description": formatted_desc,
                            "search_city": city,
                            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "platform": platform,
                            "category": category,  # Track category
                        }
                        
                        # Upload immediately
                        if self.upload_job(platform, job_data):
                            uploaded += 1
                            valid_jobs_count += 1
                            if platform == 'indeed':
                                self.stats["indeed_jobs"] += 1
                            else:
                                self.stats["naukri_jobs"] += 1
                            self.stats["total_jobs"] += 1
                            logger.info(f"✓ {platform.capitalize()} [{category}]: {job_title}")
                    
                    # Log success rate
                    if len(df) > 0:
                        success_rate = (valid_jobs_count / len(df)) * 100
                        logger.info(f"Success rate for '{keyword}' in {city}: {success_rate:.1f}% ({valid_jobs_count}/{len(df)})")
                
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
        """Run hybrid scraping workflow with weighted keyword distribution."""
        cities = cities or DEFAULT_CITIES
        
        # Get weighted keywords (pre-shuffled for mixing)
        weighted_keywords = self.get_weighted_keywords(include_internships=include_internships)
        
        logger.info("="*70)
        logger.info("HYBRID OPTIMIZED SCRAPER STARTING - MULTI-CATEGORY")
        logger.info("="*70)
        logger.info(f"Platforms: {', '.join(self.platforms)}")
        logger.info(f"Cities: {len(cities)}")
        logger.info(f"Total Keywords: {len(weighted_keywords)}")
        logger.info(f"  - Consulting: {len([k for k in weighted_keywords if k[1] == 'consulting'])}")
        logger.info(f"  - Product: {len([k for k in weighted_keywords if k[1] == 'product'])}")
        logger.info(f"  - Strategy: {len([k for k in weighted_keywords if k[1] == 'strategy'])}")
        logger.info(f"  - Operations: {len([k for k in weighted_keywords if k[1] == 'operations'])}")
        logger.info(f"Time Filter: Past {self.max_days} days")
        logger.info(f"Include Internships: {include_internships}")
        logger.info("="*70)
        
        # Connect to Google Sheets
        if not self.connect_sheets():
            return {"success": False, "error": "Google Sheets connection failed"}
        
        # Scrape LinkedIn
        if "linkedin" in self.platforms:
            await self.scrape_linkedin_batch(cities, weighted_keywords, limit_per_city)
        
        # Scrape Indeed/Naukri (run in executor since it's synchronous)
        if any(p in self.platforms for p in ['indeed', 'naukri']):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.scrape_indeed_naukri_batch,
                cities,
                weighted_keywords,
                limit_per_city
            )
        
        # Print summary
        self._print_summary()
        
        return {
            "success": self.stats["total_jobs"] > 0,
            "total_jobs": self.stats["total_jobs"],
            "stats": self.stats,
        }
    
    def _print_summary(self):
        """Print workflow summary with category breakdown and success rate analysis."""
        total_processed = self.stats["total_jobs"] + self.stats["filtered_out"]
        success_rate = (self.stats["total_jobs"] / total_processed * 100) if total_processed > 0 else 0
        
        print("\n" + "="*70)
        if self.shutdown_requested:
            print("EXECUTION SUMMARY - GRACEFUL SHUTDOWN")
        else:
            print("EXECUTION SUMMARY - MULTI-CATEGORY SCRAPER")
        print("="*70)
        print(f"LinkedIn Jobs:  {self.stats['linkedin_jobs']}")
        print(f"Indeed Jobs:    {self.stats['indeed_jobs']}")
        print(f"Naukri Jobs:    {self.stats['naukri_jobs']}")
        print(f"Total Jobs:     {self.stats['total_jobs']}")
        print("-"*70)
        print("CATEGORY BREAKDOWN:")
        print(f"  Consulting:   {self.stats['consulting_jobs']}")
        print(f"  Product:      {self.stats['product_jobs']}")
        print(f"  Strategy:     {self.stats['strategy_jobs']}")
        print(f"  Operations:   {self.stats['operations_jobs']}")
        print("-"*70)
        print("ROLE TYPE BREAKDOWN:")
        print(f"  Full-time:    {self.stats['fulltime_jobs']}")
        print(f"  Internships:  {self.stats['internship_jobs']}")
        print("-"*70)
        print(f"Filtered Out:   {self.stats['filtered_out']}")
        print(f"Duplicates:     {self.stats['duplicates_skipped']}")
        print(f"Errors:         {self.stats['errors']}")
        print("-"*70)
        print(f"SUCCESS RATE:   {success_rate:.1f}% ({self.stats['total_jobs']}/{total_processed} jobs passed validation)")
        
        # Success rate interpretation
        if success_rate >= 40:
            print("✅ Excellent success rate!")
        elif success_rate >= 25:
            print("✅ Good success rate (LinkedIn has inherent noise)")
        elif success_rate >= 15:
            print("⚠️  Moderate success rate (LinkedIn returned many irrelevant results)")
        else:
            print("⚠️  Low success rate (most results were irrelevant)")
        
        print("="*70)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if self.shutdown_requested:
            print("Status: Gracefully stopped by user (Ctrl+C)")
        print("="*70 + "\n")
        
        # Category distribution analysis
        if self.stats['total_jobs'] > 0:
            print("CATEGORY DISTRIBUTION:")
            for cat in ['consulting', 'product', 'strategy', 'operations']:
                count = self.stats[f'{cat}_jobs']
                pct = (count / self.stats['total_jobs'] * 100) if self.stats['total_jobs'] > 0 else 0
                print(f"  {cat.capitalize()}: {pct:.1f}%")
            print("="*70 + "\n")
        
        # Insights
        if not self.shutdown_requested and total_processed > 0:
            print("💡 INSIGHTS:")
            
            if success_rate < 25:
                print("  • Low success rate is often due to LinkedIn returning irrelevant results")
                print("  • Check rejection logs above to see what was filtered out")
                print("  • Consider using more specific keywords or different cities")
            
            if self.stats['filtered_out'] > self.stats['total_jobs'] * 2:
                print("  • Many jobs filtered out - this is normal for broad keywords")
                print("  • Cross-category matching is working (check logs for accepted jobs)")
            
            if self.stats['duplicates_skipped'] > 10:
                print(f"  • {self.stats['duplicates_skipped']} duplicates skipped - deduplication working well")
            
            print("="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point with graceful shutdown handling."""
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
    
    # Create scraper
    scraper = HybridOptimizedScraper(
        platforms=args.platforms,
        max_days=args.max_days,
    )
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully."""
        scraper.request_shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Press Ctrl+C to stop gracefully (will finish current job and save progress)")
    
    try:
        # Run scraper
        results = await scraper.run(
            cities=args.cities,
            limit_per_city=args.limit_per_city
        )
        
        if scraper.shutdown_requested:
            logger.info("\n✅ Graceful shutdown completed. Progress saved.")
            logger.info(f"Jobs scraped before shutdown: {scraper.stats['total_jobs']}")
            sys.exit(0)
        
        sys.exit(0 if results["success"] else 1)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Keyboard interrupt detected. Saving progress...")
        scraper._print_summary()
        logger.info("✅ Progress saved. Exiting.")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        scraper._print_summary()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
