"""
Post Parser Utility
===================
Extracts structured job details (Company, Role, Location) from a LinkedIn URL.

Supports two URL types:
1. LinkedIn Job URLs (linkedin.com/jobs/view/...) → DOM-based extraction from structured page
2. LinkedIn Post URLs (linkedin.com/posts/...) → text extraction with strict validation
"""

import logging
import re
from typing import Dict, Any, Optional, List
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Maximum reasonable length for extracted fields (anything longer is likely garbage)
MAX_COMPANY_LENGTH = 50
MAX_ROLE_LENGTH = 80
MAX_LOCATION_LENGTH = 60
MIN_COMPANY_LENGTH = 2
MIN_ROLE_LENGTH = 3
MIN_LOCATION_LENGTH = 2

# Words that indicate the extracted text is still part of a sentence (not a clean field)
SENTENCE_WORDS = ["the", "and", "for", "our", "its", "their", "your", "with", "this", "that",
                  "will", "can", "has", "have", "been", "were", "are", "also", "about", "into",
                  "through", "during", "before", "after", "while", "because", "should", "would"]

# Exclude patterns that make a field invalid (these indicate the extraction hit noise)
EXCLUDE_COMPANY_PATTERNS = [
    r'\bmanager\b', r'\bengineer\b', r'\bintern\b', r'\bproduct\b', r'\bdeveloper\b',
    r'\bdesigner\b', r'\banalyst\b', r'\bhiring\b', r'\blooking\b', r'\bgrowing\b',
    r'\bjoin\b', r'\bposition\b', r'\bopportunity\b', r'\bapply\b', r'\bsubmit\b',
    r'\bemail\b', r'\breach\b', r'\binternship\b', r'\bfull.?time\b',
]

EXCLUDE_ROLE_PATTERNS = [
    r'\bwe\'?re\b', r'\bare\b', r'\bfor\b', r'\bat\b', r'\bwith\b',
    r'^\s*(?:and|to|in|of|the|a|an)\s+',
]

EXCLUDE_LOCATION_PATTERNS = [
    r'\bhiring\b', r'\blooking\b', r'\bapply\b', r'\bmanager\b', r'\bengineer\b',
    r'\bposition\b', r'\bopportunity\b', r'\bsubmit\b',
]

# Known cities/regions for location detection (ordered by specificity - longer matches first)
KNOWN_LOCATIONS = sorted([
    "san francisco", "new york", "los angeles", "united states", "bangalore",
    "bengaluru", "mumbai", "hyderabad", "chennai", "ahmedabad", "kolkata",
    "chandigarh", "visakhapatnam", "coimbatore", "trivandrum", "gurugram",
    "gurgaon", "pune", "delhi", "noida", "jaipur", "lucknow", "indore",
    "bhopal", "kochi", "nagpur", "thane", "surat", "remote", "goa",
    "london", "singapore", "dubai", "berlin", "amsterdam", "toronto",
    "sydney", "seattle", "austin", "chicago", "boston", "india",
    "usa", "uk",
], key=len, reverse=True)  # Longer matches first to avoid partial matches


def _is_valid_company(text: str) -> bool:
    """Validate that extracted company name looks legitimate."""
    if not text or len(text) < MIN_COMPANY_LENGTH or len(text) > MAX_COMPANY_LENGTH:
        return False
    # Should start with uppercase letter, digit, or be alphabetic
    if not text[0].isupper() and not text[0].isalpha() and not text[0].isdigit():
        return False
    text_lower = text.lower()
    # Check for sentence words (if it contains too many, it's probably a full sentence)
    sentence_word_count = sum(1 for w in SENTENCE_WORDS if w in text_lower.split())
    if sentence_word_count >= 2:
        return False
    # Check exclude patterns
    for pattern in EXCLUDE_COMPANY_PATTERNS:
        if re.search(pattern, text_lower):
            return False
    return True


def _is_valid_role(text: str) -> bool:
    """Validate that extracted role looks legitimate."""
    if not text or len(text) < MIN_ROLE_LENGTH or len(text) > MAX_ROLE_LENGTH:
        return False
    text_lower = text.lower().strip()
    # Check exclude patterns
    for pattern in EXCLUDE_ROLE_PATTERNS:
        if re.search(pattern, text_lower):
            return False
    # Should start with a capital letter or number
    if text[0].islower() and not text[0].isdigit():
        return False
    if text[0] in [',', '.', '!', '?', ')', ']', '}']:
        return False
    # If it contains too many spaces, it's probably a sentence, not a role title
    if text.count(' ') > 12:
        return False
    # Check for sentence words (roles shouldn't have "the", "and", etc. as main content)
    sentence_word_count = sum(1 for w in SENTENCE_WORDS if w in text_lower.split())
    if sentence_word_count >= 1:
        return False
    return True


def _is_valid_location(text: str) -> bool:
    """Validate that extracted location looks legitimate."""
    if not text or len(text) < MIN_LOCATION_LENGTH or len(text) > MAX_LOCATION_LENGTH:
        return False
    text_lower = text.lower()
    # Must contain at least one known location word or pattern
    has_known = any(loc in text_lower for loc in KNOWN_LOCATIONS)
    if not has_known and "," not in text:
        return False
    # Check exclude patterns
    for pattern in EXCLUDE_LOCATION_PATTERNS:
        if re.search(pattern, text_lower):
            return False
    return True


async def extract_structured_post_data(page: Page, url: str) -> Optional[Dict[str, Any]]:
    """
    Navigates to LinkedIn URL and extracts structured details.

    Returns:
        dict with keys: company, role, location, url
        or dict with 'error' key on failure
    """
    logger.info(f"Extracting data from: {url}")
    if "/jobs/view/" in url:
        return await _extract_from_job_page(page, url)
    else:
        return await _extract_from_post_page(page, url)


async def _extract_from_job_page(page: Page, url: str) -> Optional[Dict[str, Any]]:
    """Extract data from a LinkedIn Job page using DOM selectors."""
    logger.info(f"Extracting from job page: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        company = "Unknown"
        role = "Unknown"
        location = "Unknown"

        # Extract Company
        company_selectors = [
            'a.topcard__org-name-link',
            'a[data-tracking-control-name*="public_jobs_topcard-org-name"]',
            'span.topcard__flavor a[href*="/company/"]',
            'a[href*="/company/"]',
        ]
        for selector in company_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.count() > 0:
                    text = await elem.inner_text()
                    text = text.strip().split("\n")[0].strip()
                    if text and len(text) > 1:
                        company = text
                        break
            except:
                continue

        # Extract Role
        title_selectors = [
            'h1.top-card-layout__title',
            'h1.t-24.t-bold',
            'h2.top-card-layout__title',
            'h1',
        ]
        for selector in title_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.count() > 0:
                    text = await elem.inner_text()
                    text = text.strip()
                    if text and len(text) > 3 and len(text) < 150:
                        role = text
                        break
            except:
                continue

        # Extract Location
        location_selectors = [
            'span.topcard__flavor--bullet',
            'span[class*="job-details-jobs-unified-top-card__bullet"]',
            'div[class*="job-details-jobs-unified-top-card__primary-description"] span',
        ]
        for selector in location_selectors:
            try:
                elems = await page.locator(selector).all()
                for elem in elems:
                    text = await elem.inner_text()
                    text = text.strip()
                    if text and ("," in text or any(city in text.lower() for city in ["remote", "india", "united states"])):
                        location = text
                        break
            except:
                continue

        logger.info(f"Job page: Company={company}, Role={role}, Location={location}")
        return {"company": company, "role": role, "location": location, "url": url}

    except Exception as e:
        logger.error(f"Job page extraction failed: {e}")
        return {"error": str(e), "url": url}


async def _extract_from_post_page(page: Page, url: str) -> Optional[Dict[str, Any]]:
    """Extract data from a LinkedIn Post page."""
    logger.info(f"Extracting from post page: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Wait for content
        try:
            await page.wait_for_selector('.feed-shared-update-v2', timeout=15000)
        except:
            try:
                await page.wait_for_selector('[data-urn*="activity"]', timeout=10000)
            except:
                logger.warning("Post selector not found, using page text")

        # Click "see more" buttons
        try:
            for btn in await page.query_selector_all('button:has-text("see more")'):
                try:
                    await btn.click()
                    await page.wait_for_timeout(500)
                except:
                    pass
        except:
            pass

        # Extract post text
        content = ""
        for selector in ['.feed-shared-update-v2__description', '.feed-shared-update-v2',
                         '.update-components-text', '.break-words.whitespace-pre-wrap', 'article']:
            try:
                text = await page.inner_text(selector)
                if text and len(text.strip()) > 50:
                    content = text.strip()
                    break
            except:
                continue

        if not content:
            content = await page.inner_text("body")

        # Extract actor company FIRST (most reliable source)
        actor_company = await _extract_actor_company(page)

        # Extract with validation, preferring actor company
        company = _extract_company(content, actor_company)
        role = _extract_role(content)
        location = _extract_location(content)

        logger.info(f"Post page: Company={company}, Role={role}, Location={location}")
        return {"company": company, "role": role, "location": location, "url": url}

    except Exception as e:
        logger.error(f"Post page extraction failed: {e}")
        return {"error": str(e), "url": url}


async def _extract_actor_company(page: Page) -> Optional[str]:
    """
    Extract company from the post author's profile line (most reliable source).
    Returns like "Google" from "CEO at Google" or "Recruiter at Microsoft"
    """
    try:
        selectors = [
            'span.feed-shared-actor__sub-description',
            'span.update-components-actor__sub-description',
            '[class*="actor__sub-description"]',
        ]
        for selector in selectors:
            try:
                elem = page.locator(selector).first
                if await elem.count() > 0:
                    text = await elem.inner_text()
                    text = text.strip()
                    if " at " in text:
                        parts = text.split(" at ")
                        company = parts[-1].strip()
                        company = re.sub(r'\s*[•|].*$', '', company).strip()
                        if 2 <= len(company) <= MAX_COMPANY_LENGTH:
                            logger.info(f"Actor company: {company}")
                            return company
                    elif text and len(text) < MAX_COMPANY_LENGTH:
                        actor_words = text.lower().split()
                        sentence_count = sum(1 for w in SENTENCE_WORDS if w in actor_words)
                        if sentence_count == 0 and text[0].isupper():
                            return text
            except:
                continue
    except Exception as e:
        logger.debug(f"Actor company extraction failed: {e}")
    return None


def _extract_company(content: str, actor_company: Optional[str] = None) -> str:
    """
    Extract company name from post text.
    Actor company takes priority since it's the most reliable.
    """
    # PRIORITY: Actor company (most reliable)
    if actor_company and _is_valid_company(actor_company):
        return actor_company

    lines = content.split("\n")
    content_lower = content.lower()

    # Strategy A: "hiring at [Company]" or "growing at [Company]" or "join [Company]"
    # (ONLY these specific hiring-related patterns, NOT "looking for")
    company_patterns = [
        r'(?:hiring|growing|recruiting|joining)\s+at\s+([A-Z][A-Za-z0-9\s&.\-]{2,45}?)(?:\s*[!.,]|\s*$|\s*\n|\s*📍|\s*✨|\s*💡|\s*📈|\s*🚀)',
        r'join(?:ing)?\s+(?:us\s+)?at\s+([A-Z][A-Za-z0-9\s&.\-]{2,45}?)(?:\s*[!.,]|\s*$|\s*\n)',
        r'part\s+of\s+(?:the\s+)?(?:team\s+)?at\s+([A-Z][A-Za-z0-9\s&.\-]{2,45}?)(?:\s*[!.,]|\s*$|\s*\n)',
        r'team\s+at\s+([A-Z][A-Za-z0-9\s&.\-]{2,45}?)(?:\s*[!.,]|\s*$|\s*\n|\s*📍)',
    ]

    for pattern in company_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            company = match.group(1).strip().rstrip("!., ")
            if _is_valid_company(company):
                return company

    # Strategy B: Look in first meaningful line for "at [CompanyName]" ending
    meaningful_lines = [l.strip() for l in lines
                        if len(l.strip()) > 15
                        and not any(w in l.lower() for w in ["reaction", "comment", "like", "share", "follow", "http"])]
    for line in meaningful_lines[:3]:
        # Check if line ends with "at CompanyName"
        at_match = re.search(r'\b(?:at|with)\s+([A-Z][A-Za-z0-9\s&.\-]{2,45})$', line.strip().rstrip("!., "))
        if at_match:
            company = at_match.group(1).strip()
            if _is_valid_company(company):
                return company

    # Strategy C: Try actor company even if it failed validation (better than Unknown)
    if actor_company and len(actor_company) > 1:
        return actor_company

    return "Unknown"


def _extract_role(content: str) -> str:
    """
    Extract job role from post text with strict validation.
    Returns the SHORTEST, most specific match.
    """
    lines = content.split("\n")
    content_lower = content.lower()
    candidates = []

    # Strategy A: Role after "hiring/looking for a/an [Role]" — most common pattern
    role_patterns = [
        r'(?:hiring|looking|seeking|recruiting)\s+(?:a|an)\s+([A-Z][A-Za-z\s/]{3,55}?)(?:\s*[!.,]|\s*$|\s*\n|\s*📍|\s*✨|\s*💡|\s*to\s+|\s*who\s+|\s*-\s+)',
        r'(?:hiring|looking|seeking|recruiting)\s+(?:for\s+)?(?:a\s+|an\s+)?([A-Z][A-Za-z\s/]{3,55}?)(?:\s*[!.,]|\s*$|\s*\n|\s*📍|\s*✨|\s*💡|\s*to\s+|\s*who\s+|\s*-\s+)',
        r'(?:role|position)\s*(?::|is|open)\s*(?:for\s+)?(?:a\s+|an\s+)?([A-Z][A-Za-z\s/]{3,55}?)(?:\s*[!.,]|\s*$|\s*\n)',
    ]
    for pattern in role_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            role = match.group(1).strip().rstrip("!., ")
            if _is_valid_role(role):
                candidates.append(role)

    # Strategy B: Role after emoji bullet points (most common in post formatting)
    for line in lines:
        stripped = line.strip()
        # Lines starting with emojis often contain role titles
        if stripped and stripped[0] in ['✨', '📈', '💡', '🚀', '💼', '🔍', '🎯', '👩‍💻', '👨‍💻', '📢', '📍', '▶', '▸', '•', '⚡']:
            clean = re.sub(r'^[✨📈💡🚀💼🔍🎯👩‍💻👨‍💻📢📍▶▸•⚡\s*:\-]+', '', stripped).strip()
            # Remove leading numbering like "1.", "2."
            clean = re.sub(r'^\d+[.)]\s*', '', clean).strip()
            if clean and len(clean) < MAX_ROLE_LENGTH and len(clean) > MIN_ROLE_LENGTH:
                if _is_valid_role(clean):
                    candidates.append(clean)

    # Strategy C: Look for known job title keywords in lines
    JOB_TITLES = [
        "product manager", "software engineer", "software development engineer", "sde",
        "backend engineer", "frontend engineer", "full stack engineer", "data scientist",
        "machine learning engineer", "devops engineer", "site reliability engineer",
        "business analyst", "data analyst", "product analyst", "data engineer",
        "chief of staff", "founder's office", "entrepreneur in residence", "eir",
        "solutions architect", "technical program manager", "tpm",
        "ux designer", "product designer", "ui designer", "qa engineer",
        "security engineer", "cloud engineer", "platform engineer",
        "growth intern", "marketing intern", "product intern",
        "python developer", "java developer", "full stack developer",
        "associate product manager", "apm", "program manager",
    ]

    for line in lines:
        line_lower = line.lower().strip()
        if len(line_lower) > MAX_ROLE_LENGTH:
            continue
        if any(w in line_lower for w in ["reaction", "comment", "like", "share", "clicked"]):
            continue

        for title in JOB_TITLES:
            if title in line_lower:
                # Find the actual role text from the original line
                idx = line_lower.find(title)
                # Extract from that position, bounded
                start = idx
                end = min(len(line), idx + len(title) + 30)
                role_text = line[start:end].strip().rstrip("!.,;: ")
                # Cut at sentence boundaries
                for punct in ['. ', '! ', '? ', ' - ', ' – ']:
                    if punct in role_text:
                        role_text = role_text.split(punct)[0].strip()
                if _is_valid_role(role_text):
                    candidates.append(role_text)
                break  # First match per line

    # Strategy D: Lines with "intern" or "internship"
    for line in lines:
        if ("intern" in line.lower() or "internship" in line.lower()):
            clean = line.strip()
            clean = re.sub(r'^[•\-*\d\s)\]]+', '', clean).strip()
            clean = re.sub(r'[#].*$', '', clean).strip()
            if len(clean) < MAX_ROLE_LENGTH and len(clean) > MIN_ROLE_LENGTH:
                if _is_valid_role(clean):
                    candidates.append(clean)

    # Return the SHORTEST valid match (most likely the actual title)
    if candidates:
        # Sort by length (shortest first), take unique
        unique = []
        for c in candidates:
            c_lower = c.lower()
            if not any(c_lower in u.lower() or u.lower() in c_lower for u in unique):
                unique.append(c)
        unique.sort(key=len)
        return unique[0]

    return "Check post for details"


def _extract_location(content: str) -> str:
    """
    Extract location from post text with strict validation.
    """
    lines = content.split("\n")
    content_lower = content.lower()

    # Strategy A: Location emojis (most explicit)
    for emoji in ["📍", "🌍", "🌏", "🌎", "📌"]:
        for line in lines:
            if emoji in line:
                loc = line.replace(emoji, "").strip().lstrip(": ").strip()
                if _is_valid_location(loc):
                    return loc

    # Strategy B: "Location:" or "Loc:" prefix
    loc_match = re.search(
        r'(?:location|loc|based|office|place)\s*[:：]\s*([A-Za-z][A-Za-z\s,./\-()]{2,55}?)(?:\s*[!.,]|\s*$|\s*\n|\s*✨|\s*📍|💡)',
        content, re.IGNORECASE | re.MULTILINE
    )
    if loc_match:
        loc = loc_match.group(1).strip().rstrip("!., ")
        if _is_valid_location(loc):
            return loc

    # Strategy C: Look for known city/region in lines
    for line in lines:
        line_lower = line.lower().strip()
        # Only check reasonably short lines
        if len(line_lower) > MAX_LOCATION_LENGTH + 20:
            continue
        found = [loc for loc in KNOWN_LOCATIONS if loc in line_lower]
        if found:
            # Use the longest match (most specific)
            best = max(found, key=len)
            idx = line_lower.find(best)
            # Try to extract just the clean location: from comma/slash/dash before city to end of city phrase
            pre = line_lower[:idx].rstrip()
            # Walk backwards to nearest separator
            sep_idx = max(pre.rfind(','), pre.rfind('/'), pre.rfind('-'), pre.rfind('('), pre.rfind(':'))
            if sep_idx >= 0:
                clean_start = sep_idx + 1
            else:
                clean_start = max(0, idx - 10)
            end = min(len(line), idx + len(best) + 20)
            context = line[clean_start:end].strip().lstrip(",;:-( ").strip()
            # Cut at sentence boundaries using rsplit on known separators
            for punct in [',', '/', '-']:
                parts = context.rsplit(punct, 1)
                if len(parts) > 1 and any(loc in parts[1].lower() for loc in KNOWN_LOCATIONS):
                    context = parts[1].strip()
            context = re.sub(r'\s*\(.*$', '', context).strip()
            if _is_valid_location(context):
                return context

    return "Unknown"
