"""
🎯 Tech + Non-Tech Roles Dashboard
Narrow tech tags (Software Engineer, Data Analyst, Data Engineer, Data Science,
ML Engineer, DevOps & Cloud, QA & Testing, Security) plus Support, Operations,
Marketing, Product, UI/UX and Founder's Office roles.
Reads job listings directly from Notion database and displays them
with the SayBriefly design system.
"""
import os
import sys
import re
import json
import uuid
import tempfile
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Try to import requests for online LaTeX compilation fallback
try:
    import requests as requests_lib
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Load environment variables - look in marketing-dashboard/, project root, AND CWD
load_dotenv(dotenv_path=Path(__file__).parent / '.env')
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
load_dotenv()  # Also check CWD as fallback

import threading

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")

# Global persistent HTTP session for Notion requests (enables HTTP keep-alive / TLS reuse)
_notion_session = None

def _get_notion_session():
    global _notion_session
    if _notion_session is None and REQUESTS_AVAILABLE:
        try:
            _notion_session = requests_lib.Session()
            adapter = requests_lib.adapters.HTTPAdapter(
                pool_connections=10,
                pool_maxsize=10,
                max_retries=2
            )
            _notion_session.mount("https://", adapter)
            _notion_session.mount("http://", adapter)
        except Exception as e:
            print(f"Warning: Could not initialize requests session: {e}")
            _notion_session = None
    return _notion_session

# Prioritized list of free OpenRouter models based on user rankings/scores
FALLBACK_MODELS = [
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-4-26b-a4b-it:free",
    "qwen/qwen3-coder:free",
    "openai/gpt-oss-20b:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "openrouter/free"
]


# High-performance Stale-While-Revalidate Cache configuration
CACHE_DIR = Path(tempfile.gettempdir()) if os.getenv("VERCEL") else Path(__file__).parent
CACHE_FILE = CACHE_DIR / "jobs_cache.json"
CACHE_FRESH_SECONDS = 180      # 3 minutes: cache considered completely fresh
CACHE_MAX_AGE_SECONDS = 86400  # 24 hours: serve stale from memory/disk while background fetching

_jobs_cache = []
_jobs_cache_timestamp = None
_jobs_stats_cache = None
_jobs_locations_cache = None
_cache_lock = threading.Lock()
_fetch_lock = threading.Lock()
_is_fetching = False

# ============================================================================
# ROLES CONFIGURATION
# ============================================================================

# Role domain keywords for filtering
# NOTE: categorize_role() is the source of truth for tagging; this dict documents
# the tag taxonomy and is used for the dropdown labels.
ROLE_DOMAINS = {
    "All": [],
    "Software Engineer": ["software engineer", "software developer", "sde", "backend", "frontend",
                           "full stack", "fullstack", "java developer", "python developer",
                           "react developer", "angular developer", "node.js", "mobile developer",
                           "android developer", "ios developer", "web developer", "wordpress",
                           "tech lead", "software architect", "engineering manager"],
    "Data Analyst": ["data analyst", "data analysis", "analytics analyst", "reporting analyst",
                      "power bi analyst", "mis analyst"],
    "Data Engineer": ["data engineer", "analytics engineer", "data architect", "etl",
                       "data warehouse", "big data"],
    "Data Science": ["data scientist", "data science"],
    "ML Engineer": ["machine learning", "ml engineer", "ai engineer", "artificial intelligence",
                     "deep learning", "nlp", "computer vision", "llm", "genai"],
    "DevOps & Cloud": ["devops", "sre", "site reliability", "platform engineer", "cloud engineer",
                        "infrastructure engineer", "system administrator", "network engineer",
                        "kubernetes", "aws", "azure", "gcp"],
    "QA & Testing": ["qa engineer", "test engineer", "sdet", "qa tester", "automation engineer",
                      "quality assurance", "quality analyst", "qa analyst", "manual tester"],
    "Security": ["security engineer", "cybersecurity", "cyber security", "security analyst",
                  "penetration tester", "information security", "network security"],
    "Support": ["customer support", "customer service", "email support", "support engineer",
                 "technical support", "helpdesk", "service desk", "it support"],
    "Operations": ["operations", "business operations", "ops manager", "ops executive"],
    "Marketing": ["marketing", "brand", "growth marketing", "content marketing", "demand generation",
                   "digital marketing", "performance marketing", "social media", "campaign",
                   "pr manager", "communications", "seo", "marketing lead", "marketing head",
                   "marketing director", "marketing strategist", "marketing specialist",
                   "marketing analyst", "marketing executive", "brand manager",
                   "brand marketing", "product marketing", "marketing intern"],
    "UI/UX": ["ui designer", "ux designer", "ui/ux", "ui ux", "ux researcher",
               "interaction designer", "visual designer", "ux lead", "ux architect",
               "user experience", "user interface", "ux strategist", "ux writer"],
    "Product": ["product manager", "product management", "product designer",
                 "product owner", "product lead", "product analyst", "product strategist",
                 "product director", "product head", "product specialist",
                 "product intern", "product development", "vp product",
                 "head of product", "chief product officer", "cpo",
                 "technical product manager", "ai product manager", "platform product manager"],
    "Founders Office": ["founder's office", "founders office", "chief of staff",
                         "entrepreneur in residence", "entrepreneur-in-residence", "eir"],
}


def categorize_role(role_title: str) -> str:
    """
    Determine which domain tag a role belongs to based on strict keyword matching.
    Tech roles are classified into NARROW sub-domains (not one broad bucket).
    
    Order matters:
    1. Tech sub-domains (Software Engineer, Data Analyst, Data Engineer,
       Data Science, ML Engineer, DevOps & Cloud, QA & Testing, Security)
    2. Support (Email Support, Customer Support Engineer, Technical Support, etc.)
    3. Operations
    4. Product (any role with "Product" in the title qualifies)
    5. Founders Office (strategic leadership roles)
    6. Marketing (clearly marketing-specific roles only, incl. Social Media)
    7. UI/UX (design & user experience roles only)
    8. Other (everything else including sales, admin, hr, finance, etc.)
    
    NOTE: "Software Engineer" → Software Engineer.
    "Data Scientist" → Data Science.
    "ML Engineer" → ML Engineer.
    "Data Analyst" → Data Analyst.
    "QA Engineer" / "Quality Analyst" → QA & Testing.
    "WordPress Developer" / "Web Developer" → Software Engineer.
    "Customer Support Engineer" / "Email Support" → Support.
    "Operations Executive" / "Operations Manager" → Operations.
    "Marketing" / "Social Media Marketing" → Marketing.
    "Account Executive" is classified as Sales → Other.
    "Customer Success" → Other.
    "Business Development" → Other.
    "Graphic Designer" → Other (not Marketing).
    "Team Lead" → Other (generic, not role-specific).
    "Senior Product Designer" → Product (contains "product designer").
    "Product Owner" → Product (contains "product").
    "Account Manager" → Other (Accounts domain removed).
    "Key Account Manager" → Other.
    "Client Partner" → Other.
    "Sales Executive" → Other (sales).
    "Business Development Executive" → Other (sales).
    "Growth Manager" (without "marketing") → Other (could be growth in any function).
    "Brand Manager" → Marketing.
    "Content Writer" → Other (content, not marketing function).
    "Copywriter" → Other.
    "PR Manager" → Marketing.
    "Communications Manager" → Marketing.
    "SEO Manager" → Marketing.
    "Social Media Manager" → Marketing.
    "Product Marketing Manager" → Marketing (product marketing is a marketing function).
    "Product Manager" → Product.
    "Product Designer" → Product.
    "UX Designer" → UI/UX.
    "UI Designer" → UI/UX.
    "UX Researcher" → UI/UX.
    "Visual Designer" → UI/UX.
    "Interaction Designer" → UI/UX.
    "Founder's Office" → Founders Office.
    "Chief of Staff" → Founders Office.
    "Entrepreneur in Residence" → Founders Office.
    "EIR" → Founders Office.
    "HR Manager" → Other.
    "Recruiter" → Other.
    "Admin Assistant" → Other.
    "Receptionist" → Other.
    "Accountant" → Other.
    "Delivery Manager" → Other.
    "Scrum Master" → Other (technical, not in a target tag).
    "Project Manager" → Other (unless product-related, then Product).
    "Program Manager" → Other (unless product-related).
    "Business Analyst" → Other (unless product-related).
    "Financial Analyst" → Other.
    "Investment Analyst" → Other.
    "Research Analyst" → Other (unless UX research, then UI/UX).
    "UX Research Analyst" → UI/UX.
    
    Args:
        role_title: The job title to categorize
        
    Returns:
        Domain tag string, e.g. Software Engineer, Data Analyst, Data Science,
        ML Engineer, DevOps & Cloud, QA & Testing, Security, Support, Operations,
        Marketing, Product, UI/UX, Founders Office, or Other
    """
    if not role_title:
        return "Other"
    title_lower = role_title.lower().strip()

    # ========================================================================
    # HARD EXCLUSIONS FIRST — roles that should NEVER be in any target domain
    # ========================================================================

    # Admin/Back-office roles → always "Other"
    admin_patterns = [
        "executive assistant", "personal assistant", "admin assistant",
        "receptionist", "front desk", "office admin",
        "data entry", "data operator",
        "telecaller", "tele caller",
    ]
    for pat in admin_patterns:
        if pat in title_lower:
            return "Other"

    # HR/Recruitment roles → always "Other"
    hr_patterns = [
        "hr ", "human resources", "recruiter", "recruitment",
        "talent acquisition", "talent partner",
    ]
    for pat in hr_patterns:
        if pat in title_lower:
            return "Other"

    # Finance/Accounting roles → always "Other"
    finance_patterns = [
        "accountant", "accounting", "finance ", "financial analyst",
        "auditor", "tax ", "payroll",
    ]
    for pat in finance_patterns:
        if pat in title_lower:
            return "Other"

    # Sales roles → always "Other"
    # Note: "Account Executive" is a SALES closing role, NOT account management
    sales_patterns = [
        "sales executive", "sales manager", "sales associate",
        "sales intern", "sales representative", "sales rep",
        "sales development", "inside sales", "outside sales",
        "account executive",  # This is sales closing, NOT account management!
        "business development executive", "bde",
        "business development manager",  # Often confused with BD in accounts
        "sdr", "sales development rep",
        "senior account executive", "enterprise account executive",
    ]
    for pat in sales_patterns:
        if pat in title_lower:
            return "Other"

    # ========================================================================
    # TECH SUB-DOMAINS (narrow classification)
    # ========================================================================

    # 1. SOFTWARE ENGINEER — engineering & development (incl. web / WordPress / mobile)
    # SDE titles like "SDE", "SDE I", "SDE-1" (exact word only — "SDET" is QA)
    sde_words = title_lower.replace('-', ' ').split()
    if "sde" in sde_words and "sdet" not in sde_words:
        return "Software Engineer"

    software_patterns = [
        "software engineer", "software developer", "software development",
        "backend", "frontend", "full stack", "fullstack",
        "java developer", "python developer", "react developer", "angular developer",
        "node.js developer", "nodejs", "mobile developer", "android developer",
        "ios developer", "web developer", "wordpress",
        "php developer", "ruby developer", "golang", "dotnet", "c# developer",
        "game developer", "tech lead", "software architect", "engineering manager",
        "staff engineer", "ui developer", "ux developer",
        # Technical program / project management (tech roles)
        "technical program manager", "tpm", "technical project manager",
    ]
    for pat in software_patterns:
        if pat in title_lower:
            return "Software Engineer"

    # 2. DATA ANALYST — analytics & reporting
    data_analyst_patterns = [
        "data analyst", "data analysis", "analytics analyst", "reporting analyst",
        "power bi analyst", "mis analyst", "tableau analyst",
    ]
    for pat in data_analyst_patterns:
        if pat in title_lower:
            return "Data Analyst"

    # 3. DATA ENGINEER — data infrastructure & pipelines
    data_engineer_patterns = [
        "data engineer", "analytics engineer", "data architect", "data modeler",
        "etl developer", "data warehouse", "big data engineer", "data platform",
    ]
    for pat in data_engineer_patterns:
        if pat in title_lower:
            return "Data Engineer"

    # 4. DATA SCIENCE — data science & research
    data_science_patterns = [
        "data scientist", "data science",
    ]
    for pat in data_science_patterns:
        if pat in title_lower:
            return "Data Science"

    # 5. ML ENGINEER — machine learning, AI & deep learning
    ml_patterns = [
        "machine learning", "ml engineer", "ai engineer", "artificial intelligence",
        "deep learning", "nlp", "computer vision", "llm", "generative ai", "genai",
    ]
    for pat in ml_patterns:
        if pat in title_lower:
            return "ML Engineer"

    # 6. DEVOPS & CLOUD — infrastructure, reliability & cloud
    devops_patterns = [
        "devops", "sre", "site reliability", "platform engineer",
        "cloud engineer", "infrastructure engineer", "system administrator", "sysadmin",
        "network engineer", "database administrator", "dba",
        "kubernetes", "aws", "azure", "gcp", "release engineer",
    ]
    for pat in devops_patterns:
        if pat in title_lower:
            return "DevOps & Cloud"

    # 7. QA & TESTING — quality assurance & testing (incl. Quality Analyst)
    qa_patterns = [
        "qa engineer", "test engineer", "sdet", "qa tester", "automation engineer",
        "quality assurance", "quality analyst", "qa analyst", "manual tester",
        "software tester", "test analyst",
    ]
    for pat in qa_patterns:
        if pat in title_lower:
            return "QA & Testing"

    # 8. SECURITY — cybersecurity & information security
    security_patterns = [
        "security engineer", "cybersecurity", "cyber security", "security analyst",
        "penetration tester", "information security", "network security",
        "application security", "soc analyst", "incident response",
    ]
    for pat in security_patterns:
        if pat in title_lower:
            return "Security"

    # ========================================================================
    # CATEGORY: SUPPORT (customer-facing support & service roles)
    # ========================================================================
    support_patterns = [
        "customer support", "customer service", "customer care",
        "support engineer", "technical support", "email support",
        "helpdesk", "help desk", "service desk", "it support",
        "desktop support", "client support",
    ]
    for pat in support_patterns:
        if pat in title_lower:
            return "Support"

    # ========================================================================
    # CATEGORY: OPERATIONS
    # ========================================================================
    operations_patterns = [
        "operations", "business operations",
        "ops manager", "ops executive", "ops associate",
        "ops coordinator", "ops lead",
    ]
    for pat in operations_patterns:
        if pat in title_lower:
            return "Operations"

    # ========================================================================
    # CATEGORY: PRODUCT (any role containing "product" in the title)
    # ========================================================================
    product_terms = [
        "product manager", "product management", "product designer",
        "product owner", "product lead", "product analyst",
        "product strategist", "product director", "product head",
        "product specialist", "product intern", "product development",
        "vp product", "head of product", "chief product officer",
        "cpo", "technical product manager", "ai product manager",
        "digital product manager", "platform product manager",
        "product marketing",  # This is a marketing function but it's a "product" role
    ]
    for term in product_terms:
        if term in title_lower:
            return "Product"

    # Catch-all: if title contains standalone "product" (but not "production")
    # e.g., "Senior Product Designer" → Product (not UI/UX despite having "designer")
    words = title_lower.split()
    if "product" in words:
        return "Product"

    # ========================================================================
    # CATEGORY: FOUNDERS OFFICE (strategic leadership roles)
    # ========================================================================
    founders_terms = [
        "founder's office", "founders office", "founder office",
        "chief of staff", "cos",
        "entrepreneur in residence", "entrepreneur-in-residence", "eir",
    ]
    for term in founders_terms:
        if term in title_lower:
            return "Founders Office"

    # ========================================================================
    # CATEGORY: MARKETING (clearly marketing-specific roles only)
    # ========================================================================
    # Strict: must start with or contain a clear marketing keyword
    marketing_terms = [
        # Direct marketing titles
        "marketing",  # "Marketing", "Marketing Manager", "Marketing Lead", etc.
        "brand manager", "brand marketing", "brand lead",
        "growth marketing",  # NOT just "growth"
        "content marketing",
        "product marketing",
        "performance marketing",
        "digital marketing",
        "social media marketing",  # Explicit "Social Media Marketing" roles
        
        # Marketing specializations
        "marketing intern", "marketing analyst",
        "marketing lead", "marketing head",
        "marketing director", "marketing strategist",
        "marketing specialist", "marketing executive",
        "marketing manager", "marketing coordinator",
        
        # Marketing functions
        "social media", "social-media",
        "campaign manager", "campaign executive",
        "demand generation", "demand-gen",
        
        # PR & Communications
        "pr manager", "pr intern", "public relations",
        "communications manager", "communications lead",
        "corporate communications",
        
        # SEO
        "seo manager", "seo lead", "seo specialist", "seo executive",
        
        # Events & Partnerships
        "event marketing", "partnership marketing",
        "field marketing", "marketing operations",
    ]
    for term in marketing_terms:
        if term in title_lower:
            # Tech / Support / Operations roles were already caught above
            return "Marketing"

    # ========================================================================
    # CATEGORY: UI/UX (design & user experience roles only)
    # ========================================================================
    ux_terms = [
        "ui designer", "ux designer", "ui/ux", "ui ux",
        "ux researcher", "user experience researcher",
        "interaction designer", "visual designer",
        "ux lead", "ux architect", "ux strategist",
        "ux writer", "ux intern", "ux manager",
        "user experience designer", "user interface designer",
        "ux design intern", "design researcher",
        "ux research intern", "usability",
    ]
    for term in ux_terms:
        if term in title_lower:
            return "UI/UX"

    # ========================================================================
    # DEFAULT: Not in any target domain
    # ========================================================================
    return "Other"


def detect_experience_level(role_title: str) -> str:
    """
    Detect the experience/seniority level from a job title.
    
    Classification logic:
    - Entry/Early: Intern, Trainee, Fresher, Junior, Associate, Graduate,
                    Apprentice, Executive (when not Senior Exec)
    - Mid: No seniority indicators (default for most roles)
    - Senior: Senior, Lead, Head, Director, VP, Chief, Principal, Staff,
               Manager (often mid-senior), Owner, Architect, Fellow
    
    Args:
        role_title: The job title to analyze
        
    Returns:
        Experience level string: "Entry Level", "Mid Level", or "Senior Level"
    """
    if not role_title:
        return "Mid Level"
    
    title_lower = role_title.lower().strip()
    
    # ========================================================================
    # Check SENIOR LEVEL indicators first (highest priority)
    # ========================================================================
    senior_keywords = [
        # Seniority prefixes
        "senior ", "sr. ", "sr ",
        # Leadership titles
        "lead ", "head of ", "head ",
        "director of ", "director",
        "vp of ", "vp ", "vice president",
        "chief ", "cfo", "cto", "coo", "cmo", "ceo", "cpo", "cso", "cgo",
        # Staff / Principal
        "principal ", "staff ",
        # Manager (typically mid-to-senior)
        "manager",
        # Owner / Architect / Fellow
        "owner", "architect", "fellow",
        # Strategic roles
        "partner", "practice lead", "global head",
    ]
    for kw in senior_keywords:
        if kw in title_lower:
            return "Senior Level"
    
    # ========================================================================
    # Check ENTRY LEVEL indicators
    # ========================================================================
    entry_keywords = [
        "intern", "trainee", "fresher",
        "junior ", "jr. ", "jr ",
        "associate ",  # "Associate Product Manager" etc.
        "executive",  # Account Executive, Executive Assistant (not Senior Exec)
        "graduate ", "graduate",
        "apprentice",
        "entry level", "entry-level",
        "analyst",  # Many analyst roles are entry-to-mid
    ]
    for kw in entry_keywords:
        if kw in title_lower:
            # But NOT if it also has a senior keyword
            senior_overrides = ["senior analyst", "lead analyst", "principal analyst"]
            if any(override in title_lower for override in senior_overrides):
                return "Senior Level"
            return "Entry Level"
    
    # ========================================================================
    # Default: Mid Level
    # ========================================================================
    return "Mid Level"


# ============================================================================
# NOTION API READER & DATA FETCHING
# ============================================================================

def _notion_request(method, endpoint, body=None):
    """
    Make an optimized HTTP request to the Notion API.
    Uses persistent HTTP keep-alive connection pooling via requests.Session,
    with automatic fallback to urllib.request if needed.
    """
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Try connection-pooled requests session
    session = _get_notion_session()
    if session:
        try:
            resp = session.request(
                method=method,
                url=url,
                json=body,
                headers=headers,
                timeout=20
            )
            if resp.status_code >= 400:
                raise Exception(f"Notion API HTTP {resp.status_code}: {resp.text}")
            return resp.json()
        except Exception as e:
            if "Notion API HTTP" in str(e):
                raise
            # Network blip on session pool, fall through to urllib fallback

    # Fallback to direct urllib.request
    import urllib.request, urllib.error, json
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"Notion API HTTP {e.code}: {error_body}")


def fetch_jobs_from_notion() -> list:
    """
    Fetch all jobs from the Notion database.
    - Requests descending sort by Date Posted so newest jobs arrive first
    - Uses persistent keep-alive connections to avoid SSL handshake overhead
    - Safely extracts text, cleans up properties, and pre-indexes search terms
    """
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("Notion API key or database ID not configured")
        return []

    try:
        all_jobs = []
        has_more = True
        start_cursor = None
        use_sorts = True
        sort_config = [{"property": "Date Posted", "direction": "descending"}]

        while has_more:
            query_body = {"page_size": 100}
            if start_cursor:
                query_body["start_cursor"] = start_cursor
            if use_sorts and sort_config:
                query_body["sorts"] = sort_config

            try:
                response = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", query_body)
            except Exception as e:
                # If Notion rejects sorting (e.g. property mismatch), retry query without sorts
                if use_sorts and ("sort" in str(e).lower() or "validation_error" in str(e).lower() or "HTTP 400" in str(e)):
                    print(f"Notice: Notion sort rejected ({e}), falling back to unsorted query")
                    use_sorts = False
                    sort_config = None
                    if "sorts" in query_body:
                        del query_body["sorts"]
                    response = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", query_body)
                else:
                    raise

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

            for page in response.get("results", []):
                props = page.get("properties", {})

                # Extract Company (Title)
                company = ""
                company_prop = props.get("Company", {})
                if company_prop.get("type") == "title":
                    title_list = company_prop.get("title", [])
                    if title_list:
                        company = "".join(t.get("plain_text", "") for t in title_list).strip()

                # Extract Position (Rich text)
                role = ""
                position_prop = props.get("Position", {})
                if position_prop.get("type") == "rich_text":
                    rt_list = position_prop.get("rich_text", [])
                    if rt_list:
                        role = "".join(t.get("plain_text", "") for t in rt_list).strip()

                # Extract Location (Rich text)
                location = ""
                location_prop = props.get("Location", {})
                if location_prop.get("type") == "rich_text":
                    loc_list = location_prop.get("rich_text", [])
                    if loc_list:
                        location = "".join(t.get("plain_text", "") for t in loc_list).strip()

                # Extract Application Link (URL)
                job_url = ""
                url_prop = props.get("Application Link", {})
                if url_prop.get("type") == "url":
                    job_url = url_prop.get("url", "") or ""

                # Extract Date Posted
                date_str = ""
                date_prop = props.get("Date Posted", {})
                if date_prop.get("type") == "date":
                    date_data = date_prop.get("date", {})
                    if date_data:
                        date_str = date_data.get("start", "")

                created_time = page.get("created_time", "")
                fallback_date = created_time[:10] if created_time else datetime.now().strftime("%Y-%m-%d")

                # Extract role domain and experience level
                domain = categorize_role(role)
                experience_level = detect_experience_level(role)

                all_jobs.append({
                    "id": page.get("id", ""),
                    "company": company or "Unknown",
                    "role": role or "Unknown",
                    "location": location or "India",
                    "url": job_url or "",
                    "date_added": date_str or fallback_date,
                    "domain": domain,
                    "level": experience_level,
                    "created_time": created_time,
                    "last_edited_time": page.get("last_edited_time", ""),
                })

        return all_jobs

    except ImportError:
        return []
    except Exception as e:
        print(f"Error fetching from Notion: {e}")
        return []


# ============================================================================
# HIGH-PERFORMANCE CACHE & AGGREGATION ENGINE
# ============================================================================

def _compute_aggregations(jobs):
    """Pre-compute dashboard stats and locations in a single pass O(N)."""
    total = len(jobs)
    domains = {}
    companies = {}
    locations_map = {}

    for j in jobs:
        # Domain count
        d = j.get("domain", "Other")
        domains[d] = domains.get(d, 0) + 1

        # Company count
        c = j.get("company", "Unknown")
        companies[c] = companies.get(c, 0) + 1

        # Location cleanup & normalization
        loc = (j.get("location") or "").strip()
        if loc and loc.lower() not in ["", "india", "unknown"]:
            normalized = loc.split(",")[0].split("·")[0].split("\u00b7")[0].strip()
            if normalized and normalized.lower() not in ["", "india"]:
                locations_map[normalized] = locations_map.get(normalized, 0) + 1

    sorted_locations = [loc for loc, _ in sorted(locations_map.items(), key=lambda x: (-x[1], x[0]))]

    stats = {
        "total_jobs": total,
        "domains": dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)),
        "companies": dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:20]),
        "total_companies": len(companies),
    }

    return stats, sorted_locations


def _update_cache(jobs, save_disk=True):
    """Update in-memory cache, build fast-search indexes, and persist to disk."""
    global _jobs_cache, _jobs_cache_timestamp, _jobs_stats_cache, _jobs_locations_cache

    if not jobs:
        return

    # Add lowercase search helper fields for high-speed in-memory filtering
    for j in jobs:
        role = j.get("role") or ""
        company = j.get("company") or ""
        location = j.get("location") or ""
        domain = j.get("domain") or "Other"
        level = j.get("level") or ""

        j["_search_text"] = f"{role} {company} {location}".lower()
        j["_domain_lower"] = domain.lower()
        j["_level_lower"] = level.lower()
        j["_location_lower"] = location.lower()

    # Sort descending by date_added and created_time (most recent first)
    jobs.sort(key=lambda j: (j.get("date_added") or "", j.get("created_time") or ""), reverse=True)

    stats, locations = _compute_aggregations(jobs)
    now = datetime.now()

    with _cache_lock:
        _jobs_cache = jobs
        _jobs_cache_timestamp = now
        _jobs_stats_cache = stats
        _jobs_locations_cache = locations

    if save_disk:
        _save_disk_cache(jobs, now)


def _load_disk_cache():
    """Load cached jobs from disk on server startup (< 5ms)."""
    global _jobs_cache, _jobs_cache_timestamp
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            jobs = data.get("jobs", [])
            ts_str = data.get("timestamp")
            if jobs:
                _update_cache(jobs, save_disk=False)
                if ts_str:
                    try:
                        _jobs_cache_timestamp = datetime.fromisoformat(ts_str)
                    except Exception:
                        _jobs_cache_timestamp = datetime.now() - timedelta(minutes=5)
                print(f" Loaded {len(jobs)} jobs from disk cache (saved at {_jobs_cache_timestamp})")
                return True
    except Exception as e:
        print(f"Notice: Could not load disk cache: {e}")
    return False


def _save_disk_cache(jobs, timestamp):
    """Save clean jobs to disk cache atomically."""
    try:
        clean_jobs = []
        for j in jobs:
            clean = {k: v for k, v in j.items() if not k.startswith("_")}
            clean_jobs.append(clean)

        data = {
            "timestamp": timestamp.isoformat(),
            "count": len(clean_jobs),
            "jobs": clean_jobs
        }

        # Write to temporary file first then atomic rename
        temp_file = CACHE_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        temp_file.replace(CACHE_FILE)
    except Exception as e:
        print(f"Notice: Could not save disk cache: {e}")


def _trigger_background_refresh():
    """Trigger background refresh thread (Stale-While-Revalidate)."""
    global _is_fetching

    with _fetch_lock:
        if _is_fetching:
            return  # Already refreshing, do not duplicate
        _is_fetching = True

    def _worker():
        global _is_fetching
        try:
            fresh_jobs = fetch_jobs_from_notion()
            if fresh_jobs:
                _update_cache(fresh_jobs, save_disk=True)
                print(f" Background Notion refresh complete: {len(fresh_jobs)} jobs active")
        except Exception as e:
            print(f"Background refresh error: {e}")
        finally:
            with _fetch_lock:
                _is_fetching = False

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()


def get_jobs(force_refresh: bool = False) -> list:
    """
    Get jobs with Stale-While-Revalidate (SWR) caching.
    - If cache is fresh (< 3 mins): returns immediately (0ms).
    - If cache is stale: returns immediately from memory (0ms) and refreshes in background.
    - If memory empty on startup: loads from persistent disk cache (< 5ms) and refreshes in background.
    - If no cache exists anywhere: synchronous fetch is performed once and cached.
    """
    global _jobs_cache, _jobs_cache_timestamp

    now = datetime.now()

    # User explicitly requested a forced refresh (e.g. Refresh button)
    if force_refresh:
        fresh_jobs = fetch_jobs_from_notion()
        if fresh_jobs:
            _update_cache(fresh_jobs, save_disk=True)
            return _jobs_cache
        return _jobs_cache

    # Check in-memory cache
    with _cache_lock:
        cache_exists = bool(_jobs_cache)
        is_fresh = False
        if cache_exists and _jobs_cache_timestamp:
            age = (now - _jobs_cache_timestamp).total_seconds()
            is_fresh = age < CACHE_FRESH_SECONDS

    # 1. Fresh cache: instant return
    if cache_exists and is_fresh:
        return _jobs_cache

    # 2. Stale cache: instant return + trigger background refresh
    if cache_exists and not is_fresh:
        _trigger_background_refresh()
        return _jobs_cache

    # 3. Memory cache empty: check disk cache
    if not cache_exists:
        if _load_disk_cache():
            with _cache_lock:
                age = (now - _jobs_cache_timestamp).total_seconds() if _jobs_cache_timestamp else 9999
            if age >= CACHE_FRESH_SECONDS:
                _trigger_background_refresh()
            return _jobs_cache

    # 4. Cold start without disk cache: fetch once and cache
    fresh_jobs = fetch_jobs_from_notion()
    if fresh_jobs:
        _update_cache(fresh_jobs, save_disk=True)

    return _jobs_cache


# Initialize disk cache on module load for instant first response
try:
    _load_disk_cache()
except Exception:
    pass


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/jobs', methods=['GET'])
def api_jobs():
    """Get jobs with optional filtering (domains, search, location, level) and pagination."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        domain = request.args.get('domain', '').strip()
        domains_param = request.args.get('domains', '').strip()
        search = request.args.get('search', '').strip()
        location = request.args.get('location', '').strip()
        level = request.args.get('level', '').strip()
        force_refresh = request.args.get('refresh', '').lower() == 'true'

        jobs = get_jobs(force_refresh=force_refresh)

        # Apply domain filter(s) — multi-select support (comma-separated `domains`)
        # plus backward-compatible single `domain` param
        selected_domains = [d.strip() for d in domains_param.split(',') if d.strip()]
        if domain and domain != "All":
            if domain.lower() not in [d.lower() for d in selected_domains]:
                selected_domains.append(domain)

        if selected_domains and "all" not in [d.lower() for d in selected_domains]:
            domains_lower = {d.lower() for d in selected_domains}
            jobs = [
                j for j in jobs
                if j.get("_domain_lower", j.get("domain", "").lower()) in domains_lower
            ]

        # Apply location filter
        if location:
            location_lower = location.lower().strip()
            jobs = [
                j for j in jobs
                if location_lower in j.get("_location_lower", j.get("location", "").lower())
            ]

        # Apply experience level filter
        if level:
            level_lower = level.lower().strip()
            jobs = [
                j for j in jobs
                if j.get("_level_lower", j.get("level", "").lower()) == level_lower
            ]

        # Apply search filter (optimized against pre-indexed lower-cased text)
        if search:
            search_lower = search.lower()
            jobs = [
                j for j in jobs
                if search_lower in j.get("_search_text", f"{j.get('role','')} {j.get('company','')} {j.get('location','')}".lower())
            ]

        # Calculate pagination
        total = len(jobs)
        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        start = (page - 1) * limit
        end = start + limit
        paginated_jobs = jobs[start:end] if start < total else []

        # Return clean jobs without internal _ keys
        clean_paginated = []
        for j in paginated_jobs:
            clean_paginated.append({k: v for k, v in j.items() if not k.startswith("_")})

        response_data = {
            "success": True,
            "jobs": clean_paginated,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            }
        }

        # Optional metadata inclusion to reduce initial round-trips
        if request.args.get('include_meta', '').lower() == 'true':
            with _cache_lock:
                response_data["stats"] = _jobs_stats_cache
                response_data["locations"] = _jobs_locations_cache

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get dashboard statistics (instant O(1) response from pre-aggregated cache)."""
    try:
        get_jobs()  # Ensure cache is initialized / background refreshed if stale
        with _cache_lock:
            stats = _jobs_stats_cache

        if stats is None:
            stats, _ = _compute_aggregations(_jobs_cache)

        return jsonify({
            "success": True,
            "stats": stats
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/domains', methods=['GET'])
def api_domains():
    """Get list of available role domain tags."""
    return jsonify({
        "success": True,
        "domains": [
            "All",
            "Software Engineer",
            "Data Analyst",
            "Data Engineer",
            "Data Science",
            "ML Engineer",
            "DevOps & Cloud",
            "QA & Testing",
            "Security",
            "Support",
            "Operations",
            "Marketing",
            "UI/UX",
            "Product",
            "Founders Office",
        ]
    })


@app.route('/api/levels', methods=['GET'])
def api_levels():
    """Get list of available experience levels."""
    return jsonify({
        "success": True,
        "levels": ["Entry Level", "Mid Level", "Senior Level"]
    })


@app.route('/api/locations', methods=['GET'])
def api_locations():
    """Get unique locations from all jobs (instant O(1) response from pre-aggregated cache)."""
    try:
        get_jobs()  # Ensure cache is initialized / background refreshed if stale
        with _cache_lock:
            locations = _jobs_locations_cache

        if locations is None:
            _, locations = _compute_aggregations(_jobs_cache)

        return jsonify({
            "success": True,
            "locations": locations or []
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    with _cache_lock:
        cache_count = len(_jobs_cache)
        cache_ts = _jobs_cache_timestamp.isoformat() if _jobs_cache_timestamp else None

    return jsonify({
        "status": "healthy",
        "source": "notion",
        "cached_jobs": cache_count,
        "cache_timestamp": cache_ts
    })


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Force refresh the jobs cache from Notion."""
    try:
        jobs = get_jobs(force_refresh=True)
        return jsonify({
            "success": True,
            "message": f"Refreshed {len(jobs)} jobs from Notion",
            "count": len(jobs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/debug', methods=['GET'])
def api_debug():
    """Diagnostic endpoint to check Notion configuration."""
    result = {
        "env_vars_set": {
            "NOTION_API_KEY": bool(NOTION_API_KEY),
            "NOTION_DATABASE_ID": bool(NOTION_DATABASE_ID),
        },
        "api_key_prefix": NOTION_API_KEY[:10] + "..." if NOTION_API_KEY else "NOT SET",
        "database_id": NOTION_DATABASE_ID or "NOT SET",
        "notion_connection": False,
        "notion_error": None,
    }

    if NOTION_API_KEY and NOTION_DATABASE_ID:
        try:
            # Try to retrieve database info
            db_info = _notion_request("GET", f"databases/{NOTION_DATABASE_ID}")
            title = db_info.get("title", [{}])
            db_title = title[0].get("plain_text", "Untitled") if title else "Untitled"
            props = db_info.get("properties", {})
            result["notion_connection"] = True
            result["database_title"] = db_title
            result["database_properties"] = list(props.keys())

            # Try a query
            test_query = _notion_request("POST", f"databases/{NOTION_DATABASE_ID}/query", {"page_size": 5})
            result["sample_count"] = len(test_query.get("results", []))
            result["has_more"] = test_query.get("has_more", False)

        except ImportError as e:
            result["notion_error"] = f"notion_client not installed: {e}"
        except Exception as e:
            result["notion_error"] = str(e)[:200]
    else:
        result["notion_error"] = "Missing environment variables"

    return jsonify(result)


# ============================================================================
# RESUME - LaTeX Editor
# ============================================================================

_default_resume_source = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}


%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}


\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%


\begin{document}

%----------HEADING----------
% \begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
%   \textbf{\href{http://sourabhbajaj.com/}{\Large Sourabh Bajaj}} & Email : \href{mailto:sourabh@sourabhbajaj.com}{sourabh@sourabhbajaj.com}\\
%   \href{http://sourabhbajaj.com/}{http://www.sourabhbajaj.com} & Mobile : +1-123-456-7890 \\
% \end{tabular*}

\begin{center}
    \textbf{\Huge \scshape Jake Ryan} \\ \vspace{1pt}
    \small 123-456-7890 $|$ \href{mailto:x@x.com}{\underline{jake@su.edu}} $|$ 
    \href{https://linkedin.com/in/...}{\underline{linkedin.com/in/jake}} $|$
    \href{https://github.com/...}{\underline{github.com/jake}}
\end{center}


%-----------EDUCATION-----------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Southwestern University}{Georgetown, TX}
      {Bachelor of Arts in Computer Science, Minor in Business}{Aug. 2018 -- May 2021}
    \resumeSubheading
      {Blinn College}{Bryan, TX}
      {Associate's in Liberal Arts}{Aug. 2014 -- May 2018}
  \resumeSubHeadingListEnd


%-----------EXPERIENCE-----------
\section{Experience}
  \resumeSubHeadingListStart

    \resumeSubheading
      {Undergraduate Research Assistant}{June 2020 -- Present}
      {Texas A\&M University}{College Station, TX}
      \resumeItemListStart
        \resumeItem{Developed a REST API using FastAPI and PostgreSQL to store data from learning management systems}
        \resumeItem{Developed a full-stack web application using Flask, React, PostgreSQL and Docker to analyze GitHub data}
        \resumeItem{Explored ways to visualize GitHub collaboration in a classroom setting}
      \resumeItemListEnd
      
% -----------Multiple Positions Heading-----------
%    \resumeSubSubheading
%     {Software Engineer I}{Oct 2014 - Sep 2016}
%     \resumeItemListStart
%        \resumeItem{Apache Beam}
%          {Apache Beam is a unified model for defining both batch and streaming data-parallel processing pipelines}
%     \resumeItemListEnd
%    \resumeSubHeadingListEnd
%-------------------------------------------

    \resumeSubheading
      {Information Technology Support Specialist}{Sep. 2018 -- Present}
      {Southwestern University}{Georgetown, TX}
      \resumeItemListStart
        \resumeItem{Communicate with managers to set up campus computers used on campus}
        \resumeItem{Assess and troubleshoot computer problems brought by students, faculty and staff}
        \resumeItem{Maintain upkeep of computers, classroom equipment, and 200 printers across campus}
    \resumeItemListEnd

    \resumeSubheading
      {Artificial Intelligence Research Assistant}{May 2019 -- July 2019}
      {Southwestern University}{Georgetown, TX}
      \resumeItemListStart
        \resumeItem{Explored methods to generate video game dungeons based off of \emph{The Legend of Zelda}}
        \resumeItem{Developed a game in Java to test the generated dungeons}
        \resumeItem{Contributed 50K+ lines of code to an established codebase via Git}
        \resumeItem{Conducted  a human subject study to determine which video game dungeon generation technique is enjoyable}
        \resumeItem{Wrote an 8-page paper and gave multiple presentations on-campus}
        \resumeItem{Presented virtually to the World Conference on Computational Intelligence}
      \resumeItemListEnd

  \resumeSubHeadingListEnd


%-----------PROJECTS-----------
\section{Projects}
    \resumeSubHeadingListStart
      \resumeProjectHeading
          {\textbf{Gitlytics} $|$ \emph{Python, Flask, React, PostgreSQL, Docker}}{June 2020 -- Present}
          \resumeItemListStart
            \resumeItem{Developed a full-stack web application using with Flask serving a REST API with React as the frontend}
            \resumeItem{Implemented GitHub OAuth to get data from user’s repositories}
            \resumeItem{Visualized GitHub data to show collaboration}
            \resumeItem{Used Celery and Redis for asynchronous tasks}
          \resumeItemListEnd
      \resumeProjectHeading
          {\textbf{Simple Paintball} $|$ \emph{Spigot API, Java, Maven, TravisCI, Git}}{May 2018 -- May 2020}
          \resumeItemListStart
            \resumeItem{Developed a Minecraft server plugin to entertain kids during free time for a previous job}
            \resumeItem{Published plugin to websites gaining 2K+ downloads and an average 4.5/5-star review}
            \resumeItem{Implemented continuous delivery using TravisCI to build the plugin upon new a release}
            \resumeItem{Collaborated with Minecraft server administrators to suggest features and get feedback about the plugin}
          \resumeItemListEnd
    \resumeSubHeadingListEnd



%
%-----------PROGRAMMING SKILLS-----------
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Languages}{: Java, Python, C/C++, SQL (Postgres), JavaScript, HTML/CSS, R} \\
     \textbf{Frameworks}{: React, Node.js, Flask, JUnit, WordPress, Material-UI, FastAPI} \\
     \textbf{Developer Tools}{: Git, Docker, TravisCI, Google Cloud Platform, VS Code, Visual Studio, PyCharm, IntelliJ, Eclipse} \\
     \textbf{Libraries}{: pandas, NumPy, Matplotlib}
    }}
 \end{itemize}


%-------------------------------------------
\end{document}"""

DEFAULT_LATEX_SOURCE = Path(__file__).parent.parent / "Latex resume" / "resume-jake" / "resume.tex"
if DEFAULT_LATEX_SOURCE.exists():
    try:
        with open(DEFAULT_LATEX_SOURCE, "r", encoding="utf-8") as f:
            _default_resume_source = f.read()
    except Exception:
        pass

_sourabh_resume_source = r"""\documentclass[letterpaper,11pt]{article}

\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}

\pagestyle{fancy}
\fancyhf{} % Clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generated PDF is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands
\newcommand{\resumeItem}[2]{
  \item\small{
    \textbf{#1}{: #2 \vspace{-2pt}}
  }
}

% Just in case someone needs a heading that does not need to be in a list
\newcommand{\resumeHeading}[4]{
    \begin{tabular*}{0.99\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small #3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small #3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small #1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeItemPlain}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubItem}[2]{\resumeItem{#1}{#2}\vspace{-4pt}}

\renewcommand{\labelitemii}{$\circ$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  CV STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%


\begin{document}

%----------HEADING-----------------
\begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
  \textbf{\href{https://sourabhbajaj.com/}{\Large Sourabh Bajaj}} & Email: \href{mailto:sourabh@sourabhbajaj.com}{sourabh@sourabhbajaj.com}\\
  \href{https://sourabhbajaj.com/}{sourabhbajaj.com} & Mobile: \href{tel:+11234567890}{+1-123-456-7890} \\
\end{tabular*}


%-----------EDUCATION-----------------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Georgia Institute of Technology}{Atlanta, GA}
      {Master of Science in Computer Science; GPA: 4.00}{Aug 2012 -- Dec 2013}
    \resumeSubheading
      {Birla Institute of Technology and Science}{Pilani, India}
      {Bachelor of Engineering in Electrical and Electronics; GPA: 3.66 (9.15/10.0)}{Aug 2008 -- July 2012}
  \resumeSubHeadingListEnd


%-----------EXPERIENCE-----------------
\section{Experience}
  \resumeSubHeadingListStart

    \resumeSubheading
      {Google}{Mountain View, CA}
      {Software Engineer}{Oct 2016 -- Present}
      \resumeItemListStart
        \resumeItem{TensorFlow}
          {TensorFlow is an open source software library for numerical computation using data flow graphs; primarily used for training deep learning models. Worked on APIs and performance for training models on Tensor Processing Units (TPU).}
        \resumeItem{Apache Beam}
          {Apache Beam is a unified model for defining both batch and streaming data-parallel processing pipelines, as well as a set of language-specific SDKs for constructing pipelines and runners.}
      \resumeItemListEnd
      
% --------Multiple Positions Heading------------
  %  \resumeSubSubheading
  %   {Software Engineer I}{Oct 2014 -- Sep 2016}
  %   \resumeItemListStart
  %      \resumeItem{Apache Beam}
  %        {Apache Beam is a unified model for defining both batch and streaming data-parallel processing pipelines}
  %   \resumeItemListEnd

%-------------------------------------------

    \resumeSubheading
      {Coursera}{Mountain View, CA}
      {Senior Software Engineer}{Jan 2014 -- Oct 2016}
      \resumeItemListStart
        \resumeItem{Notifications}
          {Service for sending email, push and in-app notifications. Involved in features such as delivery time optimization, tracking, queuing and A/B testing. Built an internal app to run batch campaigns for marketing, etc.}
        \resumeItem{Nostos}
          {Bulk data processing and injection service from Hadoop to Cassandra and provides a thin REST layer on top for serving offline computed data online.}
        \resumeItem{Workflows}
          {Dataduct an open source workflow framework to create and manage data pipelines leveraging reusable patterns to expedite developer productivity.}
        \resumeItem{Data Collection}
          {Designed the internal survey and crowdsourcing platform which allowed for creating various tasks for crowdsourcing or embedding surveys across the Coursera platform.}
        \resumeItem{Dev Environment}
          {Analytics environment based on Docker and AWS, standardized the Python and R dependencies. Wrote the core libraries that are shared by all data scientists.}
        \resumeItem{Data Warehousing}
          {Setup, schema design and management of Amazon Redshift. Built an internal app for access to the data using a web interface. Dataduct integration for daily ETL injection into Redshift.}
        \resumeItem{Recommendations}
          {Core service for all recommendation systems at Coursera, currently used on the homepage and throughout the content discovery process. Worked on both offline training and online serving.}
        \resumeItem{Content Discovery}
          {Improved content discovery by building a new onboarding experience on Coursera. Used this to personalize the search and browse experience. Also worked on ranking and indexing improvements.}
        \resumeItem{Course Dashboards}
          {Instructor dashboards and learner surveying tools, which helped instructors run their class better by providing data on Assignments and Learner Activity.}
      \resumeItemListEnd

    \resumeSubheading
      {Lucena Research}{Atlanta, GA}
      {Data Scientist}{Summer 2012 and 2013}
      \resumeItemListStart
        \resumeItem{Portfolio Management}
          {Created models for portfolio hedging, portfolio optimization and price forecasting. Also created a strategy backtesting engine used for simulating and backtesting strategies.}
        \resumeItem{QuantDesk}
          {Python backend for a web application used by hedge fund managers for portfolio management.}
      \resumeItemListEnd

    \resumeSubheading
      {Georgia Institute of Technology}{Atlanta, GA}
      {Research and Teaching Assistant}{Jan 2012 -- Dec 2013}
      \resumeItemListStart
        \resumeItem{Research Assistant -- Machine Learning}
          {Research on machine learning for portfolio hedging and replication algorithms. Modeling low-risk \& continuous-return strategies. Developed the Python library QSTK.}
        \resumeItem{Teaching Assistant -- Computational Investing}
          {The online course on Coursera, had more than 100,000 students enrolled. It was featured on the 11 Alive News and the Atlanta Journal Constitution. Involved in creating assignments, exams and conducting recitation sessions. Also taught the on-campus version of the course.}
      \resumeItemListEnd

  \resumeSubHeadingListEnd


%-----------PROJECTS-----------------
\section{Projects}
  \resumeSubHeadingListStart
    \resumeSubItem{QuantSoftware Toolkit}
      {Open source Python library for financial data analysis and machine learning for finance.}
    \resumeSubItem{GitHub Visualization}
      {Data visualization of Git log data using D3 to analyze project trends over time.}
    \resumeSubItem{Recommendation System}
      {Music and movie recommender systems using collaborative filtering on public datasets.}
    \resumeSubItem{Mac Setup}
      {Book that gives step-by-step instructions on setting up developer environment on macOS.}
  \resumeSubHeadingListEnd

%
%--------SKILLS------------
%\section{Skills}
%  \resumeSubHeadingListStart
%    \item{
%      \textbf{Languages}{: Scala, Python, JavaScript, C++, SQL, Java}
%      \hfill
%      \textbf{Technologies}{: AWS, Play, React, Kafka, GCE}
%    }
%  \resumeSubHeadingListEnd


%-------------------------------------------
\end{document}"""

DEFAULT_SOURABH_SOURCE = Path(__file__).parent.parent / "Latex resume" / "resume-master" / "sourabh_bajaj_resume.tex"
if DEFAULT_SOURABH_SOURCE.exists():
    try:
        with open(DEFAULT_SOURABH_SOURCE, "r", encoding="utf-8") as f:
            _sourabh_resume_source = f.read()
    except Exception:
        pass


_pratul_resume_source = r"""\documentclass[a4paper,20pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[pdftex]{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.530in}
\addtolength{\evensidemargin}{-0.375in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.45in}
\addtolength{\textheight}{1in}

\urlstyle{rm}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlength{\footskip}{4pt}

% Sections formatting
\titleformat{\section}{
  \vspace{-10pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-6pt}]

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    #1 \vspace{-2pt}
  }
}

\newcommand{\resumeItemWithoutTitle}[1]{
  \item\small{
    {\vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{#3} & \textit{#4} \\
    \end{tabular*}
}

\newcommand{\resumeSubSubheading}[1]{
  \vspace{-1pt}
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{#1} \\
    \end{tabular*}\vspace{-5pt}
}


\newcommand{\resumeSubItem}[2]{
  \begin{tabular*}{\textwidth}{@{}p{3cm}@{\extracolsep{\fill}}p{15cm}@{}}
    #1 & #2 \\
  \end{tabular*}
}

\renewcommand{\labelitemii}{$\circ$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeSkillsListStart}{}
\newcommand{\resumeSkillsListEnd}{\vspace{-5pt}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-----------------------------
%%%%%%  CV STARTS HERE  %%%%%%

\begin{document}

%----------HEADING-----------------
\begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
  \textbf{{\LARGE Pratul Muthuraja}} & Email: \href{mailto:pratulmuthuraja@gmail.com}{pratulmuthuraja@gmail.com}\\
  \href{https://pratulmuthuraja.com}{Portfolio: pratulmuthuraja.com} & Mobile:~~~+91 8489468800 \\
  \href{https://github.com/pratulmuthuraja}{Github: ~~github.com/pratulmuthuraja} \\
\end{tabular*}

%-----------EDUCATION-----------------
% \section{Summary}
% {
% Full-stack developer with expertise in React, Node.js, Python, Docker, and Kubernetes to automate infrastructure and create scalable, high-performance web apps and a proven track record of producing clean, maintainable solutions across tech stacks, emphasizing  reliability and observability. Looking for Full-stack Developer and Software Engineer  positions.}

%-----------EDUCATION-----------------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Illinois Insitute of Technology}{Chicago, USA}
      {Master of Computer Science}{January 2021 - May 2023}
      % {\scriptsize \textit{ \footnotesize{\newline{}\textbf{Courses:} Big Data, Cloud Computing, Software Engineering, Virtual Machines}}}
    \vspace{-5pt}
    \resumeSubheading
      {Anna University}{Chennai, India}
      {Bachelor of Engineering in Computer Science}{June 2014 - May 2018}
      % {\scriptsize \textit{ \footnotesize{\newline{}\textbf{Courses:} Operating Systems, Data Structures, Analysis Of Algorithms, Networking, Databases}}}
    \resumeSubHeadingListEnd
\vspace{-12pt}
\section{Skills}
    \resumeSkillsListStart
	\resumeSubItem{Languages}{Python, Go, JavaScript, Java, SQL, Bash, HTML/CSS, Markdown}
	\resumeSubItem{Frameworks}{Django, Flask, ReactJS, NodeJS, LAMP}
	\resumeSubItem{Tools}{Kubernetes, Docker, GIT, PostgreSQL, MySQL, SQLite, MongoDB, NGINX, Helm, Gatsby, Hugo, Jenkins, ChatGPT, ElasticSearch, Grafana, Loki, Ceph, Prometheus, Ansible}
	\resumeSubItem{Platforms}{Linux, Web, Mac, AWS, GCP}
	\resumeSubItem{Soft Skills}{Leadership, Event Management, Writing, Public Speaking, Time Management}

\resumeSkillsListEnd

\vspace{-5pt}
\section{Experience}
  \resumeSubHeadingListStart
    \resumeSubheading{Eastri (Khwaaish AI)}{Mumbai, Remote}
    {System Engineer}{October 2025 - January 2026}
    \resumeItemListStart
        \resumeItem{}
          {Architected a scalable AWS infrastructure supporting 100K+ users using EC2, EKS, S3, and CloudFront to ensure high availability and low-latency content delivery.}
        \resumeItem{}
          {Design high-level system architecture and workflow diagrams to define service interactions, data flow, and deployment topology.}
        \resumeItem{Performed AWS cost estimation and capacity planning, forecasting infrastructure spend and optimizing resource allocation.}
      \resumeItemListEnd
    \resumeSubheading{Armour Chapter of Triangle}{Chicago, USA}
    {Full-Stack Developer}{November 2023 - November 2024}
    \resumeSubSubheading{Organization Website}
    \resumeItemListStart
        \resumeItem{\textbf{Tech Stack:} React.js, Nodejs, Javascript, TailwindCSS, PostgreSQL.}
        \resumeItem{}
          {Built a full-stack web application to securely manage social and event data for over 200K members.}
        \resumeItem{}
          {Overhauled backend architecture, optimizing database queries and caching strategies to bring API response times under 100ms and reducing latency by 80\% while cutting operational costs by 60\%.}
        \resumeItem{}
          {Design and implement event-driven batch jobs for real-time notifications and automated task scheduling, improving engagement and workflow efficiency by 25\%.}
        \resumeItem{}
          {Led UI/UX development, working closely with stakeholders to create Figma wireframes and translating them into a highly responsive React frontend improving load speeds by up to 40\%.}
        \resumeItem{}
          {Improved system reliability to 99.99\% uptime by setting up load balancing, auto-scaling, failover mechanisms, and database replication, minimizing downtime and ensuring high availability.}
      \resumeItemListEnd
    \resumeSubSubheading{Private Cloud Infrastructure for Scalable EdTech Delivery}
    \resumeItemListStart
        \resumeItem{\textbf{Tech Stack:} Proxmox VE, Ceph, Kubernetes (k3s), Terraform, Ansible, ArgoCD, Helm, Prometheus, Grafana, Loki, Alertmanager, OpenTelemetry, Vault, WireGuard, Cosign, Trivy}
        \resumeItem{}{Set up a 3-node Proxmox VE cluster with Ceph storage to run a containerized EdTech platform supporting video lessons and interactive training modules supporting 2K+ concurrent users streaming over 8TB monthly.}
        \resumeItem{}{Built a CI/CD pipeline using Terraform, Ansible, ArgoCD, Helm, and k3s to streamline deployments of new course content and platform features reducing deployment time by 70\%.}
        \resumeItem{}{Rolled out a full observability stack with Prometheus, Grafana, Loki, and OpenTelemetry to keep tabs on system health for over 200 services and handle high traffic during academic peaks.}
        \resumeItem{}{Locked down access for instructors and developers with Vault for secrets management and WireGuard for secure, remote connectivity decreasing incidents by 100\%.}
        \resumeItem{}{Brought hosting costs down by 60\% while maintaining 99.99\% uptime, freeing up budget for content and engagement initiatives.}
      \resumeItemListEnd
    \resumeSubSubheading{Internal Student Grievance \& Feedback Portal}
    \resumeItemListStart
        \resumeItem{\textbf{Tech Stack:} React.js, Node.js, PostgreSQL, TailwindCSS, Framer Motion, Jest.}
        \resumeItem{}{Led end-to-end development of a secure feedback and grievance portal for university students, enabling real-time issue tracking and reducing resolution time by 40\% through streamlined departmental workflows.}
        \resumeItem{}{Designed and deployed a role-based web platform using React.js, Node.js, and PostgreSQL, with full support for anonymity, notifications, and searchable case history for admins and faculty improving response rate by 35\% and consequently increase engagement by 25\%.}
      \resumeItemListEnd

    \resumeSubheading
		{Illinois Institute of Technology}{Chicago, USA}
		{Graduate Student Ambassador}{August 2021 -  December 2022}\vspace{-5pt}
		\resumeItemListStart
        \resumeItem{Managed databases and generated reports on Salesforce; Analyzed prospective student data to improve response to Graduate Discover Day event resulting in 19\% growth of incoming graduate students compared to 2020.}
        \resumeItem{Strong leadership and collaboration skills evidenced by organizing recruitment activities through campus tours, student panel, and events for the Graduate Admissions Office showing 37\% better response rate.}
		\resumeItemListEnd

\resumeSubHeadingListEnd

\end{document}"""

DEFAULT_PRATUL_SOURCE = Path(__file__).parent.parent / "Latex resume" / "resume-main" / "resume-main" / "main.tex"
if DEFAULT_PRATUL_SOURCE.exists():
    try:
        with open(DEFAULT_PRATUL_SOURCE, "r", encoding="utf-8") as f:
            _pratul_resume_source = f.read()
    except Exception:
        pass

_faang_resume_source = r"""\documentclass{resume} % Use the custom resume.cls style

\usepackage[left=0.4 in,top=0.4in,right=0.4 in,bottom=0.4in]{geometry} % Document margins
\newcommand{\tab}[1]{\hspace{.2667\textwidth}\rlap{#1}} 
\newcommand{\itab}[1]{\hspace{0em}\rlap{#1}}
\name{Firstname Lastname} % Your name
% You can merge both of these into a single line, if you do not have a website.
\address{+1(123) 456-7890 \\ San Francisco, CA} 
\address{\href{mailto:contact@faangpath.com}{contact@faangpath.com} \\ \href{https://linkedin.com/company/faangpath}{linkedin.com/company/faangpath} \\ \href{www.faangpath.com}{www.faangpath.com}}  %

\begin{document}

%----------------------------------------------------------------------------------------
%	OBJECTIVE
%----------------------------------------------------------------------------------------

\begin{rSection}{OBJECTIVE}

{Software Engineer with 2+ years of experience in XXX, seeking full-time XXX roles.}


\end{rSection}
%----------------------------------------------------------------------------------------
%	EDUCATION SECTION
%----------------------------------------------------------------------------------------

\begin{rSection}{Education}

{\bf Master of Computer Science}, Stanford University \hfill {Expected 2020}\\
Relevant Coursework: A, B, C, and D.

{\bf Bachelor of Computer Science}, Stanford University \hfill {2014 - 2017}
%Minor in Linguistics \smallskip \\
%Member of Eta Kappa Nu \\
%Member of Upsilon Pi Epsilon \\


\end{rSection}

%----------------------------------------------------------------------------------------
% TECHINICAL STRENGTHS	
%----------------------------------------------------------------------------------------
\begin{rSection}{SKILLS}

\begin{tabular}{ @{} >{\bfseries}l @{\hspace{6ex}} l }
Technical Skills & A, B, C, D
\\
Soft Skills & A, B, C, D\\
XYZ & A, B, C, D\\
\end{tabular}\\
\end{rSection}

\begin{rSection}{EXPERIENCE}

\textbf{Role Name} \hfill Jan 2017 - Jan 2019\\
Company Name \hfill \textit{San Francisco, CA}
 \begin{itemize}
    \itemsep -3pt {} 
     \item Achieved X\% growth for XYZ using A, B, and C skills.
     \item Led XYZ which led to X\% of improvement in ABC
    \item Developed XYZ that did A, B, and C using X, Y, and Z. 
 \end{itemize}
 
\textbf{Role Name} \hfill Jan 2017 - Jan 2019\\
Company Name \hfill \textit{San Francisco, CA}
 \begin{itemize}
    \itemsep -3pt {} 
     \item Achieved X\% growth for XYZ using A, B, and C skills.
     \item Led XYZ which led to X\% of improvement in ABC
    \item Developed XYZ that did A, B, and C using X, Y, and Z. 
 \end{itemize}

\end{rSection} 

%----------------------------------------------------------------------------------------
%	WORK EXPERIENCE SECTION
%----------------------------------------------------------------------------------------

\begin{rSection}{PROJECTS}
\vspace{-1.25em}
\item \textbf{Hiring Search Tool.} {Built a tool to search for Hiring Managers and Recruiters by using ReactJS, NodeJS, Firebase and boolean queries. Over 25000 people have used it so far, with 5000+ queries being saved and shared, and search results even better than LinkedIn! \href{https://hiring-search.careerflow.ai/}{(Try it here)}}
\item \textbf{Short Project Title.} {Build a project that does something and had quantified success using A, B, and C. This project's description spans two lines and also won an award.}
\item \textbf{Short Project Title.} {Build a project that does something and had quantified success using A, B, and C. This project's description spans two lines and also won an award.}
\end{rSection} 

%----------------------------------------------------------------------------------------
\begin{rSection}{Extra-Curricular Activities} 
\begin{itemize}
    \item 	Actively write \href{https://www.faangpath.com/blog/}{blog posts} and social media posts (\href{https://www.tiktok.com/@faangpath}{TikTok}, \href{https://www.instagram.com/faangpath/?hl=en}{Instagram}) viewed by over 20K+ job seekers per week to help people with best practices to land their dream jobs. 
    \item	Sample bullet point.
\end{itemize}


\end{rSection}

%----------------------------------------------------------------------------------------
\begin{rSection}{Leadership} 
\begin{itemize}
    \item Admin for the \href{https://discord.com/invite/WWbjEaZ}{FAANGPath Discord community} with over 6000+ job seekers and industry mentors. Actively involved in facilitating online events, career conversations, and more alongside other admins and a team of volunteer moderators! 
\end{itemize}


\end{rSection}


\end{document}"""

DEFAULT_FAANG_SOURCE = Path(__file__).parent.parent / "Latex resume" / "latex-resume-template-main" / "latex-resume-template-main" / "source.tex"
if DEFAULT_FAANG_SOURCE.exists():
    try:
        with open(DEFAULT_FAANG_SOURCE, "r", encoding="utf-8") as f:
            _faang_resume_source = f.read()
    except Exception:
        pass

_resume_cls_source = r"""%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Medium Length Professional CV - RESUME CLASS FILE
%
% This template has been downloaded from:
% http://www.LaTeXTemplates.com
%
% This class file defines the structure and design of the template. 
%
% Original header:
% Copyright (C) 2010 by Trey Hunner
%
% Copying and distribution of this file, with or without modification,
% are permitted in any medium without royalty provided the copyright
% notice and this notice are preserved. This file is offered as-is,
% without any warranty.
%
% Created by Trey Hunner and modified by www.LaTeXTemplates.com
%
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\ProvidesClass{resume}[2010/07/10 v0.9 Resume class]

\LoadClass[11pt,letterpaper]{article} % Font size and paper type

\usepackage[parfill]{parskip} % Remove paragraph indentation
\usepackage{array} % Required for boldface (\bf and \bfseries) tabular columns
\usepackage{ifthen} % Required for ifthenelse statements

\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=blue,
}

\pagestyle{empty} % Suppress page numbers

%----------------------------------------------------------------------------------------
%	HEADINGS COMMANDS: Commands for printing name and address
%----------------------------------------------------------------------------------------

\def \name#1{\def\@name{#1}} % Defines the \name command to set name
\def \@name {} % Sets \@name to empty by default

\def \addressSep {$\diamond$} % Set default address separator to a diamond

% One, two or three address lines can be specified 
\let \@addressone \relax
\let \@addresstwo \relax
\let \@addressthree \relax

% \address command can be used to set the first, second, and third address (last 2 optional)
\def \address #1{
  \@ifundefined{@addresstwo}{
    \def \@addresstwo {#1}
  }{
  \@ifundefined{@addressthree}{
  \def \@addressthree {#1}
  }{
     \def \@addressone {#1}
  }}
}

% \printaddress is used to style an address line (given as input)
\def \printaddress #1{
  \begingroup
    \def \\ {\addressSep\ }
    \centerline{#1}
  \endgroup
  \par
  \addressskip
}

% \printname is used to print the name as a page header
\def \printname {
  \begingroup
    \hfil{\MakeUppercase{\namesize\bf \@name}}\hfil
    \nameskip\break
  \endgroup
}

%----------------------------------------------------------------------------------------
%	PRINT THE HEADING LINES
%----------------------------------------------------------------------------------------

\let\ori@document=\document
\renewcommand{\document}{
  \ori@document  % Begin document
  \printname % Print the name specified with \name
  \@ifundefined{@addressone}{}{ % Print the first address if specified
    \printaddress{\@addressone}}
  \@ifundefined{@addresstwo}{}{ % Print the second address if specified
    \printaddress{\@addresstwo}}
     \@ifundefined{@addressthree}{}{ % Print the third address if specified
    \printaddress{\@addressthree}}
}

%----------------------------------------------------------------------------------------
%	SECTION FORMATTING
%----------------------------------------------------------------------------------------

% Defines the rSection environment for the large sections within the CV
\newenvironment{rSection}[1]{ % 1 input argument - section name
  \sectionskip
  \MakeUppercase{{\bf #1}} % Section title
  \sectionlineskip
  \hrule % Horizontal line
  \begin{list}{}{ % List for each individual item in the section
    \setlength{\leftmargin}{0em} % Margin within the section
  }
  \item[]
}{
  \end{list}
}

%----------------------------------------------------------------------------------------
%	WORK EXPERIENCE FORMATTING
%----------------------------------------------------------------------------------------

\newenvironment{rSubsection}[4]{ % 4 input arguments - company name, year(s) employed, job title and location
 {\bf #1} \hfill {#2} % Bold company name and date on the right
 \ifthenelse{\equal{#3}{}}{}{ % If the third argument is not specified, don't print the job title and location line
  \\
  {\em #3} \hfill {\em #4} % Italic job title and location
  }\smallskip
  \begin{list}{$\cdot$}{\leftmargin=0em} % \cdot used for bullets, no indentation
   \itemsep -0.5em \vspace{-0.5em} % Compress items in list together for aesthetics
  }{
  \end{list}
  \vspace{0.5em} % Some space after the list of bullet points
}

% The below commands define the whitespace after certain things in the document - they can be \smallskip, \medskip or \bigskip
\def\namesize{\LARGE} % Size of the name at the top of the document
\def\addressskip{\smallskip} % The space between the two address (or phone/email) lines
\def\sectionlineskip{\medskip} % The space above the horizontal line for each section 
\def\nameskip{\medskip} % The space after your name at the top
\def\sectionskip{\medskip} % The space after the heading section
"""

DEFAULT_RESUME_CLS = Path(__file__).parent.parent / "Latex resume" / "latex-resume-template-main" / "latex-resume-template-main" / "resume.cls"
if DEFAULT_RESUME_CLS.exists():
    try:
        with open(DEFAULT_RESUME_CLS, "r", encoding="utf-8") as f:
            _resume_cls_source = f.read()
    except Exception:
        pass




def _find_pdflatex():
    """Try to find pdflatex executable in PATH or common locations."""
    # Check PATH first
    try:
        result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return "pdflatex"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Common Windows install locations
    common_paths = [
        "C:\\Program Files\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe",
        "C:\\Program Files (x86)\\MiKTeX\\miktex\\bin\\pdflatex.exe",
        "C:\\Program Files\\MiKTeX\\texmfs\\install\\miktex\\bin\\x64\\pdflatex.exe",
        os.path.expanduser("~\\AppData\\Local\\Programs\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe"),
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path

    return None


def _configure_miktex():
    """Configure MiKTeX to auto-install missing packages."""
    pdflatex_path = _find_pdflatex()
    if not pdflatex_path:
        return

    miktex_dir = os.path.dirname(pdflatex_path)
    initexmf = os.path.join(miktex_dir, "initexmf.exe")
    if os.path.isfile(initexmf):
        try:
            subprocess.run(
                [initexmf, "--set-config-value", "[MPM]AutoInstall=1"],
                capture_output=True, timeout=30
            )
        except Exception:
            pass


# Run MiKTeX configuration once at import time
_configure_miktex()


def _compile_latex_local(latex_source, output_dir):
    """Compile LaTeX locally using pdflatex."""
    pdflatex_path = _find_pdflatex()
    if not pdflatex_path:
        return None, "pdflatex not found. Install MiKTeX or restart after installation."

    tex_path = os.path.join(output_dir, "resume.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_source)

    if "documentclass{resume}" in latex_source.replace(" ", "") or "documentclass[11pt]{resume}" in latex_source.replace(" ", "") or "documentclass[10pt]{resume}" in latex_source.replace(" ", "") or "documentclass[12pt]{resume}" in latex_source.replace(" ", ""):
        cls_path = os.path.join(output_dir, "resume.cls")
        with open(cls_path, "w", encoding="utf-8") as f:
            f.write(_resume_cls_source)

    try:
        _is_miktex = "miktex" in pdflatex_path.lower() if pdflatex_path else False

        base_cmd = [
            pdflatex_path,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory", output_dir,
            tex_path
        ]

        if _is_miktex:
            base_cmd.insert(-1, "--enable-installer")

        for i in range(2):
            timeout = 300 if i == 0 else 120
            try:
                subprocess.run(
                    base_cmd, capture_output=True, text=True, timeout=timeout, cwd=output_dir
                )
                pdf_path = os.path.join(output_dir, "resume.pdf")
                if os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 100:
                    return pdf_path, None
            except subprocess.TimeoutExpired:
                if i == 0:
                    continue
                return None, "LaTeX compilation timed out."

        pdf_path = os.path.join(output_dir, "resume.pdf")
        if os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 100:
            return pdf_path, None

        log_path = os.path.join(output_dir, "resume.log")
        error_msg = "LaTeX compilation failed. Check your syntax."
        if os.path.isfile(log_path):
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()
                errors = re.findall(r"! (.*?)\n", log_content, re.MULTILINE)
                if errors:
                    error_msg = "LaTeX error: " + errors[0][:300]
        return None, error_msg

    except Exception as e:
        return None, f"Compilation error: {str(e)}"


def _compile_latex_online(latex_source):
    """Compile LaTeX using texlive.net API."""
    if not REQUESTS_AVAILABLE:
        return None, "'requests' library not available."

    try:
        files = [
            ('filecontents[]', ('document.tex', latex_source, 'text/plain')),
            ('filename[]', (None, 'document.tex')),
        ]
        if "documentclass{resume}" in latex_source.replace(" ", "") or "documentclass[11pt]{resume}" in latex_source.replace(" ", "") or "documentclass[10pt]{resume}" in latex_source.replace(" ", "") or "documentclass[12pt]{resume}" in latex_source.replace(" ", ""):
            files.extend([
                ('filecontents[]', ('resume.cls', _resume_cls_source, 'text/plain')),
                ('filename[]', (None, 'resume.cls')),
            ])
        data = {
            'engine': 'pdflatex',
            'return': 'pdf'
        }

        response = requests_lib.post(
            "https://texlive.net/cgi-bin/latexcgi",
            files=files,
            data=data,
            timeout=120
        )

        if response.status_code == 200 and len(response.content) > 500:
            if response.content[:4] == b"%PDF":
                pdf_path = os.path.join(tempfile.gettempdir(), f"resume_{uuid.uuid4().hex}.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                return pdf_path, None

        content_type = response.headers.get("content-type", "")
        if "html" in content_type.lower():
            return None, "Online compilation failed. Check your LaTeX syntax."
        return None, f"Online compilation failed: {response.text[:300]}"


    except requests_lib.exceptions.Timeout:
        return None, "Online compilation timed out."
    except requests_lib.exceptions.ConnectionError:
        return None, "Could not reach the online compiler."
    except Exception as e:
        return None, f"Online compilation error: {str(e)}"


@app.route('/resume')
def resume_editor():
    """Resume LaTeX editor page."""
    return render_template('resume.html')


@app.route('/api/latex/build', methods=['POST'])
def api_latex_build():
    """Compile LaTeX source to PDF and return it."""
    try:
        data = request.get_json(force=True)
        latex_source = data.get("latex_source", "")

        if not latex_source or len(latex_source.strip()) < 10:
            return jsonify({"success": False, "error": "LaTeX source is too short or empty"}), 400

        output_dir = tempfile.mkdtemp(prefix="resume_compile_")

        pdf_path, error = _compile_latex_local(latex_source, output_dir)

        if pdf_path is None:
            pdf_path, error = _compile_latex_online(latex_source)

        if pdf_path is None:
            return jsonify({"success": False, "error": error}), 400

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        try:
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
            if pdf_path.startswith(tempfile.gettempdir()):
                os.unlink(pdf_path)
        except Exception:
            pass

        return Response(
            pdf_data,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": "inline; filename=resume.pdf",
                "Content-Length": str(len(pdf_data)),
                "Cache-Control": "no-cache"
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/latex/template', methods=['GET'])
def api_latex_template():
    """Get the default LaTeX source for a specific template."""
    template = request.args.get('template', 'jake').lower()

    if template == 'sourabh':
        source = _sourabh_resume_source
    elif template == 'pratul':
        source = _pratul_resume_source
    elif template == 'faang':
        source = _faang_resume_source
    else:
        source = _default_resume_source  # Jake's template

    return jsonify({
        "success": True,
        "latex_source": source
    })



@app.route('/api/latex/status', methods=['GET'])
def api_latex_status():
    """Check if pdflatex is available locally."""
    pdflatex_path = _find_pdflatex()
    return jsonify({
        "local_available": pdflatex_path is not None,
        "online_available": REQUESTS_AVAILABLE,
        "pdflatex_path": pdflatex_path
    })


# ============================================================================
# RESUME - AI Generation via OpenRouter
# ============================================================================

# Load the Jake's template for the AI prompt
_RESUME_TEMPLATE_PATH = Path(__file__).parent.parent / "Latex resume" / "resume-jake" / "resume.tex"
if _RESUME_TEMPLATE_PATH.exists():
    with open(_RESUME_TEMPLATE_PATH, "r") as f:
        _latex_template_reference = f.read()
else:
    _latex_template_reference = _default_resume_source

# The system prompt for the AI - tells it how to convert plain text to LaTeX
_AI_RESUME_SYSTEM_PROMPT = """You are an expert LaTeX resume generator. Your task is to convert plain text resume content into a properly formatted LaTeX document using the Jake's Resume template.

## TEMPLATE STRUCTURE (use these exact LaTeX commands):
The template uses these custom commands - you MUST use them:

1. HEADER: \\\\begin{{center}} block with name, phone, email, LinkedIn, GitHub
2. EDUCATION: \\\\section{{Education}} with \\\\resumeSubheading{{School}}{{Location}}{{Degree}}{{Dates}}
3. EXPERIENCE: \\\\section{{Experience}} with \\\\resumeSubheading{{JobTitle}}{{Dates}}{{Company}}{{Location}} then \\\\resumeItemListStart and \\\\resumeItem{{text}} for each bullet
4. PROJECTS: \\\\section{{Projects}} with \\\\resumeProjectHeading{{Name $|$ TechStack}}{{Dates}} then \\\\resumeItemListStart / \\\\resumeItem
5. TECHNICAL SKILLS: \\\\section{{Technical Skills}} with \\\\begin{{itemize}} using \\\\textbf{{Category}}{{: items}}

## RULES (strict - follow every one):
1. KEEP the EXACT preamble (everything before \\\\begin{{document}}) - do NOT modify or remove any packages or macros
2. ONLY modify the content between \\\\begin{{document}} and \\\\end{{document}}
3. Parse the user's plain text resume and extract these fields:
   - Name and Contact Info (phone, email, LinkedIn URL, GitHub URL)
   - Education entries (school, degree, dates, location)
   - Experience entries (company, job title, dates, location, bullet points)
   - Projects (name, tech stack, dates, description)
   - Technical Skills (languages, frameworks, tools, libraries)
4. Use \\\\href{{url}}{{text}} for all links (email, LinkedIn, GitHub)
5. Use \\\\textbf for job titles and company names in the Experience section
6. Use \\\\emph for tech stacks and degree names
7. For the Technical Skills section, use \\\\textbf{{Category}}{{: items}} format with \\\\\\\\ for line breaks between categories
8. If a section has no content, OMIT it entirely (don't include empty sections)
9. If the user's text doesn't specify a date, use a reasonable placeholder like "Date"
10. Output ONLY the complete LaTeX code wrapped in ```latex ... ``` code block
11. Do NOT include any explanations, notes, or commentary outside the code block
12. Ensure the output will compile WITHOUT errors - use proper escaping for special characters (&, %, $, #, _, {{, }}, ~, ^)

## EXAMPLE FORMAT (content section only):
\\\\begin{{document}}

\\\\begin{{center}}
    \\\\textbf{{\\\\Huge \\\\scshape John Doe}} \\\\\\\\ \\\\vspace{{1pt}}
    \\\\small +1-123-456-7890 $|$ \\\\href{{mailto:john@example.com}}{{\\\\underline{{john@example.com}}}} $|$
    \\\\href{{https://linkedin.com/in/johndoe}}{{\\\\underline{{linkedin.com/in/johndoe}}}} $|$
    \\\\href{{https://github.com/johndoe}}{{\\\\underline{{github.com/johndoe}}}}
\\\\end{{center}}

\\\\section{{Education}}
  \\\\resumeSubHeadingListStart
    \\\\resumeSubheading
      {{University of Example}}{{City, State}}
      {{Bachelor of Science in Computer Science, Minor in Math}}{{Aug. 2018 -- May 2022}}
  \\\\resumeSubHeadingListEnd

\\\\section{{Experience}}
  \\\\resumeSubHeadingListStart
    \\\\resumeSubheading
      {{Software Engineer}}{{June 2022 -- Present}}
      {{Tech Company Inc.}}{{San Francisco, CA}}
      \\\\resumeItemListStart
        \\\\resumeItem{{Developed REST APIs using Python and Flask serving 10K+ requests/day}}
        \\\\resumeItem{{Built real-time dashboards with React and D3.js for data visualization}}
      \\\\resumeItemListEnd
  \\\\resumeSubHeadingListEnd

\\\\end{{document}}

Now, convert the user's plain text resume below into a properly formatted LaTeX document following ALL of the above rules.
"""


def _call_openrouter(system_prompt, user_content):
    """Call OpenRouter API to generate LaTeX from plain text resume, with fallbacks."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://roleboard.app",
        "X-OpenRouter-Title": "RoleBoard Resume Generator",
    }

    # Build list of models to try in order
    models_to_try = []
    
    # 1. Start with the configured model
    primary_model = OPENROUTER_MODEL or "google/gemma-4-31b-it:free"
    models_to_try.append(primary_model)
    
    # 2. Append the fallback models in order of ranking, avoiding duplicates
    for model in FALLBACK_MODELS:
        if model not in models_to_try:
            models_to_try.append(model)
            
    last_error = None
    
    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }
        
        logging.info(f"Attempting to generate resume using OpenRouter model: {model}")
        
        try:
            response = requests_lib.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            # Check for non-200 responses
            if response.status_code != 200:
                error_detail = response.text[:500]
                last_error = f"Model {model} returned HTTP {response.status_code}: {error_detail}"
                logging.warning(last_error)
                continue
                
            try:
                result = response.json()
            except Exception:
                last_error = f"Model {model} returned invalid JSON: {response.text[:300]}"
                logging.warning(last_error)
                continue
                
            choices = result.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                error_info = result.get("error", {})
                error_msg = error_info.get("message", "No choices returned") if isinstance(error_info, dict) else str(result)[:300]
                last_error = f"Model {model} returned no choices: {error_msg}"
                logging.warning(last_error)
                continue
                
            choice = choices[0]
            if not isinstance(choice, dict):
                last_error = f"Model {model} returned unexpected choice format"
                logging.warning(last_error)
                continue
                
            message = choice.get("message", {})
            if not isinstance(message, dict):
                last_error = f"Model {model} returned unexpected message format"
                logging.warning(last_error)
                continue
                
            content = message.get("content", "")
            if not content or not isinstance(content, str):
                last_error = f"Model {model} returned empty response content"
                logging.warning(last_error)
                continue
                
            # If we got here, we succeeded!
            logging.info(f"Successfully generated resume using model: {model}")
            return content, model
            
        except requests_lib.exceptions.Timeout:
            last_error = f"Model {model} request timed out"
            logging.warning(last_error)
            continue
        except requests_lib.exceptions.ConnectionError:
            last_error = f"Connection error while reaching model {model}"
            logging.warning(last_error)
            continue
        except Exception as e:
            last_error = f"Error with model {model}: {str(e)}"
            logging.warning(last_error)
            continue
            
    # If all models failed, raise the last error encountered
    raise Exception(f"All OpenRouter models failed to generate content. Last error: {last_error}")


def _clean_latex_output(raw_output):
    """Extract LaTeX code from AI output, handling various response formats."""
    if not raw_output or not isinstance(raw_output, str):
        raise Exception("AI returned empty output")

    # Strategy 1: Extract from ```latex ... ``` block
    latex_block = re.search(r"```latex\s*\n?(.*?)```", raw_output, re.DOTALL)
    if latex_block:
        result = latex_block.group(1).strip()
        if "\\begin{document}" in result:
            return result

    # Strategy 2: Extract from ``` ... ``` block (any language)
    code_block = re.search(r"```\s*\n?(.*?)```", raw_output, re.DOTALL)
    if code_block:
        result = code_block.group(1).strip()
        if result.startswith("\\documentclass") or "\\begin{document}" in result:
            return result

    # Strategy 3: Entire output starts with \documentclass
    stripped = raw_output.strip()
    if stripped.startswith("\\documentclass"):
        return stripped

    # Strategy 4: Find \documentclass anywhere in the output and extract
    docclass_match = re.search(r"(\\documentclass.*?\\end\{document\})", stripped, re.DOTALL)
    if docclass_match:
        return docclass_match.group(1).strip()

    # Strategy 5: Find \begin{document} to \end{document} block
    begin_end_match = re.search(r"(\\begin\{document\}.*?\\end\{document\})", stripped, re.DOTALL)
    if begin_end_match:
        # Reconstruct with a minimal preamble
        preamble = "\\documentclass[letterpaper,11pt]{article}\\n\\usepackage[empty]{fullpage}\\n\\usepackage{titlesec}\\n\\usepackage{hyperref}\\n\\usepackage{enumitem}\\n\\pagestyle{fancy}\\n\\fancyhf{}\\n\\fancyfoot{}\\n\\renewcommand{\\headrulewidth}{0pt}\\n\\renewcommand{\\footrulewidth}{0pt}\\n\\titleformat{\\section}{\\vspace{-4pt}\\scshape\\raggedright\\large}{}{0em}{}[\\color{black}\\titlerule \\vspace{-5pt}]"
        return preamble + "\n\n" + begin_end_match.group(1).strip()

    # Strategy 6: The output might be a simple error or message - return it as-is if it looks like reasonable text
    if len(stripped) > 100 and not stripped.startswith("<!DOCTYPE") and not stripped.startswith("{"):
        # Could be plain text with LaTeX commands - try wrapping it
        if "\\section" in stripped or "\\textbf" in stripped:
            preamble = "\\documentclass[letterpaper,11pt]{article}\\n\\usepackage[empty]{fullpage}\\n\\usepackage{titlesec}\\n\\usepackage{hyperref}\\n\\usepackage{enumitem}\\n\\pagestyle{fancy}\\n\\fancyhf{}\\n\\fancyfoot{}\\n\\renewcommand{\\headrulewidth}{0pt}\\n\\renewcommand{\\footrulewidth}{0pt}\\n\\begin{document}"
            return preamble + "\n\n" + stripped + "\n\n\\end{document}"

    raise Exception("Could not extract valid LaTeX from AI output. The model may have returned an unexpected format. Try again.")


@app.route('/api/latex/generate', methods=['POST'])
def api_latex_generate():
    """Use AI (OpenRouter) to convert plain text resume into LaTeX using the selected template style."""
    if not OPENROUTER_API_KEY:
        return jsonify({"success": False, "error": "OpenRouter API key not configured. Add OPENROUTER_API_KEY to .env"}), 400

    if not REQUESTS_AVAILABLE:
        return jsonify({"success": False, "error": "'requests' library required for AI generation"}), 400

    try:
        data = request.get_json(force=True)
        user_content = data.get("resume_content", "").strip()
        template = data.get("template", "jake").lower()

        if not user_content or len(user_content) < 20:
            return jsonify({"success": False, "error": "Please paste your full resume content (at least 20 characters)"}), 400

        if len(user_content) > 15000:
            return jsonify({"success": False, "error": "Resume content is too long (max 15,000 characters)"}), 400

        # Choose the reference template and set instructions
        if template == "sourabh":
            ref_template = _sourabh_resume_source
            template_name = "Sourabh Bajaj's Resume"
            custom_instructions = """## TEMPLATE STRUCTURE (use these exact LaTeX commands):
The template uses these custom commands - you MUST use them:

1. HEADER: tabular* block with name, email, website link, and mobile number.
2. EDUCATION: \\section{Education} with \\resumeSubheading{School}{Location}{Degree}{Dates}
3. EXPERIENCE: \\section{Experience} with \\resumeSubheading{Company}{Location}{JobTitle}{Dates} then \\resumeItemListStart and \\resumeItem{Category}{Description} (e.g. \\resumeItem{TensorFlow}{TensorFlow is...}) or plain bullets using \\resumeItemPlain{bullet text}
4. PROJECTS: \\section{Projects} with \\resumeSubItem{ProjectName}{Description}
5. SKILLS: \\section{Skills} using \\resumeSubItem{Category}{items} or tabular."""
        elif template == "pratul":
            ref_template = _pratul_resume_source
            template_name = "Pratul Muthuraja's Resume"
            custom_instructions = """## TEMPLATE STRUCTURE (use these exact LaTeX commands):
The template uses these custom commands - you MUST use them:

1. HEADER: tabular* block with name, email, portfolio, mobile, and github.
2. EDUCATION: \\section{Education} with \\resumeSubheading{School}{Location}{Degree}{Dates}
3. SKILLS: \\section{Skills} with \\resumeSubItem{Category}{items}
4. EXPERIENCE: \\section{Experience} with \\resumeSubheading{Company}{Location}{Role}{Dates} followed by optional \\resumeSubSubheading{ProjectName} and \\resumeItemListStart/\\resumeItem{bullet}"""
        elif template == "faang":
            ref_template = _faang_resume_source
            template_name = "FAANG Simple Resume"
            custom_instructions = """## TEMPLATE STRUCTURE (use these exact LaTeX commands):
The template uses these custom commands - you MUST use them:

1. HEADER: Use \\name{Firstname Lastname} and \\address{...} blocks.
2. SECTIONS: Use \\begin{rSection}{Section Name} ... \\end{rSection}
3. EXPERIENCE: Inside rSection, format job title and company using:
\\textbf{Role Name} \\hfill Dates\\\\
Company Name \\hfill \\textit{Location}
followed by an itemize environment for bullet points.
4. PROJECTS: Inside rSection, use list items like:
\\item \\textbf{Project Title.} {Project description...}
5. SKILLS: Inside rSection, use tabular formatting:
\\begin{tabular}{ @{} >{\\bfseries}l @{\\hspace{6ex}} l }
Technical Skills & details \\\\
Soft Skills & details
\\end{tabular}"""
        else:
            ref_template = _default_resume_source
            template_name = "Jake's Resume"
            custom_instructions = """## TEMPLATE STRUCTURE (use these exact LaTeX commands):
The template uses these custom commands - you MUST use them:

1. HEADER: \\\\begin{{center}} block with name, phone, email, LinkedIn, GitHub
2. EDUCATION: \\\\section{{Education}} with \\\\resumeSubheading{{School}}{{Location}}{{Degree}}{{Dates}}
3. EXPERIENCE: \\\\section{{Experience}} with \\\\resumeSubheading{{JobTitle}}{{Dates}}{{Company}}{{Location}} then \\\\resumeItemListStart and \\\\resumeItem{{text}} for each bullet
4. PROJECTS: \\\\section{{Projects}} with \\\\resumeProjectHeading{{Name $|$ TechStack}}{{Dates}} then \\\\resumeItemListStart / \\\\resumeItem
5. TECHNICAL SKILLS: \\\\section{{Technical Skills}} with \\\\begin{{itemize}} using \\\\textbf{{Category}}{{: items}}"""

        # Extract the preamble from the selected template
        preamble_match = re.search(r"(.*?)\\begin\{document\}", ref_template, re.DOTALL)
        preamble = preamble_match.group(1) if preamble_match else ref_template

        # Build dynamic system prompt
        system_prompt = f"""You are an expert LaTeX resume generator. Your task is to convert plain text resume content into a properly formatted LaTeX document using the {template_name} template.

{custom_instructions}

## RULES (strict - follow every one):
1. KEEP the EXACT preamble (everything before \\\\begin{{document}}) from the reference template below - do NOT modify or remove any packages or macros
2. ONLY modify the content between \\\\begin{{document}} and \\\\end{{document}}
3. Parse the user's plain text resume and extract contact info, education, experience, projects, and skills.
4. Use \\\\href{{url}}{{text}} for all links (email, LinkedIn, GitHub)
5. If a section has no content, OMIT it entirely (don't include empty sections)
6. If the user's text doesn't specify a date, use a reasonable placeholder like "Date" or empty
7. Output ONLY the complete LaTeX code wrapped in ```latex ... ``` code block
8. Do NOT include any explanations, notes, or commentary outside the code block
9. Ensure the output will compile WITHOUT errors - use proper escaping for special characters (&, %, $, #, _, {{, }}, ~, ^)
10. CONTENT RETENTION: You MUST include EVERY SINGLE piece of information from the user's plain text resume. DO NOT summarize, truncate, shorten, or omit any details. Every single bullet point, project entry, and work experience must be fully converted.
11. EXTRA SECTIONS: If the user's plain text contains sections that do not map directly to the reference template's predefined headers (such as "Achievements", "Extracurricular Activities", "Positions of Responsibility", "Publications", etc.), you MUST NOT omit them. Instead, create a new section using \\\\section{{Section Name}} and format the content using standard subheading and bullet list structures appropriate for the template.
12. NO PLACEHOLDERS: Do not use template placeholders (like "Company Name" or "Job Title") in the output. If the information is in the user's plain text resume, output that actual information.
"""

        # Build the full system prompt with the template preamble included
        system_prompt_with_template = (
            system_prompt
            + "\n\n## REFERENCE LATEX PREAMBLE (copy this EXACTLY into your output):\n```latex\n"
            + preamble
            + "\n```"
        )

        # Call OpenRouter with the enhanced system prompt that includes the template
        raw_output, success_model = _call_openrouter(system_prompt_with_template, user_content)

        # Clean and validate the output
        latex_source = _clean_latex_output(raw_output)

        # Basic validation
        if "\\begin{document}" not in latex_source:
            raise Exception("Generated LaTeX is missing \\\\begin{document}")

        if "\\end{document}" not in latex_source:
            raise Exception("Generated LaTeX is missing \\\\end{document}")

        return jsonify({
            "success": True,
            "latex_source": latex_source,
            "model": success_model,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
