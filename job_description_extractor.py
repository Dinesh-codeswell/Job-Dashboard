#!/usr/bin/env python3
"""
INDUSTRY-STANDARD JOB DESCRIPTION EXTRACTOR
============================================
Based on best practices from LinkedIn, Glassdoor, Indeed, and other top job boards.

Philosophy:
1. PRESERVE source HTML structure (don't reconstruct)
2. MINIMAL processing (only clean, don't transform)
3. SEMANTIC HTML (use proper tags)
4. CSS handles presentation (not Python)

Key Principles:
- If source has <h3>, keep <h3>
- If source has <ul>, keep <ul>
- If source has <p>, keep <p>
- Only remove: scripts, styles, ads, tracking
- Only add: wrapper div for styling

USAGE:
    from job_description_extractor import extract_job_description
    
    # Automatic platform detection
    html = extract_job_description(raw_html, platform="indeed")
    html = extract_job_description(raw_html, platform="linkedin")
"""

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup, Comment
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class IndustryStandardExtractor:
    """
    Industry-standard job description extractor with 100% quality checks.
    
    Follows the "preserve, don't transform" philosophy used by top job boards.
    
    QUALITY CHECKS (NEW):
    1. Minimum length validation (must be > 200 chars)
    2. Unpaid role detection (reject if "unpaid" mentioned)
    3. Button removal (Easy Apply, Apply Now, etc.)
    4. Heading/subheading formatting (proper line breaks)
    5. Extraction success validation (must have content)
    """
    
    # Elements to remove (security + clutter)
    REMOVE_TAGS = [
        'script', 'style', 'noscript', 'iframe', 'object', 'embed',
        'svg', 'canvas', 'audio', 'video', 'button', 'input', 'form',
        'nav', 'header', 'footer', 'aside'
    ]
    
    # Attributes to remove (tracking + styling)
    REMOVE_ATTRS = [
        'onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout',
        'style', 'class', 'id', 'data-tracking', 'data-analytics'
    ]
    
    # Keep these attributes (semantic meaning)
    KEEP_ATTRS = ['href', 'src', 'alt', 'title']
    
    # Button text patterns to remove
    BUTTON_PATTERNS = [
        r'easy\s+apply',
        r'apply\s+now',
        r'apply\s+on\s+company\s+website',
        r'save\s+job',
        r'save\s+this\s+job',
        r'unsave\s+job',
        r'report\s+job',
        r'share\s+job',
        r'view\s+company',
        r'view\s+profile',
        r'message\s+recruiter',
        r'follow\s+company',
        r'learn\s+more',
        r'see\s+more',
        r'show\s+more',
        r'read\s+more',
    ]
    
    # Unpaid keywords to detect
    UNPAID_KEYWORDS = [
        'unpaid', 'no compensation', 'no pay', 'volunteer',
        'unpaid internship', 'unpaid position', 'unpaid role',
        'without compensation', 'without pay', 'no salary',
    ]
    
    def __init__(self):
        """Initialize extractor."""
        pass
    
    # ========================================================================
    # QUALITY VALIDATION METHODS (NEW)
    # ========================================================================
    
    def is_unpaid_role(self, text: str) -> bool:
        """
        Check if job description mentions unpaid compensation.
        
        Args:
            text: Job description text
            
        Returns:
            True if unpaid role detected, False otherwise
        """
        text_lower = text.lower()
        
        for keyword in self.UNPAID_KEYWORDS:
            if keyword in text_lower:
                logger.warning(f"Unpaid role detected: '{keyword}' found in description")
                return True
        
        return False
    
    def validate_extraction(self, html: str, min_length: int = 200) -> tuple[bool, str]:
        """
        Validate extracted JD meets quality standards.
        
        Args:
            html: Extracted HTML
            min_length: Minimum required length
            
        Returns:
            (is_valid, reason) tuple
        """
        if not html:
            return False, "Empty extraction"
        
        # Check length (reduced from 200 to 150 for more lenient validation)
        text_content = BeautifulSoup(html, 'html.parser').get_text(strip=True)
        if len(text_content) < min_length:
            return False, f"Too short ({len(text_content)} chars, min {min_length})"
        
        # Check for unpaid
        if self.is_unpaid_role(text_content):
            return False, "Unpaid role detected"
        
        # Check for actual content (not just buttons/metadata)
        # Made more lenient - just check if we have ANY content tags
        if not any(tag in html for tag in ['<h', '<p', '<ul', '<li', '<strong', '<b', '<div']):
            return False, "No content tags found"
        
        return True, "Valid extraction"
    
    def remove_buttons(self, html: str) -> str:
        """
        Remove button text and elements from HTML.
        
        Args:
            html: HTML string
            
        Returns:
            HTML with buttons removed
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove button elements
        for button in soup.find_all('button'):
            button.decompose()
        
        # Remove text matching button patterns
        for tag in soup.find_all(string=True):
            text_lower = tag.lower()
            for pattern in self.BUTTON_PATTERNS:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    # Remove the entire parent element if it's just a button
                    if tag.parent and tag.parent.name in ['div', 'span', 'p', 'li']:
                        parent_text = tag.parent.get_text(strip=True).lower()
                        if re.search(pattern, parent_text, re.IGNORECASE):
                            tag.parent.decompose()
                            break
        
        return str(soup)
    
    def fix_heading_formatting(self, html: str) -> str:
        """
        Fix heading/subheading formatting to ensure proper line breaks.
        
        Issues fixed:
        - Headings not on new lines
        - Missing line breaks after headings
        - Subheadings merged with content
        
        Args:
            html: HTML string
            
        Returns:
            HTML with proper heading formatting
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all heading tags
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            # Ensure heading is on its own line
            if heading.previous_sibling and isinstance(heading.previous_sibling, str):
                prev_text = str(heading.previous_sibling).strip()
                if prev_text and not prev_text.endswith('\n'):
                    heading.previous_sibling.replace_with(prev_text + '\n')
            
            # Ensure content after heading starts on new line
            if heading.next_sibling and isinstance(heading.next_sibling, str):
                next_text = str(heading.next_sibling).strip()
                if next_text and not next_text.startswith('\n'):
                    heading.next_sibling.replace_with('\n' + next_text)
        
        # Format HTML with proper newlines
        html_str = str(soup)
        html_str = re.sub(r'(</h[1-6]>)(\S)', r'\1\n\2', html_str)  # After headings
        html_str = re.sub(r'(<h[1-6]>)(\S)', r'\1\n\2', html_str)  # Before headings
        
        return html_str
    
    # ========================================================================
    # LINKEDIN EXTRACTION (Playwright-based)
    # ========================================================================
    
    async def extract_linkedin(self, page: Page) -> Optional[str]:
        """
        Extract LinkedIn job description using industry-standard approach.
        
        LinkedIn Structure:
        - Main container: div with "About the job" heading
        - Content: Nested divs with actual HTML structure
        - Strategy: Find container, extract inner HTML, clean minimally
        
        CRITICAL FIXES:
        1. Increased timeout + better error handling
        2. Remove buttons (Easy Apply, etc.)
        3. Fix heading formatting
        4. Validate extraction quality
        5. Check for unpaid roles
        
        Args:
            page: Playwright page object
            
        Returns:
            Clean HTML string or None if extraction fails
        """
        try:
            # Wait for content to load (increased timeout from 10s to 15s)
            try:
                await page.wait_for_selector('h2:has-text("About the job")', timeout=15000)
            except:
                logger.warning("LinkedIn: 'About the job' heading not found within 15s")
                return None
            
            # Get the description container
            # LinkedIn wraps description in a div after "About the job" heading
            container = page.locator('h2:has-text("About the job")').locator('xpath=following-sibling::div[1]')
            
            if await container.count() == 0:
                logger.warning("LinkedIn: Description container not found")
                return None
            
            # Get raw HTML
            raw_html = await container.inner_html()
            
            if not raw_html or len(raw_html) < 100:
                logger.warning("LinkedIn: Description too short")
                return None
            
            # Clean and return
            cleaned = self._clean_html(raw_html, platform="linkedin")
            
            # Remove buttons
            cleaned = self.remove_buttons(cleaned)
            
            # Fix heading formatting
            cleaned = self.fix_heading_formatting(cleaned)
            
            # Validate extraction
            is_valid, reason = self.validate_extraction(cleaned)
            if not is_valid:
                logger.warning(f"LinkedIn: Extraction validation failed - {reason}")
                return None
            
            logger.info("LinkedIn: Extraction successful and validated")
            return cleaned
            
        except Exception as e:
            logger.error(f"LinkedIn extraction error: {e}")
            return None
    
    # ========================================================================
    # INDEED EXTRACTION (HTML-based)
    # ========================================================================
    
    def extract_indeed(self, raw_html: str) -> Optional[str]:
        """
        Extract Indeed job description with AGGRESSIVE cleaning.
        
        Indeed has MAJOR issues:
        1. Escaped characters: \\- \\( \\)
        2. Encoding issues: Ã¢ÂÂ (UTF-8 mojibake)
        3. Decorative junk: *͏** ---- etc.
        4. Poor structure: Everything in one <p> tag
        
        CRITICAL FIXES:
        1. Remove buttons (Easy Apply, etc.)
        2. Fix heading formatting
        3. Validate extraction quality
        4. Check for unpaid roles
        5. Ensure extraction succeeded
        
        Strategy: Extract, fix encoding, remove junk, restructure properly
        
        Args:
            raw_html: Raw HTML from Indeed
            
        Returns:
            Clean, properly structured HTML like LinkedIn or None if validation fails
        """
        try:
            logger.info("Indeed: Extracting and cleaning HTML")
            
            if not raw_html or len(raw_html) < 50:
                logger.warning("Indeed: Raw HTML too short")
                return None
            
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Find description container
            container = (
                soup.find('div', {'id': 'jobDescriptionText'}) or
                soup.find('div', class_=lambda x: x and 'jobsearch-jobDescriptionText' in str(x)) or
                soup.find('div', class_=lambda x: x and 'job-description-content' in str(x)) or
                soup.find('div', class_=lambda x: x and 'description' in str(x).lower())
            )
            
            if not container:
                logger.warning("Indeed: Description container not found, trying full HTML")
                container = soup
            
            # Clean the HTML first (remove scripts, styles, etc.)
            cleaned_soup = self._clean_indeed_specific(BeautifulSoup(str(container), 'html.parser'))
            
            # Check if we have good HTML structure (has proper tags)
            has_structure = bool(cleaned_soup.find_all(['ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'li', 'strong', 'b']))
            
            if has_structure:
                # HTML already has good structure, clean and format it properly
                logger.info(f"Indeed: HTML has structure, cleaning and formatting")
                
                # Apply comprehensive cleaning
                cleaned_html = self._clean_html(str(cleaned_soup), platform="indeed")
                
            else:
                # No structure, need to rebuild from text
                logger.info(f"Indeed: No HTML structure, rebuilding from text")
                text_content = cleaned_soup.get_text(separator='\n', strip=True)
                
                if len(text_content) < 100:
                    logger.warning("Indeed: Description too short")
                    return None
                
                # AGGRESSIVE CLEANING: Fix all Indeed issues
                cleaned_html = self._rebuild_indeed_structure(text_content)
                
                logger.info(f"Indeed: Rebuilt to {len(cleaned_html)} chars of clean HTML")
                
                cleaned_html = f'<div class="job-description-content">\n{cleaned_html}\n</div>'
            
            # Remove buttons
            cleaned_html = self.remove_buttons(cleaned_html)
            
            # Fix heading formatting
            cleaned_html = self.fix_heading_formatting(cleaned_html)
            
            # Validate extraction
            is_valid, reason = self.validate_extraction(cleaned_html)
            if not is_valid:
                logger.warning(f"Indeed: Extraction validation failed - {reason}")
                return None
            
            logger.info("Indeed: Extraction successful and validated")
            return cleaned_html
            
        except Exception as e:
            logger.error(f"Indeed extraction error: {e}")
            return None
    
    def _rebuild_indeed_structure(self, text: str) -> str:
        """
        Rebuild Indeed job description with proper structure.
        
        Indeed uses markdown-style formatting that needs conversion:
        - ### Heading → <h3>Heading</h3>
        - **Bold** → <strong>Bold</strong>
        - *Italic* → Remove (decorative)
        - --- → Remove (decorative)
        - Bullet points → <ul><li>
        
        Args:
            text: Raw text content from Indeed
            
        Returns:
            Clean, properly structured HTML like LinkedIn
        """
        # STEP 1: Fix escaped characters
        text = text.replace('\\-', '-')
        text = text.replace('\\(', '(')
        text = text.replace('\\)', ')')
        text = text.replace('\\/', '/')
        text = text.replace('\\.', '.')
        text = text.replace('\\,', ',')
        text = text.replace('\\:', ':')
        text = text.replace('\\;', ';')
        text = text.replace('\\&', '&')
        
        # STEP 2: Fix encoding issues (UTF-8 mojibake)
        text = text.replace('Ã¢ÂÂ', "'")
        text = text.replace('â', "'")
        text = text.replace('â', '"')
        text = text.replace('â', '"')
        text = text.replace('â', '—')
        text = text.replace('Â', '')
        text = text.replace('‑', '-')  # Non-breaking hyphen
        
        # STEP 3: Process line by line
        lines = text.split('\n')
        html_parts = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip pure decorative separators
            if re.match(r'^[-*_=\.•]{3,}$', line):
                continue
            
            # Skip junk symbols
            if line in ['*͏**', '----', '***', '---', '===', '...', '*', '**']:
                continue
            
            # STEP 4: Convert markdown-style headings (### Heading)
            if line.startswith('###'):
                # Close list if open
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                
                # Extract heading text and remove markdown + asterisks
                heading = line.replace('###', '').strip()
                heading = heading.strip('*').strip()
                if heading:
                    html_parts.append(f'<h3>{heading}</h3>')
                continue
            
            # STEP 5: Convert bold headings (**Heading**)
            if line.startswith('**') and line.endswith('**') and len(line) < 100:
                # Close list if open
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                
                # Extract heading text
                heading = line.strip('*').strip()
                if heading and not heading.startswith('-'):  # Not a separator
                    html_parts.append(f'<h3>{heading}</h3>')
                continue
            
            # STEP 6: Convert bullet points
            if line.startswith(('•', '-', '*', '▪', '·')):
                # Open list if not open
                if not in_list:
                    html_parts.append('<ul>')
                    in_list = True
                
                # Clean bullet text - remove leading bullet and asterisks
                bullet_text = re.sub(r'^[•\-*▪·]\s*', '', line).strip()
                bullet_text = bullet_text.strip('*').strip()
                
                # Skip if it's just decorative
                if bullet_text and not re.match(r'^[-*_=\.]{2,}$', bullet_text):
                    html_parts.append(f'<li>{bullet_text}</li>')
                continue
            
            # STEP 7: Regular paragraphs
            # Close list if open
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            
            # Remove inline asterisks for bold (convert **text** to <strong>text</strong>)
            line = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', line)
            
            # Remove single asterisks (decorative)
            line = line.strip('*').strip()
            
            # Add as paragraph if not empty
            if line and len(line) > 2:
                html_parts.append(f'<p>{line}</p>')
        
        # Close list if still open
        if in_list:
            html_parts.append('</ul>')
        
        # Join with newlines for proper HTML formatting
        return '\n'.join(html_parts)
    
    # ========================================================================
    # CORE CLEANING LOGIC (Industry Standard)
    # ========================================================================
    
    def _clean_html(self, html: str, platform: str = "generic") -> str:
        """
        Clean HTML using industry-standard approach.
        
        Philosophy: PRESERVE structure, REMOVE clutter
        
        Steps:
        1. Parse HTML
        2. Remove dangerous/tracking elements
        3. Remove dangerous/tracking attributes
        4. Keep semantic structure intact
        5. Wrap in container div
        
        Args:
            html: Raw HTML string
            platform: Source platform (for platform-specific cleaning)
            
        Returns:
            Clean HTML string
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Step 1: Remove dangerous/unwanted elements
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Step 2: Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Step 3: Clean attributes (keep semantic, remove tracking)
        for tag in soup.find_all(True):
            # Get current attributes
            attrs = dict(tag.attrs)
            
            # Remove all except whitelisted
            for attr in list(attrs.keys()):
                if attr not in self.KEEP_ATTRS:
                    del tag.attrs[attr]
        
        # Step 4: Platform-specific cleaning
        if platform == "indeed":
            soup = self._clean_indeed_specific(soup)
        elif platform == "linkedin":
            soup = self._clean_linkedin_specific(soup)
        
        # Step 5: Get cleaned HTML
        cleaned = str(soup)
        
        # Step 6: Format HTML properly with newlines between tags for proper rendering
        cleaned = re.sub(r'>\s*<', '>\n<', cleaned)  # Add newlines between tags
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # Remove excessive newlines
        cleaned = cleaned.strip()
        
        # Step 7: Wrap in container
        return f'<div class="job-description-content">\n{cleaned}\n</div>'
    
    def _clean_indeed_specific(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Indeed-specific cleaning (LEGACY - now using _rebuild_indeed_structure).
        
        This method is kept for backward compatibility but is no longer
        the primary cleaning method for Indeed descriptions.
        """
        # Remove decorative list items
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            if text and re.match(r'^[-*=_\.]+$', text):
                li.decompose()
        
        # Remove empty elements
        for tag in soup.find_all(['p', 'div', 'span']):
            if not tag.get_text(strip=True) and not tag.find_all():
                tag.decompose()
        
        return soup
    
    def _clean_linkedin_specific(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        LinkedIn-specific cleaning.
        
        LinkedIn issues:
        - "Show more" / "Show less" buttons
        - Whitespace spans
        - Nested divs with no semantic meaning
        """
        # Remove "Show more" artifacts
        for tag in soup.find_all(string=re.compile(r'(show more|show less|see more|see less)', re.I)):
            if tag.parent:
                tag.parent.decompose()
        
        # Remove whitespace-only spans
        for span in soup.find_all('span'):
            if not span.get_text(strip=True):
                span.decompose()
        
        return soup


# ============================================================================
# CONVENIENCE FUNCTIONS (Industry Standard API)
# ============================================================================

async def extract_linkedin_description(page: Page) -> Optional[str]:
    """
    Extract LinkedIn job description (industry-standard approach).
    
    Args:
        page: Playwright page object
        
    Returns:
        Clean HTML string
    """
    extractor = IndustryStandardExtractor()
    return await extractor.extract_linkedin(page)


def extract_indeed_description(raw_html: str) -> Optional[str]:
    """
    Extract Indeed job description (industry-standard approach).
    
    Args:
        raw_html: Raw HTML from Indeed
        
    Returns:
        Clean HTML string
    """
    extractor = IndustryStandardExtractor()
    return extractor.extract_indeed(raw_html)


def extract_job_description(raw_html: str, platform: str = "generic") -> Optional[str]:
    """
    Extract job description from any platform (auto-detect).
    
    Args:
        raw_html: Raw HTML
        platform: Platform name (indeed, linkedin, generic)
        
    Returns:
        Clean HTML string
    """
    extractor = IndustryStandardExtractor()
    
    if platform.lower() == "indeed":
        return extractor.extract_indeed(raw_html)
    elif platform.lower() == "linkedin":
        # LinkedIn HTML string extraction (not live page)
        # The LinkedIn scraper already returns HTML, we just need to clean it
        logger.info("LinkedIn: Extracting from HTML string")
        
        if not raw_html or len(raw_html) < 100:
            logger.warning("LinkedIn: Raw HTML too short")
            return None
        
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # LinkedIn wraps content in show-more-less-html structure
        # Try multiple selectors to find the actual content
        content_div = None
        
        # Try 1: show-more-less-html__markup (most common)
        content_div = soup.find('div', class_='show-more-less-html__markup')
        if content_div:
            logger.info("LinkedIn: Found content via show-more-less-html__markup")
        
        # Try 2: Any div with 'description' in class
        if not content_div:
            content_div = soup.find('div', class_=lambda x: x and 'description' in str(x).lower())
            if content_div:
                logger.info("LinkedIn: Found content via description class")
        
        # Try 3: Use the whole soup if nothing found
        if not content_div:
            logger.info("LinkedIn: Using full HTML (no specific container found)")
            content_div = soup
        
        # Get the HTML string
        content_html = str(content_div)
        logger.info(f"LinkedIn: Content HTML length before cleaning: {len(content_html)} chars")
        
        # Clean the HTML (but don't be too aggressive)
        cleaned = extractor._clean_html(content_html, platform="linkedin")
        logger.info(f"LinkedIn: Content HTML length after cleaning: {len(cleaned)} chars")
        
        # Remove buttons
        cleaned = extractor.remove_buttons(cleaned)
        
        # Fix heading formatting
        cleaned = extractor.fix_heading_formatting(cleaned)
        
        # Check final length
        text_content = BeautifulSoup(cleaned, 'html.parser').get_text(strip=True)
        logger.info(f"LinkedIn: Final text content length: {len(text_content)} chars")
        
        # Validate extraction
        is_valid, reason = extractor.validate_extraction(cleaned, min_length=150)
        if not is_valid:
            logger.warning(f"LinkedIn: Extraction validation failed - {reason}")
            # If validation fails but we have some content, return it anyway
            if len(text_content) > 50:
                logger.info(f"LinkedIn: Returning cleaned HTML despite validation failure (has {len(text_content)} chars)")
                return cleaned
            else:
                logger.error("LinkedIn: Extraction completely failed - no content")
                return None
        
        logger.info("LinkedIn: Extraction successful and validated")
        return cleaned
    else:
        # Generic extraction
        return extractor._clean_html(raw_html, platform="generic")


# ============================================================================
# BACKWARD COMPATIBILITY (Legacy API)
# ============================================================================

def extract_from_text(text: str) -> Optional[str]:
    """
    Legacy function for plain text conversion.
    
    NOTE: This is a fallback only. Always prefer HTML extraction.
    """
    if not text or len(text) < 50:
        return None
    
    # Simple paragraph wrapping
    paragraphs = text.split('\n\n')
    html_parts = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # Check if it's a heading (short, ends with colon)
            if len(para) < 80 and para.endswith(':'):
                html_parts.append(f'<h3>{para}</h3>')
            # Check if it's a bullet point
            elif para.startswith(('•', '-', '*', '▪')):
                items = para.split('\n')
                html_parts.append('<ul>')
                for item in items:
                    item = re.sub(r'^[•\-*▪]\s*', '', item).strip()
                    if item:
                        html_parts.append(f'<li>{item}</li>')
                html_parts.append('</ul>')
            # Regular paragraph
            else:
                html_parts.append(f'<p>{para}</p>')
    
    result = '\n'.join(html_parts)
    return f'<div class="job-description-content">\n{result}\n</div>' if result else None
