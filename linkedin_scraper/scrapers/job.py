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
        """
        Extract complete job description from LinkedIn.
        Returns formatted HTML with proper structure.
        """
        try:
            # Find "About the job" section
            about_heading = self.page.locator('h2:has-text("About the job")').first
            if await about_heading.count() > 0:
                # Get parent container
                parent = about_heading.locator('xpath=ancestor::div[@class][2]')
                if await parent.count() > 0:
                    # Get all text
                    text = await parent.inner_text()
                    if text and len(text) > 100:
                        # Format it properly
                        return self._format_description_text(text)
            
            # Fallback: Get main content
            main_content = self.page.locator('main').first
            if await main_content.count() > 0:
                text = await main_content.inner_text()
                if 'About the job' in text:
                    description = text.split('About the job')[1] if 'About the job' in text else text
                    if description and len(description) > 100:
                        return self._format_description_text(description.strip())
            
            return None
        except Exception as e:
            logger.error(f"Error extracting description: {e}")
            return None

    def _format_description_text(self, text: str) -> str:
        """
        Convert plain text to formatted HTML with clear structure.
        ONLY removes the very first heading artifact (About the job, Job Description, etc.)
        Preserves ALL subheadings within the JD.
        """
        if not text:
            return None

        # ONLY the topmost headings to filter out (scraping artifacts at the start)
        top_headings_to_remove = [
            'about the job',
            'job description',
            'company description',
            'about us',
            'about our company',
            'about the role',
        ]

        lines = text.split('\n')
        html_parts = []
        current_list = []
        current_paragraph = []
        first_heading_removed = False

        # Emoji markers for sections
        section_emojis = ['📌', '📍', '🏢', '🕒', '🔎', '💰', '👤', '✅', '⭐', '🎯', '📋', '💼']

        for line in lines:
            line = line.strip()

            # Skip empty lines - they separate sections
            if not line:
                # Save current paragraph
                if current_paragraph:
                    html_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
                # Save current list
                if current_list:
                    html_parts.append('<ul>' + ''.join(f'<li>{item}</li>' for item in current_list) + '</ul>')
                    current_list = []
                continue

            # Check if this is a heading artifact (ONLY at the very beginning)
            is_heading_artifact = (
                not first_heading_removed and
                any(line.lower() == heading or line.lower().startswith(heading + ':') 
                    for heading in top_headings_to_remove)
            )

            if is_heading_artifact:
                # Skip ONLY the first heading artifact
                first_heading_removed = True
                continue

            # Check for section headers (emoji, ALL CAPS, or ends with :)
            is_header = (
                any(line.startswith(emoji) for emoji in section_emojis) or
                (line.isupper() and len(line) > 3 and len(line) < 100) or
                line.endswith(':')
            )

            if is_header:
                # Save current content first
                if current_paragraph:
                    html_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
                if current_list:
                    html_parts.append('<ul>' + ''.join(f'<li>{item}</li>' for item in current_list) + '</ul>')
                    current_list = []
                # Add header
                html_parts.append(f'<h3>{line}</h3>')

            # Check for bullet points
            elif line.startswith(('•', '▪', '▸', '◦', '-', '*', '➤')):
                if current_paragraph:
                    html_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
                current_list.append(line[1:].strip())
            
            # Check for numbered lists
            elif len(line) > 3 and line[0].isdigit() and '.' in line[:3]:
                if current_paragraph:
                    html_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
                current_list.append(line.split('. ', 1)[-1] if '. ' in line else line)
            
            # Regular text - add to paragraph
            else:
                if current_list:
                    html_parts.append('<ul>' + ''.join(f'<li>{item}</li>' for item in current_list) + '</ul>')
                    current_list = []
                current_paragraph.append(line)
        
        # Don't forget remaining content
        if current_paragraph:
            html_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
        if current_list:
            html_parts.append('<ul>' + ''.join(f'<li>{item}</li>' for item in current_list) + '</ul>')
        
        result = '\n\n'.join(html_parts)
        return result if result and len(result) > 50 else None
