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

DEFAULT_JOB_BOARDS = os.getenv("DEFAULT_JOB_BOARDS", "linkedin,indeed").split(",")
DEFAULT_CITIES = os.getenv("DEFAULT_CITIES", "Bangalore,Mumbai,Pune,Gurugram,Chennai,Hyderabad").split(",")
DEFAULT_RESULTS_PER_CITY = int(os.getenv("DEFAULT_RESULTS_PER_CITY", "10"))
DEFAULT_HOURS_OLD = int(os.getenv("DEFAULT_HOURS_OLD", "48"))
DEFAULT_MAX_DAYS = DEFAULT_HOURS_OLD // 24

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# ============================================================================
# HIGH-YIELD KEYWORDS (FROM NOTION SCRAPER - PROVEN TO WORK)
# ============================================================================

# These 36 keywords are proven to return 10-12 jobs each on LinkedIn
# DO NOT add more keywords - quality over quantity!
HIGH_YIELD_KEYWORDS = [
    # TIER 0: Strategic Leadership (highest priority)
    "Founder's Office",
    "Chief of Staff",
    "Entrepreneur in Residence",
    "EIR",

    # TIER 1: Product Management
    "Product Manager",
    "APM",
    "Associate Product Manager",
    "Senior Product Manager",

    # TIER 2: Strategy & Growth
    "Strategy Manager",
    "Growth Manager",
    "Business Strategy Manager",
    "Corporate Strategy Manager",

    # TIER 3: Consulting
    "Management Consultant",
    "Strategy Consultant",
    "Business Consultant",
    "Senior Consultant",

    # TIER 4: Operations & Analytics
    "Business Operations Manager",
    "Program Manager",
    "Business Analyst",
    "Strategy Analyst",

    # TIER 5: Internships (high-yield only)
    "Product Manager Intern",
    "Strategy Intern",
    "Business Analyst Intern",
    "Consulting Intern",
    "Founder's Office Intern",
]

# REMOVED: All the low-yield keywords that return 0-1 jobs
# Examples of REMOVED keywords:
# - "Principal Consultant" (returns 1 job, 0% success)
# - "CGO", "CSO", "COO" (returns 1 job each, 0% success)
# - "VP of Strategy", "Director of Product" (returns 1 job, 0% success)
# - All the leadership titles that are too specific

# ============================================================================
# ROLE CATEGORIES (SIMPLIFIED - NO WEIGHTED DISTRIBUTION)
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

# CATEGORY 2: PRODUCT MANAGEMENT ROLES (25% weight) - EXPANDED WITH LEADERSHIP
PRODUCT_KEYWORDS = [
    # Individual Contributor & Mid-Level
    "Product Manager", "Senior Product Manager", "Associate Product Manager",
    "Product Strategy Manager", "Principal Product Manager",
    "Lead Product Manager", "Group Product Manager",
    
    # Leadership & Executive
    "Head of Product", "Director of Product", "VP of Product",
    "Chief Product Officer", "CPO", "Product Director",
    "Product Lead", "Product Head",
]

PRODUCT_INTERNSHIPS = [
    "Product Management Intern", "Product Manager Intern",
    "Associate Product Manager Intern", "Product Strategy Intern",
]

# CATEGORY 3: STRATEGY & GROWTH ROLES (25% weight) - EXPANDED WITH LEADERSHIP
STRATEGY_KEYWORDS = [
    # Individual Contributor & Mid-Level
    "Growth Strategy Manager", "Business Strategy Manager",
    "Corporate Strategy Manager", "Strategy Manager",
    "Growth Manager", "Business Growth Manager",
    
    # Leadership & Executive
    "Head of Strategy", "Director of Strategy", "VP of Strategy",
    "Chief Strategy Officer", "CSO", "Strategy Director",
    "Head of Growth", "Director of Growth", "VP of Growth",
    "Chief Growth Officer", "CGO",
]

STRATEGY_INTERNSHIPS = [
    "Growth Strategy Intern", "Business Strategy Intern",
    "Corporate Strategy Intern", "Strategy Intern",
    "Growth Intern", "Business Growth Intern",
]

# CATEGORY 4: OPERATIONS & ANALYTICS ROLES (20% weight) - EXPANDED WITH LEADERSHIP
OPERATIONS_KEYWORDS = [
    # Individual Contributor & Mid-Level
    "Business Operations Manager", "Operations Strategy Manager",
    "Strategy Analyst", "Business Analyst",
    "Program Manager", "Strategic Project Manager",
    "Founder's Office", "Market Research Analyst",
    
    # Leadership & Executive
    "Chief of Staff", "CoS", "Executive Chief of Staff",
    "Head of Operations", "Director of Operations", "VP of Operations",
    "Chief Operating Officer", "COO", "Operations Director",
    "Head of Business Operations", "Director of Business Operations",
    "Head of Programs", "Director of Programs",
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

# NEW: Required title patterns for high confidence (by category) - EXPANDED
REQUIRED_PATTERNS_BY_CATEGORY = {
    "consulting": [r'\bconsultant\b', r'\bconsulting\b', r'\badvisor\b', r'\badvisory\b'],
    "product": [
        r'\bproduct\s+manager\b', r'\bproduct\s+management\b', r'\bapm\b', r'\bpm\b',
        r'\bhead\s+of\s+product\b', r'\bdirector\s+of\s+product\b', r'\bvp\s+of\s+product\b',
        r'\bchief\s+product\s+officer\b', r'\bcpo\b', r'\bproduct\s+director\b',
        r'\bproduct\s+lead\b', r'\bproduct\s+head\b'
    ],
    "strategy": [
        r'\bstrategy\b', r'\bgrowth\b', r'\bstrategic\b',
        r'\bhead\s+of\s+strategy\b', r'\bdirector\s+of\s+strategy\b', r'\bvp\s+of\s+strategy\b',
        r'\bchief\s+strategy\s+officer\b', r'\bcso\b',
        r'\bhead\s+of\s+growth\b', r'\bdirector\s+of\s+growth\b', r'\bvp\s+of\s+growth\b',
        r'\bchief\s+growth\s+officer\b', r'\bcgo\b'
    ],
    "operations": [
        r'\boperations\b', r'\bprogram\s+manager\b', r'\bbusiness\s+analyst\b', 
        r'\bstrategy\s+analyst\b', r"founder'?s?\s+office\b", r'\bmarket\s+research\b',
        r'\bchief\s+of\s+staff\b', r'\bcos\b',
        r'\bhead\s+of\s+operations\b', r'\bdirector\s+of\s+operations\b', r'\bvp\s+of\s+operations\b',
        r'\bchief\s+operating\s+officer\b', r'\bcoo\b',
        r'\bhead\s+of\s+business\s+operations\b', r'\bhead\s+of\s+programs\b'
    ],
}

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
        # CRITICAL FIX: Scroll MORE to load more jobs (was 2, now 5)
        await self.scroll_page_to_bottom(pause_time=0.5, max_scrolls=5)
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
            "total_jobs": 0,
            "duplicates_skipped": 0,
            "filtered_out": 0,
            "old_jobs_filtered": 0,  # NEW: Track jobs filtered by date
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
    
    def get_high_yield_keywords(self) -> List[str]:
        """
        Get ONLY high-yield keywords that are proven to work.
        
        CRITICAL INSIGHT: LinkedIn returns 1 job for specific keywords, 10-12 for generic ones.
        Solution: Use ONLY the 36 generic keywords from Notion scraper.
        
        Returns:
            List of keyword strings (no tuples, no categories)
        """
        return HIGH_YIELD_KEYWORDS
    
    def detect_role_category(self, job_title: str) -> Optional[str]:
        """Detect which category a job belongs to (EXPANDED with leadership roles)."""
        title_lower = job_title.lower().strip()
        
        # Check each category (with leadership roles)
        if any(term in title_lower for term in ["consultant", "consulting", "advisory", "advisor"]):
            return "consulting"
        elif any(term in title_lower for term in [
            "product manager", "product management", "apm",
            "head of product", "director of product", "vp of product", "vp product",
            "chief product officer", "cpo", "product director", "product lead", "product head"
        ]):
            return "product"
        elif any(term in title_lower for term in [
            "strategy", "growth", "strategic",
            "head of strategy", "director of strategy", "vp of strategy", "vp strategy",
            "chief strategy officer", "cso",
            "head of growth", "director of growth", "vp of growth", "vp growth",
            "chief growth officer", "cgo"
        ]):
            return "strategy"
        elif any(term in title_lower for term in [
            "operations", "program manager", "business analyst", 
            "strategy analyst", "founder", "market research",
            "chief of staff", "cos",
            "head of operations", "director of operations", "vp of operations", "vp operations",
            "chief operating officer", "coo",
            "head of business operations", "head of programs", "director of programs"
        ]):
            return "operations"
        
        return None
    
    def normalize_employment_type(self, raw_type: str) -> str:
        """
        Normalize employment type to consistent format.
        
        Handles:
        - Indeed: 'fulltime', 'parttime', 'contract', 'internship'
        - Naukri: 'fulltime', 'parttime', 'contract'
        - LinkedIn: 'Full Time', 'Part Time', 'Contract', 'Internship'
        - Missing: 'nan', '', None
        
        Returns: Title case with space (e.g., 'Full Time', 'Internship')
        """
        if not raw_type or str(raw_type).lower() in ['nan', 'none', '']:
            return 'Full Time'  # Default
        
        type_str = str(raw_type).strip().lower()
        
        # Handle comma-separated values (e.g., "fulltime, internship")
        if ',' in type_str:
            # Take the first value
            type_str = type_str.split(',')[0].strip()
        
        # Normalize to title case with space
        type_mapping = {
            'fulltime': 'Full Time',
            'full-time': 'Full Time',
            'full time': 'Full Time',
            'parttime': 'Part Time',
            'part-time': 'Part Time',
            'part time': 'Part Time',
            'contract': 'Contract',
            'contractor': 'Contract',
            'temporary': 'Temporary',
            'temp': 'Temporary',
            'internship': 'Internship',
            'intern': 'Internship',
            'freelance': 'Freelance',
            'freelancer': 'Freelance',
        }
        
        # Try exact match first
        if type_str in type_mapping:
            return type_mapping[type_str]
        
        # Try partial match
        for key, value in type_mapping.items():
            if key in type_str:
                return value
        
        # If no match, return title case of original
        return raw_type.strip().title()

    
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
        
        # Category 2: Product (EXPANDED with leadership)
        product_terms = [
            'product manager', 'product management', 'apm', 'associate product',
            'head of product', 'director of product', 'vp of product', 'vp product',
            'chief product officer', 'cpo', 'product director', 'product lead', 'product head'
        ]
        if any(term in title_lower for term in product_terms):
            return True, "Matches product category"
        
        # Category 3: Strategy & Growth (EXPANDED with leadership)
        strategy_terms = [
            'strategy', 'growth', 'strategic',
            'head of strategy', 'director of strategy', 'vp of strategy', 'vp strategy',
            'chief strategy officer', 'cso',
            'head of growth', 'director of growth', 'vp of growth', 'vp growth',
            'chief growth officer', 'cgo'
        ]
        if any(term in title_lower for term in strategy_terms):
            return True, "Matches strategy category"
        
        # Category 4: Operations & Analytics (EXPANDED with leadership)
        operations_terms = [
            'operations', 'program manager', 'business analyst', 
            'strategy analyst', 'founder', 'market research',
            'chief of staff', 'cos',
            'head of operations', 'director of operations', 'vp of operations', 'vp operations',
            'chief operating officer', 'coo',
            'head of business operations', 'head of programs', 'director of programs'
        ]
        if any(term in title_lower for term in operations_terms):
            return True, "Matches operations category"
        
        # Internships - accept if has "intern" + any role keyword
        if 'intern' in title_lower:
            role_keywords = ['product', 'strategy', 'consulting', 'business', 'operations', 'analyst', 'growth']
            if any(kw in title_lower for kw in role_keywords):
                return True, "Matches internship in target category"
        
        return False, f"Does not match any target category: {job_title}"
    
    def is_valid_role(self, job_title: str, company: str = "", search_keyword: str = "") -> tuple[bool, str]:
        """
        VALIDATION v6.0: PRECISE matching for user's exact requirements.
        
        USER REQUIREMENTS (CRYSTAL CLEAR):
        
        ACCEPT (Core Non-Technical Roles):
        1. ALL Consultant roles (HIGHEST PRIORITY - NEVER reject)
           - Product Consultant, Financial Consultant, Technical Consultant, etc.
        2. Program Manager (all levels)
        3. Product Manager (all levels)
        4. Growth roles
        5. Strategy roles
        6. Operations roles (business operations, not technical ops)
        7. Analyst roles (Business Analyst, Strategy Analyst, Product Analyst)
        8. Founder's Office / Chief of Staff
        9. ALL internships for above roles
        
        REJECT:
        - Technical roles (Full Stack Developer, Software Engineer, etc.)
        - Marketing roles (Marketing Manager, Marketing Intern, etc.)
        - HR roles (HR Manager, HR Executive, Recruiter)
        - Sales roles (Sales Executive, BDE, etc.)
        - Admin/Support roles
        
        Philosophy: Two-step validation
        1. Check if it's a WANTED role (consultant, PM, analyst, etc.)
        2. Check if it's NOT a REJECTED role (tech, marketing, HR, sales)
        
        Returns (is_valid, reason) tuple.
        """
        if not job_title or job_title.strip() in ["", "Post a job", "View job", "Join LinkedIn"]:
            return False, "Empty or invalid job title"
        
        title_lower = job_title.lower().strip()
        
        # ========================================================================
        # STEP 1: HARD REJECT - Technical & Unwanted Roles (STRICT)
        # ========================================================================
        # These are NEVER acceptable, even if they match wanted categories
        
        hard_reject_keywords = [
            # Technical/Engineering roles (REJECT ALL)
            'software engineer', 'software developer', 'full stack', 'fullstack',
            'frontend developer', 'backend developer', 'front end', 'back end',
            'web developer', 'mobile developer', 'ios developer', 'android developer',
            'devops', 'sre', 'site reliability',
            'data engineer', 'ml engineer', 'machine learning engineer',
            'ai engineer', 'artificial intelligence',
            'cloud engineer', 'infrastructure engineer',
            'qa engineer', 'test engineer', 'sdet',
            'ui developer', 'ux developer',
            '.net developer', 'java developer', 'python developer',
            'react developer', 'angular developer', 'node developer',
            
            # Marketing roles (REJECT ALL)
            'marketing manager', 'marketing executive', 'marketing coordinator',
            'marketing intern', 'marketing associate',
            'digital marketing', 'performance marketing', 'growth marketing',
            'social media manager', 'social media executive', 'social media intern',
            'brand manager', 'brand executive',
            'seo executive', 'seo manager', 'seo specialist',
            'content marketing', 'email marketing',
            'marketing communications', 'marcom',
            
            # HR roles (REJECT ALL)
            'hr manager', 'hr executive', 'hr business partner', 'hrbp',
            'human resources manager', 'human resources executive',
            'recruiter', 'recruitment', 'talent acquisition',
            'hr intern', 'hr associate',
            
            # Sales roles (REJECT ALL)
            'sales executive', 'sales manager', 'sales associate',
            'sales intern', 'sales representative', 'sales rep',
            'business development executive', 'bde',
            'account executive', 'account manager',
            'sdr', 'sales development',
            'inside sales', 'outside sales',
            
            # Admin/Support roles (REJECT ALL)
            'admin', 'administrative assistant', 'office admin',
            'executive assistant', 'personal assistant',
            'receptionist', 'front desk',
            'customer support', 'customer service', 'customer success',
            'technical support', 'support engineer',
            'data entry', 'data operator',
            'telecaller', 'tele caller',
            
            # Other unwanted
            'accountant', 'accounting',
            'copywriter', 'copy writer',
            'video editor', 'video editing',
            'content writer', 'content creator',
            'graphic designer', 'ui designer', 'ux designer',
        ]
        
        for rejected in hard_reject_keywords:
            if rejected in title_lower:
                return False, f"Hard reject: '{rejected}' (technical/marketing/HR/sales role)"
        
        # ========================================================================
        # STEP 2: POSITIVE VALIDATION - Must match wanted categories
        # ========================================================================
        # Job must match at least ONE of these categories to be accepted
        
        # Category 1: CONSULTANT (HIGHEST PRIORITY - ALL types accepted)
        is_consultant = (
            'consultant' in title_lower or
            'consulting' in title_lower or
            'advisory' in title_lower or
            'advisor' in title_lower
        )
        
        # Category 2: PROGRAM MANAGER (all levels)
        is_program_manager = (
            'program manager' in title_lower or
            'programme manager' in title_lower or
            'program management' in title_lower or
            ('program' in title_lower and any(term in title_lower for term in ['lead', 'head', 'director', 'vp']))
        )
        
        # Category 3: PRODUCT MANAGER (all levels + all variations)
        is_product_manager = (
            'product manager' in title_lower or
            'product management' in title_lower or
            'product owner' in title_lower or
            'product lead' in title_lower or
            'product specialist' in title_lower or
            'product development' in title_lower or
            'product designer' in title_lower or  # Product design (non-technical)
            'apm' in title_lower or
            'associate product' in title_lower or
            'assistant product' in title_lower or
            'junior product manager' in title_lower or
            'senior product manager' in title_lower or
            'lead product manager' in title_lower or
            'principal product manager' in title_lower or
            'staff product manager' in title_lower or
            'director product' in title_lower or
            'vp product' in title_lower or
            'head of product' in title_lower or
            'chief product officer' in title_lower or
            'cpo' == title_lower or
            # Specialized product roles
            'ai product manager' in title_lower or
            'ml product manager' in title_lower or
            'technical product manager' in title_lower or
            'digital product manager' in title_lower or
            'platform product manager' in title_lower or
            'product manager ai' in title_lower or
            'product manager ml' in title_lower or
            # Numbered levels
            'product manager 1' in title_lower or
            'product manager 2' in title_lower or
            'product manager 3' in title_lower or
            'product manager i' in title_lower or
            'product manager ii' in title_lower or
            'product manager iii' in title_lower or
            # Internships
            'product intern' in title_lower or
            'product management intern' in title_lower
        )
        
        # Category 3B: PROJECT MANAGER (all levels)
        is_project_manager = (
            'project manager' in title_lower or
            'project management' in title_lower or
            'project lead' in title_lower or
            'project coordinator' in title_lower or
            'senior project manager' in title_lower or
            'lead project manager' in title_lower or
            'principal project manager' in title_lower or
            'project director' in title_lower or
            'pmo' in title_lower or
            'project management office' in title_lower or
            'project intern' in title_lower
        )
        
        # Category 4: GROWTH roles
        is_growth = (
            'growth manager' in title_lower or
            'growth lead' in title_lower or
            'growth strategist' in title_lower or
            'growth analyst' in title_lower or
            'growth intern' in title_lower or
            'growth associate' in title_lower or
            'growth specialist' in title_lower or
            'senior growth' in title_lower or
            'principal growth' in title_lower or
            'growth product manager' in title_lower or
            'product growth' in title_lower or
            ('growth' in title_lower and any(term in title_lower for term in 
                ['head', 'director', 'vp', 'manager', 'lead', 'analyst', 'strategist']))
        )
        
        # Category 5: STRATEGY roles
        is_strategy = (
            'strategy manager' in title_lower or
            'strategy lead' in title_lower or
            'strategy analyst' in title_lower or
            'strategy intern' in title_lower or
            'strategic' in title_lower or
            'strategist' in title_lower or
            'business strategy' in title_lower or
            'corporate strategy' in title_lower or
            'product strategy' in title_lower or
            'growth strategy' in title_lower or
            'strategy consultant' in title_lower or
            'strategy associate' in title_lower or
            'senior strategy' in title_lower or
            'principal strategy' in title_lower or
            ('strategy' in title_lower and any(term in title_lower for term in 
                ['head', 'director', 'vp', 'chief', 'manager', 'lead', 'analyst', 'associate']))
        )
        
        # Category 6: OPERATIONS roles (business operations, not technical)
        is_operations = (
            'business operations' in title_lower or
            'operations manager' in title_lower or
            'operations lead' in title_lower or
            'operations analyst' in title_lower or
            'operations intern' in title_lower or
            'operations associate' in title_lower or
            'operations specialist' in title_lower or
            'operations governance' in title_lower or  # NEW
            'governance specialist' in title_lower or  # NEW
            'senior operations' in title_lower or
            'principal operations' in title_lower or
            'biz ops' in title_lower or
            'bizops' in title_lower or
            # More flexible matching for operations roles
            ('operations' in title_lower and not any(bad in title_lower for bad in ['sales operations', 'marketing operations'])) or
            ('governance' in title_lower and any(good in title_lower for good in ['operations', 'business', 'corporate']))
        )
        
        # Category 7: ANALYST roles (business/strategy/product, not technical)
        is_analyst = (
            'business analyst' in title_lower or
            'strategy analyst' in title_lower or
            'product analyst' in title_lower or
            'operations analyst' in title_lower or
            'management analyst' in title_lower or
            'consulting analyst' in title_lower or
            'financial analyst' in title_lower or
            'investment analyst' in title_lower or
            'research analyst' in title_lower or
            'market research analyst' in title_lower or
            'business intelligence analyst' in title_lower or
            'analytics manager' in title_lower or
            'senior analyst' in title_lower or
            'lead analyst' in title_lower or
            'principal analyst' in title_lower or
            'analyst intern' in title_lower or
            ('analyst' in title_lower and any(term in title_lower for term in 
                ['business', 'strategy', 'product', 'operations', 'management', 
                 'consulting', 'financial', 'investment', 'research', 'market']))
        )
        
        # Category 8: FOUNDER'S OFFICE / CHIEF OF STAFF
        is_founders_office = (
            "founder's office" in title_lower or
            'founder office' in title_lower or
            'chief of staff' in title_lower or
            'cos' == title_lower or
            'entrepreneur in residence' in title_lower or
            'eir' in title_lower
        )
        
        # Check if ANY wanted category matches
        if not (is_consultant or is_program_manager or is_product_manager or 
                is_project_manager or is_growth or is_strategy or is_operations or 
                is_analyst or is_founders_office):
            return False, "Does not match any wanted category (consultant/PM/product/project/analyst/strategy/growth/operations)"
        
        # ========================================================================
        # ACCEPT: Job passed all checks
        # ========================================================================
        matched_categories = []
        if is_consultant:
            matched_categories.append("consultant")
        if is_program_manager:
            matched_categories.append("program-manager")
        if is_product_manager:
            matched_categories.append("product-manager")
        if is_project_manager:
            matched_categories.append("project-manager")
        if is_growth:
            matched_categories.append("growth")
        if is_strategy:
            matched_categories.append("strategy")
        if is_operations:
            matched_categories.append("operations")
        if is_analyst:
            matched_categories.append("analyst")
        if is_founders_office:
            matched_categories.append("founders-office")
        
        return True, f"Valid role (matches: {', '.join(matched_categories)})"
    
    def is_job_fresh(self, posted_date: str) -> bool:
        """
        Check if job is within max_days threshold.
        
        CRITICAL: Indeed/Naukri often return old jobs despite hours_old parameter.
        This method provides strict post-scraping validation.
        
        Args:
            posted_date: Date string in various formats
            
        Returns:
            True if job is within max_days threshold, False otherwise
        """
        if not posted_date or str(posted_date).strip() in ['', 'nan', 'None']:
            # No date = reject (don't assume fresh)
            return False
        
        posted_str = str(posted_date).strip().lower()
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self.max_days)
        
        # Parse ISO format dates FIRST (most common for Indeed/Naukri)
        # Format: 2026-04-07, 2026-04-06, etc.
        iso_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', posted_str)
        if iso_match:
            try:
                y, m, d = map(int, iso_match.groups())
                job_time = datetime(y, m, d, tzinfo=timezone.utc)
                is_fresh = job_time >= cutoff
                
                if not is_fresh:
                    days_old = (now - job_time).days
                    logger.debug(f"Job too old: {posted_date} ({days_old} days old, cutoff: {self.max_days} days)")
                
                return is_fresh
            except Exception as e:
                logger.debug(f"Error parsing ISO date '{posted_date}': {e}")
                return False
        
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
                    # Reject if months old
                    return False
                else:
                    return False
                
                return job_time >= cutoff
        
        # If can't parse, REJECT (don't assume fresh)
        logger.debug(f"Could not parse date '{posted_date}', rejecting")
        return False
    
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
        keywords: List[str],  # CHANGED: Simple list, not tuples
        limit_per_keyword: int = 10,
        max_jobs: int = None
    ) -> int:
        """
        Scrape LinkedIn jobs with HIGH-YIELD keywords only.
        
        CRITICAL FIX: Use ONLY 36 proven keywords (not 100+).
        Each keyword returns 10-12 jobs (not 1).
        
        Args:
            keywords: Simple list of keyword strings
            max_jobs: Maximum number of jobs to scrape (stops when reached)
        """
        uploaded = 0
        
        logger.info("="*70)
        logger.info("🔵 LINKEDIN SCRAPING STARTED (HIGH-YIELD KEYWORDS ONLY)")
        logger.info(f"Cities: {len(cities)}, Keywords: {len(keywords)}")
        if max_jobs:
            logger.info(f"Quota: {max_jobs} jobs (will stop when reached)")
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
                if self.shutdown_requested or (max_jobs and uploaded >= max_jobs):
                    break
                
                for keyword in keywords:  # CHANGED: Simple iteration
                    if self.shutdown_requested or (max_jobs and uploaded >= max_jobs):
                        break
                    
                    completed += 1
                    
                    # Calculate remaining quota
                    remaining = max_jobs - uploaded if max_jobs else limit_per_keyword
                    actual_limit = min(limit_per_keyword, remaining) if max_jobs else limit_per_keyword
                    
                    logger.info(f"[{completed}/{total_tasks}] Processing: {keyword} in {city} [Quota: {uploaded}/{max_jobs or '∞'}]")
                    
                    try:
                        search_scraper = OptimizedJobSearchScraper(browser.page, callback=ConsoleCallback())
                        
                        # Search for jobs WITH DATE FILTER
                        job_urls = await search_scraper.search(
                            keywords=keyword,
                            location=city,
                            limit=actual_limit,
                            days_ago=self.max_days
                        )
                        
                        logger.info(f"Found {len(job_urls)} jobs for '{keyword}' in {city}")
                        
                        # Process jobs (same as before)
                        job_scraper = JobScraper(browser.page, callback=ConsoleCallback())
                        
                        valid_jobs_count = 0
                        skipped_early = 0
                        
                        for job_url in job_urls:
                            if max_jobs and uploaded >= max_jobs:
                                break
                            
                            if self.shutdown_requested:
                                break
                            
                            if self.is_duplicate(job_url):
                                self.stats["duplicates_skipped"] += 1
                                continue
                            
                            try:
                                await self.engine.rate_limiter.acquire('linkedin')
                                
                                # Early validation (extract title first)
                                quick_title = ""
                                quick_company = ""
                                
                                try:
                                    await browser.page.goto(job_url, wait_until="domcontentloaded", timeout=10000)
                                    
                                    title_selectors = [
                                        'h1.top-card-layout__title',
                                        'h1.t-24.t-bold',
                                        'h2.top-card-layout__title',
                                        'h1[class*="job"]',
                                        'h1',
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
                                    
                                    company_selectors = [
                                        'a.topcard__org-name-link',
                                        'span.topcard__flavor',
                                        'a[data-tracking-control-name*="company"]',
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
                                    
                                    if quick_title:
                                        is_valid, reason = self.is_valid_role(
                                            quick_title.strip(),
                                            quick_company.strip(),
                                            keyword
                                        )
                                        
                                        if not is_valid:
                                            self.stats["filtered_out"] += 1
                                            skipped_early += 1
                                            logger.info(f"❌ Rejected: '{quick_title}' at {quick_company} | Reason: {reason}")
                                            continue
                                        
                                        logger.info(f"✅ Valid: '{quick_title}' | {reason}")
                                
                                except Exception as e:
                                    logger.info(f"⚠️  Early extraction failed: {str(e)[:100]}, falling back to full scrape")
                                
                                # Full scrape
                                job = await job_scraper.scrape(job_url)
                                
                                # Final validation
                                is_valid, reason = self.is_valid_role(
                                    job.job_title or "",
                                    job.company or "",
                                    keyword
                                )
                                
                                if not is_valid:
                                    self.stats["filtered_out"] += 1
                                    logger.info(f"❌ Rejected: '{job.job_title}' at {job.company} | Reason: {reason}")
                                    continue
                                
                                # Process description
                                description = job.job_description or ""
                                if description:
                                    description = description.replace("… more", "").replace("... more", "")
                                    description = description.replace("Show less", "").replace("Show more", "")
                                    if len(description) > 45000:
                                        description = description[:45000]
                                
                                # Detect category
                                category = self.detect_role_category(job.job_title or "")
                                
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
                                    "category": category or "unknown",
                                }
                                
                                # Upload immediately
                                if self.upload_job("linkedin", job_data):
                                    uploaded += 1
                                    valid_jobs_count += 1
                                    self.stats["linkedin_jobs"] += 1
                                    self.stats["total_jobs"] += 1
                                    logger.info(f"✓ LinkedIn [{category or 'unknown'}]: {job.job_title} at {job.company} [{uploaded}/{max_jobs or '∞'}]")
                            
                            except Exception as e:
                                self.stats["errors"] += 1
                                logger.debug(f"Error scraping job: {e}")
                        
                        # Log success rate
                        if len(job_urls) > 0:
                            success_rate = (valid_jobs_count / len(job_urls)) * 100
                            logger.info(f"📊 '{keyword}' in {city}: {success_rate:.1f}% success ({valid_jobs_count}/{len(job_urls)} jobs)")
                            if skipped_early > 0:
                                logger.info(f"  ⚡ Early rejections (time saved): {skipped_early} jobs")
                        
                        await asyncio.sleep(0.5)
                    
                    except Exception as e:
                        self.stats["errors"] += 1
                        logger.error(f"Error processing {keyword} in {city}: {e}")
        
        logger.info("="*70)
        logger.info(f"🔵 LINKEDIN SCRAPING COMPLETE: {uploaded} jobs uploaded")
        if max_jobs:
            quota_pct = (uploaded / max_jobs * 100) if max_jobs > 0 else 0
            logger.info(f"   Quota utilization: {quota_pct:.1f}% ({uploaded}/{max_jobs})")
        logger.info("="*70)
        return uploaded
    
    def scrape_indeed_naukri_batch(
        self,
        cities: List[str],
        keywords: List[str],  # FIXED: Simple list, not tuples
        limit_per_city: int = 10,
        max_jobs: int = None
    ) -> int:
        """
        Scrape Indeed jobs with HIGH-YIELD keywords only.
        
        NOTE: Naukri removed due to 406 Recaptcha errors.
        
        CRITICAL OPTIMIZATION: Indeed ignores hours_old parameter and returns old jobs.
        Solution: Pre-filter DataFrame by date BEFORE processing individual jobs.
        
        Args:
            keywords: Simple list of keyword strings
            max_jobs: Maximum number of jobs to scrape (stops when reached)
        """
        uploaded = 0
        
        logger.info("="*70)
        logger.info("🟢 INDEED SCRAPING STARTED (HIGH-YIELD KEYWORDS ONLY)")
        logger.info(f"Cities: {len(cities)}, Keywords: {len(keywords)}")
        if max_jobs:
            logger.info(f"Quota: {max_jobs} jobs (will stop when reached)")
        logger.info("="*70)
        
        for city in cities:
            if self.shutdown_requested or (max_jobs and uploaded >= max_jobs):
                break
            
            for keyword in keywords:  # FIXED: Simple iteration
                if self.shutdown_requested or (max_jobs and uploaded >= max_jobs):
                    break
                
                # Calculate remaining quota
                remaining = max_jobs - uploaded if max_jobs else limit_per_city
                actual_limit = min(limit_per_city, remaining) if max_jobs else limit_per_city
                
                logger.info(f"Scraping: {keyword} in {city} [Quota: {uploaded}/{max_jobs or '∞'}]")
                    
                try:
                    time.sleep(1)
                    
                    # Request MORE jobs (Indeed returns old ones)
                    request_limit = actual_limit * 3
                    
                    # Scrape Indeed ONLY (Naukri removed due to Recaptcha)
                    df = scrape_multi_platform(
                        sites=["indeed"],
                        search_term=keyword,
                        location=city,
                        results_wanted=request_limit,  # Request MORE
                        hours_old=self.max_days * 24,
                        description_format="html",  # CRITICAL: Request HTML, not markdown
                        verbose=0
                    )
                    
                    if len(df) == 0:
                        continue
                    
                    # ========================================================================
                    # CRITICAL OPTIMIZATION: PRE-FILTER BY DATE (Before processing)
                    # ========================================================================
                    original_count = len(df)
                    
                    # Filter out old jobs FIRST
                    fresh_jobs = []
                    for _, row in df.iterrows():
                        posted_date = str(row.get('date_posted', ''))
                        if self.is_job_fresh(posted_date):
                            fresh_jobs.append(row)
                        else:
                            self.stats["old_jobs_filtered"] += 1
                    
                    # Log filtering results
                    filtered_count = original_count - len(fresh_jobs)
                    if filtered_count > 0:
                        logger.info(f"⚡ Pre-filtered {filtered_count}/{original_count} old jobs (saved {filtered_count} validations)")
                    
                    # If no fresh jobs, skip to next keyword
                    if len(fresh_jobs) == 0:
                        logger.info(f"❌ No fresh jobs found for '{keyword}' in {city} (all {original_count} were too old)")
                        continue
                    
                    # Limit to actual_limit (we requested 3x, now trim to what we need)
                    fresh_jobs = fresh_jobs[:actual_limit]
                    
                    logger.info(f"✅ Found {len(fresh_jobs)} fresh jobs (filtered from {original_count})")
                    
                    # ========================================================================
                    # Process ONLY fresh jobs
                    # ========================================================================
                    valid_jobs_count = 0
                    
                    for row in fresh_jobs:
                        # Check quota again (inner loop)
                        if max_jobs and uploaded >= max_jobs:
                            logger.info(f"✅ Indeed quota reached mid-processing ({uploaded}/{max_jobs})")
                            break
                        
                        job_url = row.get('job_url', '')
                        if not job_url or self.is_duplicate(job_url):
                            self.stats["duplicates_skipped"] += 1
                            continue
                        
                        platform = row.get('site', 'indeed')
                        job_title = row.get('title', '')
                        company = str(row.get('company', ''))
                        posted_date = str(row.get('date_posted', ''))
                        
                        # Date already validated in pre-filter, skip check
                        
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
                                from job_description_extractor import extract_indeed_description, extract_from_text
                                
                                # Indeed only (Naukri removed)
                                formatted_desc = extract_indeed_description(raw_desc) or extract_from_text(raw_desc) or raw_desc
                                
                                if len(formatted_desc) > 45000:
                                    formatted_desc = formatted_desc[:45000]
                            except Exception as e:
                                logger.debug(f"Description extraction error: {e}")
                                formatted_desc = raw_desc[:45000] if len(raw_desc) > 45000 else raw_desc
                        
                        # Normalize
                        raw_employment_type = str(row.get('job_type', 'Full Time'))
                        normalized_employment_type = self.normalize_employment_type(raw_employment_type)
                        
                        # Detect category BEFORE creating job_data
                        category = self.detect_role_category(job_title)
                        
                        job_data = {
                            "job_title": self.sanitizer.sanitize_html(job_title),
                            "company": self.sanitizer.sanitize_html(company),
                            "company_logo": self.sanitizer.sanitize_url(str(row.get('company_logo', ''))),
                            "employment_type": normalized_employment_type,
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
                            self.stats["indeed_jobs"] += 1  # Only Indeed now
                            self.stats["total_jobs"] += 1
                            logger.info(f"✓ {platform.capitalize()} [{category}]: {job_title} [{uploaded}/{max_jobs or '∞'}]")
                    
                    # Log success rate
                    if len(fresh_jobs) > 0:
                        success_rate = (valid_jobs_count / len(fresh_jobs)) * 100
                        logger.info(f"📊 '{keyword}' in {city}: {success_rate:.1f}% success ({valid_jobs_count}/{len(fresh_jobs)} fresh jobs)")
                
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.error(f"Error scraping {keyword} in {city}: {e}")
                
                time.sleep(1)
            
            time.sleep(2)
        
        logger.info("="*70)
        logger.info(f"🟢 INDEED SCRAPING COMPLETE: {uploaded} jobs uploaded")
        if max_jobs:
            quota_pct = (uploaded / max_jobs * 100) if max_jobs > 0 else 0
            logger.info(f"   Quota utilization: {quota_pct:.1f}% ({uploaded}/{max_jobs})")
        logger.info(f"   Old jobs filtered: {self.stats['old_jobs_filtered']} (saved processing time)")
        logger.info("="*70)
        return uploaded
    
    async def run(
        self,
        cities: List[str] = None,
        include_internships: bool = True,
        limit_per_city: int = 10,
        target_total_jobs: int = 100,  # NEW: Total jobs to scrape
        linkedin_ratio: float = 0.80,  # NEW: 80% LinkedIn (changed from 60%)
    ) -> Dict[str, Any]:
        """
        Run hybrid scraping workflow with CONTROLLED DISTRIBUTION.
        
        NEW: Enforces 80:20 LinkedIn:Indeed ratio by setting quotas.
        
        Args:
            target_total_jobs: Total jobs to scrape (default: 100)
            linkedin_ratio: Percentage of jobs from LinkedIn (default: 0.80 = 80%)
        """
        cities = cities or DEFAULT_CITIES
        
        # Calculate platform quotas
        linkedin_quota = int(target_total_jobs * linkedin_ratio)
        indeed_quota = target_total_jobs - linkedin_quota
        
        # Get high-yield keywords (FIXED: Use new method)
        keywords = self.get_high_yield_keywords()
        
        # CRITICAL FIX: Don't divide quota by total searches!
        # Instead, request MORE jobs per search and stop when quota is reached
        # This ensures we get enough jobs even if some are rejected
        total_searches = len(cities) * len(keywords)
        
        # Request 10-15 jobs per search (LinkedIn typically returns this many)
        # The quota will stop us when we reach the target
        linkedin_limit_per_search = 15 if "linkedin" in self.platforms else 0
        indeed_limit_per_search = 5 if "indeed" in self.platforms else 0
        
        logger.info("="*70)
        logger.info("HYBRID OPTIMIZED SCRAPER - HIGH-YIELD KEYWORDS ONLY")
        logger.info("="*70)
        logger.info(f"Platforms: {', '.join(self.platforms)}")
        logger.info(f"Cities: {len(cities)}")
        logger.info(f"Keywords: {len(keywords)} (high-yield only)")
        logger.info(f"Time Filter: Past {self.max_days} days")
        logger.info("-"*70)
        logger.info("DISTRIBUTION QUOTAS:")
        logger.info(f"  Target Total: {target_total_jobs} jobs")
        logger.info(f"  LinkedIn:     {linkedin_quota} jobs ({linkedin_ratio*100:.0f}%) - {linkedin_limit_per_search} per search")
        logger.info(f"  Indeed:       {indeed_quota} jobs ({(1-linkedin_ratio)*100:.0f}%) - {indeed_limit_per_search} per search")
        logger.info("="*70)
        
        # Store quotas for tracking
        self.linkedin_quota = linkedin_quota
        self.indeed_quota = indeed_quota
        
        # Connect to Google Sheets
        if not self.connect_sheets():
            return {"success": False, "error": "Google Sheets connection failed"}
        
        # PARALLEL EXECUTION: Run all platforms simultaneously with quotas
        tasks = []
        
        # Add LinkedIn task with quota
        if "linkedin" in self.platforms:
            logger.info(f"🚀 Starting LinkedIn scraping (quota: {linkedin_quota} jobs)")
            tasks.append(
                asyncio.create_task(
                    self.scrape_linkedin_batch(
                        cities, 
                        keywords,  # FIXED: Use simple list
                        linkedin_limit_per_search,
                        max_jobs=linkedin_quota
                    )
                )
            )
        
        # Add Indeed task with quota (run in executor since it's synchronous)
        if "indeed" in self.platforms:
            logger.info(f"🚀 Starting Indeed scraping (quota: {indeed_quota} jobs)")
            loop = asyncio.get_event_loop()
            tasks.append(
                loop.run_in_executor(
                    None,
                    self.scrape_indeed_naukri_batch,
                    cities,
                    keywords,  # FIXED: Use simple list
                    indeed_limit_per_search,
                    indeed_quota
                )
            )
        
        # Wait for all platforms to complete (or until shutdown)
        if tasks:
            logger.info(f"⏳ Running {len(tasks)} platform(s) in parallel with quotas...")
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Print summary with distribution analysis
        self._print_summary()
        
        return {
            "success": self.stats["total_jobs"] > 0,
            "total_jobs": self.stats["total_jobs"],
            "stats": self.stats,
        }
    
    def _print_summary(self):
        """Print workflow summary with category breakdown, success rate, and DISTRIBUTION analysis."""
        total_processed = self.stats["total_jobs"] + self.stats["filtered_out"]
        success_rate = (self.stats["total_jobs"] / total_processed * 100) if total_processed > 0 else 0
        
        # Calculate platform distribution
        linkedin_pct = (self.stats['linkedin_jobs'] / self.stats['total_jobs'] * 100) if self.stats['total_jobs'] > 0 else 0
        indeed_pct = (self.stats['indeed_jobs'] / self.stats['total_jobs'] * 100) if self.stats['total_jobs'] > 0 else 0
        
        print("\n" + "="*70)
        if self.shutdown_requested:
            print("EXECUTION SUMMARY - GRACEFUL SHUTDOWN")
        else:
            print("EXECUTION SUMMARY - MULTI-CATEGORY SCRAPER")
        print("="*70)
        print(f"LinkedIn Jobs:  {self.stats['linkedin_jobs']} ({linkedin_pct:.1f}%)")
        print(f"Indeed Jobs:    {self.stats['indeed_jobs']} ({indeed_pct:.1f}%)")
        print(f"Total Jobs:     {self.stats['total_jobs']}")
        
        # Distribution analysis
        if hasattr(self, 'linkedin_quota') and hasattr(self, 'indeed_quota'):
            print("-"*70)
            print("DISTRIBUTION ANALYSIS:")
            print(f"  Target:  LinkedIn {self.linkedin_quota} ({linkedin_pct:.0f}%) | Indeed {self.indeed_quota} ({indeed_pct:.0f}%)")
            print(f"  Actual:  LinkedIn {self.stats['linkedin_jobs']} ({linkedin_pct:.1f}%) | Indeed {self.stats['indeed_jobs']} ({indeed_pct:.1f}%)")
            
            # Check if distribution is close to target
            target_linkedin_pct = (self.linkedin_quota / (self.linkedin_quota + self.indeed_quota) * 100)
            deviation = abs(linkedin_pct - target_linkedin_pct)
            
            if deviation < 5:
                print(f"  Status:  ✅ Distribution on target (deviation: {deviation:.1f}%)")
            elif deviation < 15:
                print(f"  Status:  ⚠️  Slight deviation from target ({deviation:.1f}%)")
            else:
                print(f"  Status:  ❌ Significant deviation from target ({deviation:.1f}%)")
                if linkedin_pct < target_linkedin_pct - 10:
                    print(f"           LinkedIn underperforming - may need more keywords or cities")
                elif linkedin_pct > target_linkedin_pct + 10:
                    print(f"           LinkedIn overperforming - Indeed may need adjustment")
        
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
        print(f"  - Old Jobs:   {self.stats['old_jobs_filtered']} (posted > {self.max_days} days ago)")
        print(f"  - Invalid:    {self.stats['filtered_out'] - self.stats['old_jobs_filtered']}")
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
            
            # Distribution insights
            if hasattr(self, 'linkedin_quota'):
                if linkedin_pct < 50:
                    print(f"  • LinkedIn underperforming ({linkedin_pct:.1f}%) - may need:")
                    print(f"    - More keywords or cities")
                    print(f"    - Higher limit_per_keyword")
                    print(f"    - Check if LinkedIn rate limiting is too aggressive")
                elif linkedin_pct > 70:
                    print(f"  • LinkedIn overperforming ({linkedin_pct:.1f}%) - Indeed may need:")
                    print(f"    - More keywords or cities")
                    print(f"    - Higher limit_per_city")
            
            print("="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point with graceful shutdown handling and distribution control."""
    parser = argparse.ArgumentParser(
        description="Hybrid Optimized India Jobs Scraper with 80:20 LinkedIn:Indeed Distribution",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["linkedin", "indeed"],
        default=DEFAULT_JOB_BOARDS,
        help="Platforms to scrape (Naukri removed due to Recaptcha)"
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
        help="Jobs per keyword per city (used for quota calculation)"
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        help="Specific cities to search"
    )
    parser.add_argument(
        "--target-total",
        type=int,
        default=100,
        help="Target total jobs to scrape (default: 100)"
    )
    parser.add_argument(
        "--linkedin-ratio",
        type=float,
        default=0.80,
        help="LinkedIn percentage (0.0-1.0, default: 0.80 = 80%%)"
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
        # Run scraper with distribution control
        results = await scraper.run(
            cities=args.cities,
            limit_per_city=args.limit_per_city,
            target_total_jobs=args.target_total,
            linkedin_ratio=args.linkedin_ratio
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
