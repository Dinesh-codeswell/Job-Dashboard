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
    Industry-standard job description extractor.
    
    Follows the "preserve, don't transform" philosophy used by top job boards.
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
    
    def __init__(self):
        """Initialize extractor."""
        pass
    
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
        
        Args:
            page: Playwright page object
            
        Returns:
            Clean HTML string preserving original structure
        """
        try:
            # Wait for content to load
            await page.wait_for_selector('h2:has-text("About the job")', timeout=10000)
            
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
            return self._clean_html(raw_html, platform="linkedin")
            
        except Exception as e:
            logger.error(f"LinkedIn extraction error: {e}")
            return None
    
    # ========================================================================
    # INDEED EXTRACTION (HTML-based)
    # ========================================================================
    
    def extract_indeed(self, raw_html: str) -> Optional[str]:
        """
        Extract Indeed job description using industry-standard approach.
        
        Indeed Structure:
        - Main container: div#jobDescriptionText
        - Content: Nested HTML with headings, lists, paragraphs
        - Strategy: Find container, extract inner HTML, clean minimally
        
        Args:
            raw_html: Raw HTML from Indeed
            
        Returns:
            Clean HTML string preserving original structure
        """
        try:
            if not raw_html or len(raw_html) < 50:
                return None
            
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Find description container
            container = (
                soup.find('div', {'id': 'jobDescriptionText'}) or
                soup.find('div', class_=lambda x: x and 'jobsearch-jobDescriptionText' in str(x)) or
                soup.find('div', class_=lambda x: x and 'description' in str(x).lower())
            )
            
            if not container:
                logger.warning("Indeed: Description container not found")
                return None
            
            # CRITICAL FIX: Get inner HTML, not str(container)
            # str(container) includes the outer div, we want ONLY the content
            inner_html = ''.join(str(child) for child in container.children)
            
            if len(inner_html) < 100:
                logger.warning("Indeed: Description too short")
                return None
            
            # Clean and return
            return self._clean_html(inner_html, platform="indeed")
            
        except Exception as e:
            logger.error(f"Indeed extraction error: {e}")
            return None
    
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
        
        # Step 6: Remove excessive whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        # Step 7: Wrap in container
        return f'<div class="job-description-content">\n{cleaned}\n</div>'
    
    def _clean_indeed_specific(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Indeed-specific cleaning.
        
        Indeed issues:
        - Decorative separators (dashes, asterisks)
        - Empty divs
        - Redundant spans
        """
        # Remove decorative list items
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            if text and re.match(r'^[-*=_\.]+$', text):
                li.decompose()
        
        # Remove empty elements (but preserve structure)
        for tag in soup.find_all(['p', 'div', 'span']):
            # Only remove if truly empty (no children and no text)
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
        # LinkedIn requires Playwright, can't use raw HTML
        logger.warning("LinkedIn extraction requires Playwright page object")
        return None
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
