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
            # LinkedIn job pages have structure:
            # Line 0: Company Name
            # Line 1: (empty)
            # Line 2: Job Title
            # Line 3: (empty)
            # Line 4: Location · Time info
            
            try:
                main_content = self.page.locator('main').first
                if await main_content.count() > 0:
                    text = await main_content.inner_text()
                    lines = [line.strip() for line in text.split('\n')]
                    
                    # Filter out empty lines but keep track of original positions
                    non_empty_lines = []
                    for i, line in enumerate(lines):
                        if line:
                            non_empty_lines.append((i, line))
                    
                    # Look for company name followed by job title
                    for idx, (orig_idx, line) in enumerate(non_empty_lines):
                        # First non-empty line is usually company name
                        if idx == 0:
                            company_name = line
                            # Second non-empty line should be job title
                            if len(non_empty_lines) > 1:
                                job_title = non_empty_lines[1][1]
                                # Validate it's not employment type or location
                                skip_patterns = [
                                    'full-time', 'part-time', 'contract', 
                                    'united states', 'remote', 'ago', 
                                    'clicked', 'apply', 'save'
                                ]
                                job_title_lower = job_title.lower()
                                
                                # Check if job title is valid
                                if (len(job_title) > 3 and 
                                    len(job_title) < 150 and
                                    not any(pattern in job_title_lower for pattern in skip_patterns)):
                                    return job_title
            except Exception as e:
                pass
            
            # Try to find job title by looking for text after company link
            try:
                company_link = self.page.locator('a[href*="/company/"]').first
                if await company_link.count() > 0:
                    # Get parent element and find text after it
                    parent = company_link.locator('xpath=ancestor::*[3]')
                    if await parent.count() > 0:
                        text = await parent.inner_text()
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        for line in lines:
                            if line and len(line) > 3 and len(line) < 100:
                                # Skip employment types and common words
                                skip_words = ['full-time', 'part-time', 'contract', 'apply', 'save', 'share', 'ago']
                                if not any(word in line.lower() for word in skip_words):
                                    return line
            except:
                pass
            
            # Try h2 elements (LinkedIn sometimes uses h2 for job titles)
            h2_elements = await self.page.locator('h2').all()
            for elem in h2_elements:
                text = await elem.inner_text()
                text = text.strip()
                # Job title is usually not "About the job" or notifications
                skip_words = ['notification', 'about the job', 'full-time', 'part-time']
                if text and len(text) > 3 and len(text) < 100 and not any(w in text.lower() for w in skip_words):
                    return text
            
            # Fallback: try original selectors
            selectors = [
                'h1[data-test-job-title]',
                'h1.job-title',
                'h1',
                '.job-title h1',
                '[data-test-job-title]'
            ]
            
            for selector in selectors:
                try:
                    title_elem = self.page.locator(selector).first
                    if await title_elem.count() > 0:
                        title = await title_elem.inner_text()
                        title = title.strip()
                        if title and len(title) > 3:
                            return title
                except:
                    continue
            
            return None
        except:
            return None
    
    async def _get_company(self) -> Optional[str]:
        """Extract company name from company link."""
        try:
            # Find company links that have text (not just images)
            company_links = await self.page.locator('a[href*="/company/"]').all()
            for link in company_links:
                text = await link.inner_text()
                text = text.strip()
                # Skip empty or very short text (likely image-only links)
                if text and len(text) > 1 and not text.startswith('logo'):
                    return text
        except:
            pass
        return None

    async def _get_employment_type(self) -> Optional[str]:
        """Extract employment type (Full-time/Part-time/Remote etc.)."""
        try:
            # Get all text from main content
            main_content = self.page.locator('main').first
            if await main_content.count() > 0:
                text = await main_content.inner_text()
                lines = [line.strip().lower() for line in text.split('\n')]
                
                # Look for employment type patterns
                employment_types = ['full-time', 'part-time', 'contract', 'temporary', 'internship', 'freelance']
                
                for line in lines:
                    for emp_type in employment_types:
                        if emp_type in line:
                            # Return capitalized version
                            return emp_type.replace('-', ' ').title()
                
                # Also check for "Remote" as employment type indicator
                for line in lines:
                    if 'remote' in line and len(line) < 20:
                        return 'Remote'
            
            # Fallback: check specific elements
            text_elements = await self.page.locator('span, div').all()
            for elem in text_elements:
                try:
                    text = await elem.inner_text()
                    text_lower = text.strip().lower()
                    
                    for emp_type in ['full-time', 'part-time', 'contract', 'temporary', 'internship']:
                        if emp_type in text_lower:
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
            # Look for location text in the page
            text_elements = await self.page.locator('span, div').all()
            for elem in text_elements:
                try:
                    text = await elem.inner_text()
                    text = text.strip()
                    # Check for location patterns
                    if text and len(text) > 3 and len(text) < 100:
                        if (',' in text or 
                            'Remote' in text or 
                            'United States' in text or
                            'US' == text or
                            'Worldwide' in text or
                            'Europe' in text):
                            # Skip if it looks like a salary or other info
                            if not text.startswith('$') and 'per year' not in text.lower():
                                return text
                except:
                    continue
            
            # Fallback: try original approach
            try:
                main_content = self.page.locator('main').first
                if await main_content.count() > 0:
                    text = await main_content.inner_text()
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and (',' in line or 'Remote' in line or 'United States' in line):
                            if len(line) > 3 and len(line) < 100 and not line.startswith('$'):
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
        """Extract complete job description from page."""
        try:
            # Method 1: Find "About the job" section and get all text after it
            about_heading = self.page.locator('h2:has-text("About the job")').first
            if await about_heading.count() > 0:
                # Get the parent section containing the description
                parent = about_heading.locator('xpath=ancestor::*[2]')
                if await parent.count() > 0:
                    # Get all text content from the parent
                    description = await parent.inner_text()
                    # Clean up the description
                    lines = description.split('\n')
                    cleaned_lines = []
                    in_description = False
                    
                    for line in lines:
                        line = line.strip()
                        if 'About the job' in line:
                            in_description = True
                            continue
                        if in_description and line:
                            cleaned_lines.append(line)
                    
                    if cleaned_lines:
                        return '\n'.join(cleaned_lines)
            
            # Method 2: Look for article element with job description
            articles = await self.page.locator('article').all()
            for article in articles:
                text = await article.inner_text()
                if text and len(text) > 500:  # Job descriptions are typically long
                    # Check if it contains typical job description keywords
                    if any(word in text.lower() for word in ['responsibilities', 'requirements', 'qualifications', 'benefits', 'about the job']):
                        return text.strip()
            
            # Method 3: Get all text from main content after "About the job"
            try:
                main_content = self.page.locator('main').first
                if await main_content.count() > 0:
                    text = await main_content.inner_text()
                    # Find "About the job" and get everything after it
                    if 'About the job' in text:
                        description = text.split('About the job')[1]
                        # Clean up extra whitespace
                        lines = [line.strip() for line in description.split('\n') if line.strip()]
                        if lines:
                            return '\n'.join(lines)
            except:
                pass
            
            # Method 4: Fallback - get all text from the page (excluding header/nav)
            try:
                # Remove navigation and header elements
                content = self.page.locator('main')
                if await content.count() > 0:
                    text = await content.inner_text()
                    # Skip first few lines (company, title, location)
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    # Start from after location/time info
                    start_idx = 0
                    for i, line in enumerate(lines):
                        if 'ago' in line.lower() or 'clicked' in line.lower() or 'apply' in line.lower():
                            start_idx = i + 1
                            break
                    
                    if start_idx < len(lines):
                        description = '\n'.join(lines[start_idx:])
                        if len(description) > 200:  # Ensure it's substantial
                            return description
            except:
                pass
            
            return None
        except Exception as e:
            return None
