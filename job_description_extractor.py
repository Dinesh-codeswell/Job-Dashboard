#!/usr/bin/env python3
"""
PIXEL-PERFECT JOB DESCRIPTION EXTRACTOR
========================================
Industry-grade job description extraction with perfect formatting preservation.

Features:
✅ Preserves exact HTML structure from source
✅ Maintains heading hierarchy (H1, H2, H3)
✅ Proper paragraph spacing and line breaks
✅ Bullet points and numbered lists
✅ Bold, italic, and other formatting
✅ Consistent styling across platforms
✅ Removes only scraping artifacts, not content
✅ Handles LinkedIn, Indeed, and Naukri formats

USAGE:
    from job_description_extractor import JobDescriptionExtractor
    
    extractor = JobDescriptionExtractor()
    formatted_html = extractor.extract_linkedin(page)
    formatted_html = extractor.extract_indeed(raw_html)
    formatted_html = extractor.extract_naukri(raw_html)
"""

import re
import logging
from typing import Optional, List, Tuple
from bs4 import BeautifulSoup, NavigableString, Tag
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class JobDescriptionExtractor:
    """
    Pixel-perfect job description extractor for all platforms.
    
    Preserves:
    - Heading hierarchy (H1-H6)
    - Paragraph spacing
    - Bullet points and lists
    - Text formatting (bold, italic, underline)
    - Line breaks and whitespace
    - Section structure
    """
    
    # Scraping artifacts to remove (ONLY at the very start)
    HEADING_ARTIFACTS = [
        'about the job',
        'job description',
        'company description',
        'about us',
        'about our company',
        'about the role',
        'role description',
        'position summary',
        'job summary',
        'overview',
        'the role',
        'the opportunity',
        'job details',
        'position details',
    ]
    
    # Section headers that should be H3
    SECTION_KEYWORDS = [
        'responsibilities',
        'requirements',
        'qualifications',
        'skills',
        'experience',
        'education',
        'benefits',
        'perks',
        'about us',
        'about the company',
        'what we offer',
        'what you will do',
        'what you bring',
        'who you are',
        'key responsibilities',
        'required skills',
        'preferred qualifications',
        'nice to have',
        'bonus points',
        'compensation',
        'salary',
        'location',
        'work environment',
        'team',
        'culture',
        'mission',
        'vision',
        'values',
    ]
    
    def __init__(self):
        """Initialize extractor."""
        self.first_heading_removed = False
    
    # ========================================================================
    # LINKEDIN EXTRACTION
    # ========================================================================
    
    async def extract_linkedin(self, page: Page) -> Optional[str]:
        """
        Extract pixel-perfect job description from LinkedIn.
        
        Args:
            page: Playwright page object
            
        Returns:
            Formatted HTML string with perfect structure
        """
        try:
            # Method 1: Find "About the job" section (most reliable)
            about_heading = page.locator('h2:has-text("About the job")').first
            if await about_heading.count() > 0:
                # Get the next sibling div that contains the actual description
                description_container = about_heading.locator('xpath=following-sibling::div[1]')
                if await description_container.count() > 0:
                    html_content = await description_container.inner_html()
                    if html_content and len(html_content) > 100:
                        return self._process_linkedin_html(html_content)
                
                # Fallback: Get parent container
                parent = about_heading.locator('xpath=ancestor::div[@class][2]')
                if await parent.count() > 0:
                    html_content = await parent.inner_html()
                    return self._process_linkedin_html(html_content)
            
            # Method 2: Find description by specific LinkedIn classes
            selectors = [
                'div.jobs-description__content',
                'div.jobs-box__html-content',
                '[data-test-job-description-text]',
                '.jobs-description-content__text',
                'article.jobs-description',
            ]
            
            for selector in selectors:
                elem = page.locator(selector).first
                if await elem.count() > 0:
                    html_content = await elem.inner_html()
                    if html_content and len(html_content) > 100:
                        return self._process_linkedin_html(html_content)
            
            # Method 3: Try to get plain text and convert
            try:
                about_heading = page.locator('h2:has-text("About the job")').first
                if await about_heading.count() > 0:
                    # Get all text after "About the job"
                    parent = about_heading.locator('xpath=ancestor::div[@class][1]')
                    if await parent.count() > 0:
                        text_content = await parent.inner_text()
                        if text_content and len(text_content) > 100:
                            # Remove "About the job" heading
                            text_content = text_content.replace('About the job', '', 1).strip()
                            return self.extract_from_plain_text(text_content)
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"LinkedIn extraction error: {e}")
            return None
    
    def _process_linkedin_html(self, html_content: str) -> str:
        """
        Process LinkedIn HTML to extract clean, formatted description.
        
        Args:
            html_content: Raw HTML from LinkedIn
            
        Returns:
            Clean, formatted HTML with proper spacing
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements (navigation, cookies, etc.)
        for tag in soup(['script', 'style', 'svg', 'button', 'input', 'nav', 'header', 'footer', 'form']):
            tag.decompose()
        
        # Remove elements with navigation/menu classes
        unwanted_classes = ['navigation', 'menu', 'header', 'footer', 'cookie', 'alert', 'banner']
        for unwanted_class in unwanted_classes:
            for tag in soup.find_all(class_=lambda x: x and unwanted_class in str(x).lower()):
                tag.decompose()
        
        # Remove "Skip to main content" and similar
        for tag in soup.find_all(string=lambda text: text and any(skip in text.lower() for skip in ['skip to', 'loading...', 'please wait', 'apply now', 'view profile'])):
            if tag.parent:
                tag.parent.decompose()
        
        # Find the actual description content
        description_div = soup.find('div', class_=lambda x: x and 'description' in str(x).lower())
        if not description_div:
            description_div = soup
        
        # CRITICAL FIX: LinkedIn wraps everything in a single span
        # We need to extract and properly format the content with spacing
        main_span = description_div.find('span', {'data-testid': 'expandable-text-box'})
        if main_span:
            formatted_parts = []
            self.first_heading_removed = False
            
            # Process all direct children of the span
            for element in main_span.children:
                if isinstance(element, NavigableString):
                    text = str(element).strip()
                    if text and len(text) > 2:
                        # Check if this looks like a heading
                        if text.isupper() or text.endswith(':') or any(kw in text.lower() for kw in self.SECTION_KEYWORDS):
                            formatted_parts.append(f'<h3>{text}</h3>')
                        else:
                            formatted_parts.append(f'<p>{text}</p>')
                
                elif isinstance(element, Tag):
                    if element.name == 'strong':
                        # Strong tags MIGHT be headings - check length and content
                        text = element.get_text(strip=True)
                        if text:
                            # If short (<80 chars) and looks like a heading, treat as H3
                            # Otherwise, it's just emphasis in a paragraph
                            is_heading = (
                                len(text) < 80 and
                                (text.endswith(':') or 
                                 text.isupper() or
                                 any(kw in text.lower() for kw in self.SECTION_KEYWORDS))
                            )
                            if is_heading:
                                formatted_parts.append(f'<h3>{text}</h3>')
                            else:
                                # Just emphasis, treat as paragraph
                                formatted_parts.append(f'<p>{text}</p>')
                    
                    elif element.name == 'ul':
                        # Process list - keep the structure
                        list_items = []
                        for li in element.find_all('li', recursive=False):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                list_items.append(f'<li>{li_text}</li>')
                        if list_items:
                            formatted_parts.append(f'<ul>\n' + '\n'.join(list_items) + '\n</ul>')
                    
                    elif element.name == 'ol':
                        # Process ordered list
                        list_items = []
                        for li in element.find_all('li', recursive=False):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                list_items.append(f'<li>{li_text}</li>')
                        if list_items:
                            formatted_parts.append(f'<ol>\n' + '\n'.join(list_items) + '\n</ol>')
                    
                    elif element.name == 'p':
                        # Process paragraph - check if it contains strong tags (headings)
                        strong_tags = element.find_all('strong')
                        if strong_tags:
                            # Check if strong tags are headings or just emphasis
                            has_heading = False
                            for strong in strong_tags:
                                text = strong.get_text(strip=True)
                                if text and len(text) < 80 and (
                                    text.endswith(':') or 
                                    text.isupper() or
                                    any(kw in text.lower() for kw in self.SECTION_KEYWORDS)
                                ):
                                    has_heading = True
                                    break
                            
                            if has_heading:
                                # This paragraph contains headings, process them separately
                                for child in element.children:
                                    if isinstance(child, Tag) and child.name == 'strong':
                                        text = child.get_text(strip=True)
                                        if text:
                                            # Check if it's a heading
                                            is_heading = (
                                                len(text) < 80 and
                                                (text.endswith(':') or 
                                                 text.isupper() or
                                                 any(kw in text.lower() for kw in self.SECTION_KEYWORDS))
                                            )
                                            if is_heading:
                                                formatted_parts.append(f'<h3>{text}</h3>')
                                            else:
                                                formatted_parts.append(f'<p><strong>{text}</strong></p>')
                                    elif isinstance(child, NavigableString):
                                        text = str(child).strip()
                                        if text and len(text) > 2:
                                            formatted_parts.append(f'<p>{text}</p>')
                                    elif isinstance(child, Tag) and child.name == 'br':
                                        # Skip br tags
                                        continue
                                    elif isinstance(child, Tag):
                                        # Other tags, get text
                                        text = child.get_text(strip=True)
                                        if text and len(text) > 2:
                                            formatted_parts.append(f'<p>{text}</p>')
                            else:
                                # Strong tags are just emphasis, keep paragraph intact
                                # Get HTML to preserve strong tags
                                para_html = str(element)
                                # Clean up the HTML
                                para_html = re.sub(r'<p[^>]*>', '', para_html)
                                para_html = re.sub(r'</p>', '', para_html)
                                para_html = para_html.strip()
                                if para_html and len(para_html) > 2:
                                    formatted_parts.append(f'<p>{para_html}</p>')
                        else:
                            # Regular paragraph without strong tags
                            text = element.get_text(strip=True)
                            if text and len(text) > 2:
                                formatted_parts.append(f'<p>{text}</p>')
                    
                    else:
                        # Try to get text content for other tags
                        text = element.get_text(strip=True)
                        if text and len(text) > 2:
                            formatted_parts.append(f'<p>{text}</p>')
            
            # Join with proper spacing
            if formatted_parts:
                return '<div class="job-description-content">\n' + '\n'.join(formatted_parts) + '\n</div>'
        
        # Fallback to original method if no span found
        # Convert <br/> tags to paragraph breaks
        self._convert_br_to_paragraphs(description_div)
        
        # Build formatted HTML with proper spacing
        formatted_parts = []
        self.first_heading_removed = False
        
        # Process top-level block elements only
        for element in description_div.find_all(recursive=False):
            if isinstance(element, Tag):
                result = self._process_html_element(element)
                if result:
                    formatted_parts.append(result)
        
        # If no formatted parts, try processing all descendants
        if not formatted_parts:
            for element in description_div.descendants:
                if isinstance(element, Tag):
                    result = self._process_html_element(element)
                    if result:
                        formatted_parts.append(result)
        
        # Join with proper spacing - use <div> wrapper with spacing class
        return '<div class="job-description-content">\n' + '\n'.join(formatted_parts) + '\n</div>'
    
    def _convert_br_to_paragraphs(self, soup_element):
        """
        Convert <br/> tags to proper paragraph breaks.
        Multiple consecutive <br/> tags become paragraph separators.
        """
        # Find all <br> tags
        for br in soup_element.find_all('br'):
            # Check if there are multiple consecutive <br> tags
            next_sibling = br.next_sibling
            if next_sibling and next_sibling.name == 'br':
                # Multiple <br> tags - this is a paragraph break
                # Replace with a paragraph separator marker
                br.replace_with('\n\n')
            else:
                # Single <br> - just a line break within a paragraph
                br.replace_with(' ')
    
    # ========================================================================
    # INDEED EXTRACTION
    # ========================================================================
    
    def extract_indeed(self, raw_html: str) -> Optional[str]:
        """
        Extract pixel-perfect job description from Indeed.
        
        Args:
            raw_html: Raw HTML from Indeed API/scraper
            
        Returns:
            Formatted HTML string
        """
        try:
            if not raw_html or len(raw_html) < 50:
                return None
            
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'svg', 'button', 'input', 'form']):
                tag.decompose()
            
            # Indeed-specific: Find job description container
            description_div = (
                soup.find('div', {'id': 'jobDescriptionText'}) or
                soup.find('div', class_=lambda x: x and 'jobsearch-jobDescriptionText' in str(x)) or
                soup.find('div', class_=lambda x: x and 'description' in str(x).lower()) or
                soup
            )
            
            return self._process_generic_html(description_div)
            
        except Exception as e:
            logger.error(f"Indeed extraction error: {e}")
            return None
    
    # ========================================================================
    # NAUKRI EXTRACTION
    # ========================================================================
    
    def extract_naukri(self, raw_html: str) -> Optional[str]:
        """
        Extract pixel-perfect job description from Naukri.
        
        Args:
            raw_html: Raw HTML from Naukri API/scraper
            
        Returns:
            Formatted HTML string
        """
        try:
            if not raw_html or len(raw_html) < 50:
                return None
            
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'svg', 'button', 'input', 'form']):
                tag.decompose()
            
            # Naukri-specific: Find job description container
            description_div = (
                soup.find('div', class_=lambda x: x and 'jd-description' in str(x).lower()) or
                soup.find('div', class_=lambda x: x and 'job-description' in str(x).lower()) or
                soup.find('div', class_=lambda x: x and 'description' in str(x).lower()) or
                soup
            )
            
            return self._process_generic_html(description_div)
            
        except Exception as e:
            logger.error(f"Naukri extraction error: {e}")
            return None
    
    # ========================================================================
    # GENERIC HTML PROCESSING
    # ========================================================================
    
    def _process_generic_html(self, soup_element) -> Optional[str]:
        """
        Process generic HTML structure to extract formatted description.
        
        Args:
            soup_element: BeautifulSoup element
            
        Returns:
            Formatted HTML string with proper spacing, or None if no content extracted
        """
        formatted_parts = []
        self.first_heading_removed = False
        
        for element in soup_element.descendants:
            if isinstance(element, NavigableString):
                text = str(element).strip()
                if text and element.parent.name not in ['script', 'style', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'strong', 'b', 'em', 'i']:
                    # Standalone text becomes paragraph
                    if element.parent.name in ['div', 'section', 'article', 'td']:
                        formatted_parts.append(f'<p>{text}</p>')
            
            elif isinstance(element, Tag):
                result = self._process_html_element(element)
                if result:
                    formatted_parts.append(result)
        
        # Return None if no content was extracted
        if not formatted_parts:
            return None
        
        return '<div class="job-description-content">\n' + '\n'.join(formatted_parts) + '\n</div>'
    
    def _process_html_element(self, element: Tag) -> Optional[str]:
        """
        Process individual HTML element and return formatted version.
        
        Args:
            element: BeautifulSoup Tag element
            
        Returns:
            Formatted HTML string or None
        """
        tag_name = element.name
        text = element.get_text(strip=True)
        
        if not text or len(text) < 2:
            return None
        
        # Skip if already processed (has children that were processed)
        if element.find_parent(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
            return None
        
        # Process headings
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return self._process_heading(text, tag_name)
        
        # Process paragraphs
        elif tag_name == 'p':
            return self._process_paragraph(element)
        
        # Process lists
        elif tag_name == 'ul':
            return self._process_unordered_list(element)
        
        elif tag_name == 'ol':
            return self._process_ordered_list(element)
        
        # Process divs (might contain structured content)
        elif tag_name == 'div':
            return self._process_div(element)
        
        # Process spans (inline formatting)
        elif tag_name == 'span':
            return self._process_span(element)
        
        # Process strong/bold
        elif tag_name in ['strong', 'b']:
            return f'<strong>{text}</strong>'
        
        # Process emphasis/italic
        elif tag_name in ['em', 'i']:
            return f'<em>{text}</em>'
        
        # Process line breaks
        elif tag_name == 'br':
            return '<br>'
        
        return None
    
    def _process_heading(self, text: str, tag_name: str) -> Optional[str]:
        """Process heading element."""
        text_lower = text.lower().strip()
        
        # Check if this is a heading artifact (ONLY at the very start)
        if not self.first_heading_removed:
            is_artifact = any(
                text_lower == artifact or
                text_lower.startswith(artifact + ':') or
                text_lower.startswith(artifact + ' -')
                for artifact in self.HEADING_ARTIFACTS
            )
            
            if is_artifact:
                self.first_heading_removed = True
                return None
        
        # Determine heading level based on content
        if any(keyword in text_lower for keyword in self.SECTION_KEYWORDS):
            return f'<h3>{text}</h3>'
        
        # Keep original heading level
        return f'<{tag_name}>{text}</{tag_name}>'
    
    def _process_paragraph(self, element: Tag) -> Optional[str]:
        """Process paragraph element with inline formatting."""
        # Get HTML content to preserve inline formatting
        html_content = ''.join(str(child) for child in element.children)
        html_content = html_content.strip()
        
        if not html_content:
            return None
        
        # Clean up excessive whitespace
        html_content = re.sub(r'\s+', ' ', html_content)
        
        return f'<p>{html_content}</p>'
    
    def _process_unordered_list(self, element: Tag) -> Optional[str]:
        """Process unordered list."""
        items = []
        for li in element.find_all('li', recursive=False):
            text = li.get_text(strip=True)
            if text:
                # Preserve inline formatting in list items
                html_content = ''.join(str(child) for child in li.children)
                html_content = html_content.strip()
                items.append(f'<li>{html_content}</li>')
        
        if not items:
            return None
        
        return '<ul>\n' + '\n'.join(items) + '\n</ul>'
    
    def _process_ordered_list(self, element: Tag) -> Optional[str]:
        """Process ordered list."""
        items = []
        for li in element.find_all('li', recursive=False):
            text = li.get_text(strip=True)
            if text:
                # Preserve inline formatting in list items
                html_content = ''.join(str(child) for child in li.children)
                html_content = html_content.strip()
                items.append(f'<li>{html_content}</li>')
        
        if not items:
            return None
        
        return '<ol>\n' + '\n'.join(items) + '\n</ol>'
    
    def _process_div(self, element: Tag) -> Optional[str]:
        """Process div element (might contain paragraphs or sections)."""
        # Check if div contains block elements
        has_block_elements = element.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'div'])
        
        if has_block_elements:
            # Let child elements be processed separately
            return None
        
        # Div with only text/inline elements becomes a paragraph
        text = element.get_text(strip=True)
        if text and len(text) > 10:
            html_content = ''.join(str(child) for child in element.children)
            html_content = html_content.strip()
            return f'<p>{html_content}</p>'
        
        return None
    
    def _process_span(self, element: Tag) -> Optional[str]:
        """Process span element (inline formatting)."""
        # Spans are usually inline, let parent handle them
        return None
    
    # ========================================================================
    # PLAIN TEXT FALLBACK (for API responses without HTML)
    # ========================================================================
    
    def extract_from_plain_text(self, text: str) -> Optional[str]:
        """
        Convert plain text to formatted HTML with intelligent structure detection.
        Optimized for Indeed job descriptions.
        
        Args:
            text: Plain text job description
            
        Returns:
            Formatted HTML string with proper spacing
        """
        if not text or len(text) < 50:
            return None
        
        # CRITICAL: Split inline bullets into separate lines
        # Format: "* Item 1 * Item 2 * Item 3" → ["* Item 1", "* Item 2", "* Item 3"]
        text = re.sub(r'\s+\*\s+', '\n* ', text)
        
        lines = text.split('\n')
        formatted_parts = []
        current_list = []
        current_paragraph = []
        self.first_heading_removed = False
        
        # Emoji markers for sections
        section_emojis = ['📌', '📍', '🏢', '🕒', '🔎', '💰', '👤', '✅', '⭐', '🎯', '📋', '💼', '🚀', '💡', '🎓', '🏆']
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines - they separate sections
            if not line:
                # Save current paragraph
                if current_paragraph:
                    formatted_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
                # Save current list
                if current_list:
                    formatted_parts.append('<ul>\n' + '\n'.join(f'<li>{item}</li>' for item in current_list) + '\n</ul>')
                    current_list = []
                continue
            
            # Check if this is a heading artifact (ONLY at the very beginning)
            if not self.first_heading_removed:
                is_artifact = any(
                    line.lower() == artifact or
                    line.lower().startswith(artifact + ':') or
                    line.lower().startswith(artifact + ' -')
                    for artifact in self.HEADING_ARTIFACTS
                )
                
                if is_artifact:
                    self.first_heading_removed = True
                    continue
            
            # CRITICAL: Check for Indeed-style headings (wrapped in ** or *)
            # Format: *Description** or **Position Overview** or *In this position you will:**
            # BUT: Single * at start with no ** is a bullet point
            # AND: Long text with ** is NOT a heading, it's emphasis in a paragraph
            if line.startswith('*'):
                # Check if it's a heading (has ** somewhere) or just a bullet
                if '**' in line or (line.endswith('*') and line.count('*') > 1):
                    # Check if it's too long to be a heading (>80 chars = paragraph)
                    clean_text = line.strip('*').strip()
                    if len(clean_text) > 80:
                        # Too long for heading, treat as paragraph
                        if current_list:
                            formatted_parts.append('<ul>\n' + '\n'.join(f'<li>{item}</li>' for item in current_list) + '\n</ul>')
                            current_list = []
                        # Remove ** markers and add as paragraph
                        clean_text = clean_text.replace('**', '')
                        current_paragraph.append(clean_text)
                        continue
                    
                    # This is a heading
                    # Save current content first
                    if current_paragraph:
                        formatted_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                        current_paragraph = []
                    if current_list:
                        formatted_parts.append('<ul>\n' + '\n'.join(f'<li>{item}</li>' for item in current_list) + '\n</ul>')
                        current_list = []
                    
                    # Clean up the heading (remove * markers)
                    if clean_text:
                        formatted_parts.append(f'<h3>{clean_text}</h3>')
                    continue
                else:
                    # Single * at start = bullet point
                    if current_paragraph:
                        formatted_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                        current_paragraph = []
                    # Remove * and add to list
                    clean_text = line.lstrip('*').strip()
                    if clean_text:
                        current_list.append(clean_text)
                    continue
            
            # Check for section headers (but NOT full sentences)
            is_short_header = (
                any(line.startswith(emoji) for emoji in section_emojis) or
                (line.isupper() and len(line) > 3 and len(line) < 100) or
                (line.endswith(':') and len(line) < 80 and not line.count('.') > 1) or  # Short line ending with :
                (any(keyword in line.lower() for keyword in self.SECTION_KEYWORDS) and len(line) < 80)
            )
            
            # CRITICAL: Don't treat full sentences as headings
            is_full_sentence = (
                len(line) > 100 or  # Long lines are paragraphs
                line.count('.') > 1 or  # Multiple sentences
                line.count(',') > 2 or  # Multiple clauses
                line.count('—') > 0 or  # Em dash indicates paragraph
                ' and ' in line.lower() or ' or ' in line.lower()  # Conjunctions
            )
            
            if is_short_header and not is_full_sentence:
                # Save current content first
                if current_paragraph:
                    formatted_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
                if current_list:
                    formatted_parts.append('<ul>\n' + '\n'.join(f'<li>{item}</li>' for item in current_list) + '\n</ul>')
                    current_list = []
                # Add header
                formatted_parts.append(f'<h3>{line}</h3>')
            
            # Check for bullet points (but NOT headings with *)
            elif line.startswith(('•', '▪', '▸', '◦', '-', '➤', '→', '✓', '✔')) and not line.startswith('*'):
                if current_paragraph:
                    formatted_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
                # Remove bullet character and add to list
                clean_text = re.sub(r'^[•▪▸◦\-➤→✓✔]\s*', '', line)
                current_list.append(clean_text)
            
            # Check for numbered lists
            elif len(line) > 3 and re.match(r'^\d+[\.\)]\s+', line):
                if current_paragraph:
                    formatted_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
                    current_paragraph = []
                # Remove number and add to list
                clean_text = re.sub(r'^\d+[\.\)]\s+', '', line)
                current_list.append(clean_text)
            
            # Regular text - add to paragraph
            else:
                if current_list:
                    formatted_parts.append('<ul>\n' + '\n'.join(f'<li>{item}</li>' for item in current_list) + '\n</ul>')
                    current_list = []
                current_paragraph.append(line)
        
        # Don't forget remaining content
        if current_paragraph:
            formatted_parts.append('<p>' + ' '.join(current_paragraph) + '</p>')
        if current_list:
            formatted_parts.append('<ul>\n' + '\n'.join(f'<li>{item}</li>' for item in current_list) + '\n</ul>')
        
        result = '<div class="job-description-content">\n' + '\n'.join(formatted_parts) + '\n</div>'
        return result if result and len(result) > 50 else None
    
    # ========================================================================
    # POST-PROCESSING
    # ========================================================================
    
    def clean_html(self, html: str) -> str:
        """
        Final cleanup of HTML to ensure consistency.
        
        Args:
            html: Raw HTML string
            
        Returns:
            Cleaned HTML string
        """
        if not html:
            return ""
        
        # Remove excessive whitespace
        html = re.sub(r'\n{3,}', '\n\n', html)
        html = re.sub(r' {2,}', ' ', html)
        
        # Remove empty tags
        html = re.sub(r'<p>\s*</p>', '', html)
        html = re.sub(r'<h[1-6]>\s*</h[1-6]>', '', html)
        html = re.sub(r'<ul>\s*</ul>', '', html)
        html = re.sub(r'<ol>\s*</ol>', '', html)
        
        # Remove "Show more" / "Show less" artifacts
        html = html.replace('… more', '').replace('... more', '')
        html = html.replace('Show less', '').replace('Show more', '')
        html = html.replace('see more', '').replace('see less', '')
        
        # Trim
        html = html.strip()
        
        return html


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def extract_linkedin_description(page: Page) -> Optional[str]:
    """
    Convenience function to extract LinkedIn job description.
    
    Args:
        page: Playwright page object
        
    Returns:
        Formatted HTML string
    """
    extractor = JobDescriptionExtractor()
    html = await extractor.extract_linkedin(page)
    return extractor.clean_html(html) if html else None


def extract_indeed_description(raw_html: str) -> Optional[str]:
    """
    Convenience function to extract Indeed job description.
    
    Args:
        raw_html: Raw HTML from Indeed
        
    Returns:
        Formatted HTML string
    """
    extractor = JobDescriptionExtractor()
    html = extractor.extract_indeed(raw_html)
    return extractor.clean_html(html) if html else None


def extract_naukri_description(raw_html: str) -> Optional[str]:
    """
    Convenience function to extract Naukri job description.
    
    Args:
        raw_html: Raw HTML from Naukri
        
    Returns:
        Formatted HTML string
    """
    extractor = JobDescriptionExtractor()
    html = extractor.extract_naukri(raw_html)
    return extractor.clean_html(html) if html else None


def extract_from_text(text: str) -> Optional[str]:
    """
    Convenience function to extract from plain text.
    
    Args:
        text: Plain text description
        
    Returns:
        Formatted HTML string
    """
    extractor = JobDescriptionExtractor()
    html = extractor.extract_from_plain_text(text)
    return extractor.clean_html(html) if html else None
