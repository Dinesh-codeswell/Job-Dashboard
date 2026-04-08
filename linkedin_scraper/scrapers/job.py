"""
Job scraper for LinkedIn.

Extracts job posting information from LinkedIn job pages.
"""
import logging
from typing import Optional
from playwright.async_api import Page

from ..models.job import Job
from ..core.exceptions import ProfileNotFoundError
from ..callbacks import ProgressCallback, SilentCallback
from .base import BaseScraper

logger = logging.getLogger(__name__)


class JobScraper(BaseScraper):
    """
    Scraper for LinkedIn job postings.
    
    Example:
        async with BrowserManager() as browser:
            scraper = JobScraper(browser.page)
            job = await scraper.scrape("https://www.linkedin.com/jobs/view/123456/")
            print(job.to_json())
    """
    
    def __init__(self, page: Page, callback: Optional[ProgressCallback] = None):
        """
        Initialize job scraper.
        
        Args:
            page: Playwright page object
            callback: Optional progress callback
        """
        super().__init__(page, callback or SilentCallback())
    
    async def scrape(self, linkedin_url: str) -> Job:
        """
        Scrape a LinkedIn job posting.
        
        Args:
            linkedin_url: URL of the LinkedIn job posting
            
        Returns:
            Job object with scraped data
            
        Raises:
            ProfileNotFoundError: If job posting not found
        """
        logger.info(f"Starting job scraping: {linkedin_url}")
        await self.callback.on_start("Job", linkedin_url)
        
        # Navigate to job page
        await self.navigate_and_wait(linkedin_url)
        await self.callback.on_progress("Navigated to job page", 10)
        
        # Check if page exists
        await self.check_rate_limit()
        
        # Extract job details
        job_title = await self._get_job_title()
        await self.callback.on_progress(f"Got job title: {job_title}", 20)

        company = await self._get_company()
        await self.callback.on_progress("Got company name", 30)

        company_logo = await self._get_company_logo()
        await self.callback.on_progress("Got company logo", 35)

        employment_type = await self._get_employment_type()
        await self.callback.on_progress(f"Got employment type: {employment_type}", 40)

        location = await self._get_location()
        await self.callback.on_progress("Got location", 50)

        posted_date = await self._get_posted_date()
        await self.callback.on_progress("Got posted date", 60)

        job_description = await self._get_description()
        await self.callback.on_progress("Got job description", 80)

        # Create job object
        job = Job(
            linkedin_url=linkedin_url,
            job_title=job_title,
            company=company,
            company_logo=company_logo,
            employment_type=employment_type,
            location=location,
            posted_date=posted_date,
            job_description=job_description
        )
        
        await self.callback.on_progress("Scraping complete", 100)
        await self.callback.on_complete("Job", job)
        
        logger.info(f"Successfully scraped job: {job_title}")
        return job
    
    async def _get_job_title(self) -> Optional[str]:
        """Extract job title from page."""
        try:
            # FIXED: Use specific selectors for LinkedIn's current layout
            # Try specific job title selectors first (most reliable)
            title_selectors = [
                'h1.top-card-layout__title',  # New LinkedIn layout (PRIMARY)
                'h1.t-24.t-bold',  # Alternative layout
                'h2.top-card-layout__title',  # Sometimes uses h2
                'h1[class*="job"]',  # Fallback with "job" in class
                'h1[data-test-job-title]',  # Old layout
                'h1.job-title',  # Old layout
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = self.page.locator(selector).first
                    if await title_elem.count() > 0:
                        title = await title_elem.inner_text()
                        title = title.strip()
                        # Validate it's not company name or location
                        # Company names often have "  Location" pattern
                        if title and len(title) > 3 and len(title) < 150:
                            # Skip if it looks like "Company  Location" format
                            if '  ' in title and (',' in title or 'India' in title):
                                continue
                            # Skip if it's obviously a location
                            if any(city in title for city in ['Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai', 'Gurugram', 'Ahmedabad']):
                                continue
                            return title
                except:
                    continue
            
            # Fallback: Try h1 elements and validate
            h1_elements = await self.page.locator('h1').all()
            for elem in h1_elements:
                try:
                    text = await elem.inner_text()
                    text = text.strip()
                    if text and len(text) > 3 and len(text) < 150:
                        # Skip if it looks like "Company  Location" format
                        if '  ' in text and (',' in text or 'India' in text):
                            continue
                        # Skip if it's obviously a location
                        if any(city in text for city in ['Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai', 'Gurugram', 'Ahmedabad']):
                            continue
                        # Skip common non-title text
                        skip_words = ['notification', 'about the job', 'full-time', 'part-time', 'apply', 'save']
                        if not any(w in text.lower() for w in skip_words):
                            return text
                except:
                    continue
            
            # Last resort: Parse main content carefully
            try:
                main_content = self.page.locator('main').first
                if await main_content.count() > 0:
                    text = await main_content.inner_text()
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    # Look for a line that looks like a job title
                    # (not company, not location, not employment type)
                    for line in lines[:10]:  # Check first 10 lines only
                        if len(line) > 3 and len(line) < 150:
                            # Skip if it looks like "Company  Location"
                            if '  ' in line and (',' in line or 'India' in line):
                                continue
                            # Skip locations
                            if any(city in line for city in ['Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai', 'Gurugram', 'Ahmedabad']):
                                continue
                            # Skip employment types
                            skip_patterns = ['full-time', 'part-time', 'contract', 'ago', 'clicked', 'apply', 'save', 'share']
                            if any(pattern in line.lower() for pattern in skip_patterns):
                                continue
                            # This might be the job title
                            return line
            except:
                pass
            
            return None
        except:
            return None
    
    async def _get_company(self) -> Optional[str]:
        """Extract company name from company link."""
        try:
            # FIXED: More precise selectors for company name
            # Try specific selectors first (most reliable)
            company_selectors = [
                'a.topcard__org-name-link',  # New LinkedIn layout
                'a[data-tracking-control-name*="public_jobs_topcard-org-name"]',
                'a[href*="/company/"].topcard__flavor',
                'span.topcard__flavor a[href*="/company/"]',
            ]
            
            for selector in company_selectors:
                try:
                    elem = self.page.locator(selector).first
                    if await elem.count() > 0:
                        text = await elem.inner_text()
                        text = text.strip()
                        # Clean up: remove location if accidentally included
                        if text and len(text) > 1:
                            # Remove common location patterns
                            text = text.split('\n')[0].strip()  # Take first line only
                            # Remove trailing location info (e.g., "Company  Location")
                            if '  ' in text:
                                text = text.split('  ')[0].strip()
                            return text
                except:
                    continue
            
            # Fallback: Find company links that have text (not just images)
            company_links = await self.page.locator('a[href*="/company/"]').all()
            for link in company_links:
                text = await link.inner_text()
                text = text.strip()
                # Skip empty or very short text (likely image-only links)
                if text and len(text) > 1 and not text.startswith('logo'):
                    # Clean up: remove location if accidentally included
                    text = text.split('\n')[0].strip()  # Take first line only
                    if '  ' in text:
                        text = text.split('  ')[0].strip()
                    # Skip if it looks like a location (has comma or "India")
                    if ',' not in text and 'India' not in text:
                        return text
        except:
            pass
        return None

    async def _get_company_logo(self) -> Optional[str]:
        """Extract company logo image URL."""
        try:
            # Method 1: Find logo image in company link
            company_links = await self.page.locator('a[href*="/company/"]').all()
            for link in company_links:
                # Look for img tags within the company link
                images = await link.locator('img').all()
                for img in images:
                    try:
                        # Try different attributes that might contain the logo URL
                        logo_url = await img.get_attribute('src')
                        if logo_url and logo_url.strip():
                            # Clean up the URL
                            if logo_url.startswith('//'):
                                logo_url = 'https:' + logo_url
                            elif not logo_url.startswith('http'):
                                logo_url = f'https://www.linkedin.com{logo_url}'
                            return logo_url
                    except:
                        continue
                
                # Method 2: Check for background-image or style attributes
                try:
                    style = await link.get_attribute('style')
                    if style and 'background-image' in style:
                        import re
                        match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                        if match:
                            logo_url = match.group(1)
                            if logo_url.startswith('//'):
                                logo_url = 'https:' + logo_url
                            elif not logo_url.startswith('http'):
                                logo_url = f'https://www.linkedin.com{logo_url}'
                            return logo_url
                except:
                    continue
            
            # Method 3: Look for any logo images on the page
            logo_selectors = [
                'img[src*="logo"]',
                'img[alt*="logo"]',
                'img[data-test-logo]',
                '[data-test-company-logo] img',
                '.company-logo img'
            ]
            
            for selector in logo_selectors:
                try:
                    img = self.page.locator(selector).first
                    if await img.count() > 0:
                        logo_url = await img.get_attribute('src')
                        if logo_url and logo_url.strip():
                            if logo_url.startswith('//'):
                                logo_url = 'https:' + logo_url
                            elif not logo_url.startswith('http'):
                                logo_url = f'https://www.linkedin.com{logo_url}'
                            return logo_url
                except:
                    continue
            
            return None
        except:
            return None

    async def _get_employment_type(self) -> Optional[str]:
        """Extract employment type (Full-time/Part-time/Remote/Internship etc.)."""
        try:
            # Get all text from main content
            main_content = self.page.locator('main').first
            if await main_content.count() > 0:
                text = await main_content.inner_text()
                lines = [line.strip().lower() for line in text.split('\n')]

                # Look for employment type patterns - CHECK INTERNSHIP FIRST
                employment_types = ['internship', 'full-time', 'part-time', 'contract', 'temporary', 'freelance']

                for line in lines:
                    for emp_type in employment_types:
                        if emp_type in line:
                            # Return capitalized version
                            if emp_type == 'internship':
                                return 'Internship'
                            return emp_type.replace('-', ' ').title()

                # Also check for "Intern" in job title (backup for internship detection)
                try:
                    job_title = await self._get_job_title()
                    if job_title and 'intern' in job_title.lower():
                        return 'Internship'
                except:
                    pass

                # Fallback: check specific elements
                text_elements = await self.page.locator('span, div').all()
                for elem in text_elements:
                    try:
                        text = await elem.inner_text()
                        text_lower = text.strip().lower()

                        for emp_type in employment_types:
                            if emp_type in text_lower:
                                if emp_type == 'internship':
                                    return 'Internship'
                                return emp_type.replace('-', ' ').title()

                        if 'remote' in text_lower and len(text.strip()) < 20:
                            return 'Remote'
                    except:
                        continue

                return None
        except:
            return None

    async def _get_company_url(self) -> Optional[str]:
        """Extract company LinkedIn URL."""
        try:
            company_link = self.page.locator('a[href*="/company/"]').first
            if await company_link.count() > 0:
                href = await company_link.get_attribute('href')
                if href:
                    if '?' in href:
                        href = href.split('?')[0]
                    if not href.startswith('http'):
                        href = f"https://www.linkedin.com{href}"
                    return href
        except:
            pass
        return None
    
    async def _get_location(self) -> Optional[str]:
        """Extract job location from job details panel."""
        try:
            # FIXED: More precise location extraction
            # Try specific location selectors first
            location_selectors = [
                'span.topcard__flavor--bullet',  # New LinkedIn layout
                'span[class*="job-details-jobs-unified-top-card__bullet"]',
                'div[class*="job-details-jobs-unified-top-card__primary-description"] span',
            ]
            
            for selector in location_selectors:
                try:
                    elems = await self.page.locator(selector).all()
                    for elem in elems:
                        text = await elem.inner_text()
                        text = text.strip()
                        # Check if it looks like a location (has comma or known location keywords)
                        if text and len(text) > 3 and len(text) < 100:
                            if (',' in text or 
                                'Remote' in text or 
                                'India' in text or
                                'United States' in text or
                                'Worldwide' in text or
                                'Europe' in text or
                                any(city in text for city in ['Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai', 'Gurugram', 'Gurgaon'])):
                                # Skip if it looks like a salary or other info
                                if not text.startswith('$') and 'per year' not in text.lower() and 'applicant' not in text.lower():
                                    # Clean up: remove company name if accidentally included
                                    if '  ' in text:
                                        # Take the part after double space (location part)
                                        parts = text.split('  ')
                                        for part in parts:
                                            if ',' in part or 'India' in part or 'Remote' in part:
                                                return part.strip()
                                    return text
                except:
                    continue
            
            # Fallback: Look for location text in the page
            text_elements = await self.page.locator('span, div').all()
            for elem in text_elements:
                try:
                    text = await elem.inner_text()
                    text = text.strip()
                    # Check for location patterns
                    if text and len(text) > 3 and len(text) < 100:
                        if (',' in text or 
                            'Remote' in text or 
                            'India' in text or
                            'United States' in text or
                            'US' == text or
                            'Worldwide' in text or
                            'Europe' in text):
                            # Skip if it looks like a salary or other info
                            if not text.startswith('$') and 'per year' not in text.lower():
                                # Clean up: remove company name if accidentally included
                                if '  ' in text:
                                    parts = text.split('  ')
                                    for part in parts:
                                        if ',' in part or 'India' in part or 'Remote' in part:
                                            return part.strip()
                                # Skip if it contains company name patterns
                                if not any(word in text for word in ['logo', 'company', 'about']):
                                    return text
                except:
                    continue
            
            # Last resort: try original approach
            try:
                main_content = self.page.locator('main').first
                if await main_content.count() > 0:
                    text = await main_content.inner_text()
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and (',' in line or 'Remote' in line or 'India' in line or 'United States' in line):
                            if len(line) > 3 and len(line) < 100 and not line.startswith('$'):
                                # Clean up
                                if '  ' in line:
                                    parts = line.split('  ')
                                    for part in parts:
                                        if ',' in part or 'India' in part or 'Remote' in part:
                                            return part.strip()
                                return line
            except:
                pass
                
            return None
        except:
            return None
    
    async def _get_posted_date(self) -> Optional[str]:
        """Extract posted date from job details."""
        try:
            text_elements = await self.page.locator('span, div').all()
            for elem in text_elements:
                text = await elem.inner_text()
                if text and ('ago' in text.lower() or 'day' in text.lower() or 'week' in text.lower() or 'hour' in text.lower()):
                    text = text.strip()
                    if len(text) < 50:
                        return text
        except:
            pass
        return None
    
    async def _get_applicant_count(self) -> Optional[str]:
        """Extract applicant count from job details."""
        try:
            main_content = self.page.locator('main').first
            if await main_content.count() > 0:
                text_elements = await main_content.locator('span, div').all()
                for elem in text_elements:
                    text = await elem.inner_text()
                    text = text.strip()
                    if text and len(text) < 50:
                        text_lower = text.lower()
                        if 'applicant' in text_lower or 'people clicked' in text_lower or 'applied' in text_lower:
                            return text
        except:
            pass
        return None
    
    async def _get_description(self) -> Optional[str]:
        """
        Extract pixel-perfect job description from LinkedIn.
        Uses advanced JobDescriptionExtractor for perfect formatting.
        """
        try:
            # Import the extractor
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from job_description_extractor import extract_linkedin_description
            
            # Use the pixel-perfect extractor
            description = await extract_linkedin_description(self.page)
            return description
            
        except Exception as e:
            logger.error(f"Error extracting description: {e}")
            # Fallback to basic extraction
            return await self._get_description_fallback()
    
    async def _get_description_fallback(self) -> Optional[str]:
        """Fallback description extraction if advanced extractor fails."""
        try:
            # Find "About the job" section
            about_heading = self.page.locator('h2:has-text("About the job")').first
            if await about_heading.count() > 0:
                parent = about_heading.locator('xpath=ancestor::div[@class][2]')
                if await parent.count() > 0:
                    text = await parent.inner_text()
                    if text and len(text) > 100:
                        return text.strip()
            
            # Fallback: Get main content
            main_content = self.page.locator('main').first
            if await main_content.count() > 0:
                text = await main_content.inner_text()
                if 'About the job' in text:
                    description = text.split('About the job')[1] if 'About the job' in text else text
                    if description and len(description) > 100:
                        return description.strip()
            
            return None
        except Exception as e:
            logger.error(f"Fallback extraction error: {e}")
            return None
