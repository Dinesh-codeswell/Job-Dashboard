"""
Job Description Formatter - Pixel-Perfect HTML Extraction

Converts LinkedIn/Indeed job descriptions from raw HTML to clean, properly formatted HTML
with correct spacing, line breaks, and heading separation.

Fixes:
- Headings running together without line breaks
- Missing spacing between sections
- Improper <br> tag handling
- Bullet points not properly formatted
"""

import re
from typing import Optional
from html import unescape
import logging

logger = logging.getLogger(__name__)


class JobDescriptionFormatter:
    """
    Formats job descriptions from raw HTML to clean, structured HTML.
    """
    
    @staticmethod
    def clean_and_format(raw_html: str) -> str:
        """
        Clean and format job description HTML.
        
        Args:
            raw_html: Raw HTML from LinkedIn/Indeed
            
        Returns:
            Clean, properly formatted HTML
        """
        if not raw_html:
            return ""
        
        try:
            # Step 1: Unescape HTML entities
            html = unescape(raw_html)
            logger.debug(f"Step 1 - Unescaped: {len(html)} chars")
            
            # Step 2: Remove LinkedIn-specific wrapper divs and buttons
            html = JobDescriptionFormatter._remove_linkedin_wrappers(html)
            logger.debug(f"Step 2 - Wrappers removed: {len(html)} chars")
            
            if not html.strip():
                logger.warning("HTML is empty after removing wrappers! Returning original.")
                return raw_html  # Return original if we accidentally removed everything
            
            # Step 3: Fix heading spacing - CRITICAL FIX
            html = JobDescriptionFormatter._fix_heading_spacing(html)
            logger.debug(f"Step 3 - Heading spacing fixed: {len(html)} chars")
            
            # Step 4: Convert <br> tags to proper paragraph breaks
            html = JobDescriptionFormatter._fix_br_tags(html)
            logger.debug(f"Step 4 - BR tags fixed: {len(html)} chars")
            
            # Step 5: Clean up bullet points
            html = JobDescriptionFormatter._fix_bullet_points(html)
            logger.debug(f"Step 5 - Bullet points fixed: {len(html)} chars")
            
            # Step 6: Remove empty elements
            html = JobDescriptionFormatter._remove_empty_elements(html)
            logger.debug(f"Step 6 - Empty elements removed: {len(html)} chars")
            
            # Step 7: Wrap paragraphs (only if needed)
            html = JobDescriptionFormatter._wrap_paragraphs(html)
            logger.debug(f"Step 7 - Paragraphs wrapped: {len(html)} chars")
            
            # Step 8: Final cleanup
            html = JobDescriptionFormatter._final_cleanup(html)
            logger.debug(f"Step 8 - Final cleanup: {len(html)} chars")
            
            result = html.strip()
            
            # Safety check: if result is empty or too short, return original
            if not result or len(result) < 50:
                logger.warning(f"Result too short ({len(result)} chars), returning original")
                return raw_html
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting job description: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return raw_html  # Return original on error
    
    @staticmethod
    def _remove_linkedin_wrappers(html: str) -> str:
        """Remove LinkedIn-specific wrapper divs and buttons."""
        # First, extract content from show-more-less-html__markup divs
        markup_match = re.search(
            r'<div[^>]*class="[^"]*show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>',
            html,
            flags=re.DOTALL | re.IGNORECASE
        )
        if markup_match:
            html = markup_match.group(1)
        
        # Remove job-description-content wrapper if present (Deloitte scraper)
        html = re.sub(
            r'<div[^>]*class="[^"]*job-description-content[^"]*"[^>]*>',
            '',
            html,
            flags=re.IGNORECASE
        )
        
        # Remove wrapping <p> tags if the entire content is wrapped in one
        # Pattern: <p><section...>...</section></p>
        html = re.sub(
            r'^<p>\s*(<section.*?</section>)\s*</p>$',
            r'\1',
            html,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove buttons wrapped in <p> tags
        html = re.sub(
            r'<p>\s*(<button[^>]*>.*?</button>)\s*</p>',
            '',
            html,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove buttons (but keep content before them)
        html = re.sub(
            r'<button[^>]*>.*?</button>',
            '',
            html,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove SVG icons
        html = re.sub(
            r'<svg[^>]*>.*?</svg>',
            '',
            html,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove icon elements
        html = re.sub(
            r'<icon[^>]*>.*?</icon>',
            '',
            html,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove show-more-less sections (but content is already extracted above)
        html = re.sub(
            r'<section[^>]*class="show-more-less-html"[^>]*>',
            '',
            html,
            flags=re.IGNORECASE
        )
        html = re.sub(r'</section>', '', html, flags=re.IGNORECASE)
        
        # Remove trailing </div> tags from wrappers
        html = re.sub(r'</div>\s*$', '', html, flags=re.IGNORECASE)
        
        return html
    
    @staticmethod
    def _fix_heading_spacing(html: str) -> str:
        """
        Fix heading spacing - CRITICAL FIX for headings running together.
        
        Problem: "locations.About Swiggy InstamartSwiggy Instamart"
        Solution: "locations.\n\n<h3>About Swiggy Instamart</h3>\n\nSwiggy Instamart"
        """
        # Pattern 1: Text followed immediately by <strong> (heading indicator)
        # Example: "locations.<strong>About Swiggy Instamart<br><br></strong>"
        # Fix: Add double <br> before <strong> to create paragraph break
        html = re.sub(
            r'([a-z\.\,\)])(<strong>)',
            r'\1<br><br>\2',
            html,
            flags=re.IGNORECASE
        )
        
        # Pattern 2: </strong> followed immediately by text (no space)
        # Example: "</strong>Swiggy Instamart, is building"
        # Fix: Add double <br> after </strong> to create paragraph break
        html = re.sub(
            r'(</strong>)([A-Z][a-z])',
            r'\1<br><br>\2',
            html
        )
        
        # Pattern 3: <br><br> inside <strong> tags (LinkedIn pattern)
        # Example: "<strong>About The Role<br><br></strong>"
        # Fix: Move <br><br> outside </strong> tag
        html = re.sub(
            r'<strong>([^<]+)<br><br></strong>',
            r'<strong>\1</strong><br><br>',
            html,
            flags=re.IGNORECASE
        )
        
        # Pattern 4: Multiple <br> tags between sections
        # Normalize to exactly 2 <br> tags for consistent spacing
        html = re.sub(
            r'(<br\s*/?>){3,}',
            '<br><br>',
            html,
            flags=re.IGNORECASE
        )
        
        return html
    
    @staticmethod
    def _fix_br_tags(html: str) -> str:
        """
        Convert <br> tags to proper paragraph breaks.
        
        Rules:
        - Single <br> → Keep as line break within paragraph
        - Double <br><br> → Convert to paragraph break (</p><p>)
        - <br> before/after headings → Remove (handled by heading spacing)
        - Only convert <strong> to <h3> if it's a standalone heading (not inline)
        """
        # First, identify and convert ONLY standalone headings to <h3>
        # A standalone heading is:
        # 1. Preceded by <br><br> or at start
        # 2. Followed by <br><br> or at end
        # 3. Short text (< 100 chars)
        # 4. Often ends with "?" or ":"
        
        # Pattern: <br><br><strong>Heading Text<br><br></strong>
        # This is clearly a heading
        html = re.sub(
            r'(<br\s*/?>\s*<br\s*/?>|^)\s*<strong>([^<]{1,100}?)</strong>\s*(<br\s*/?>\s*<br\s*/?>|$)',
            lambda m: f'{m.group(1)}<h3>{m.group(2).strip()}</h3>{m.group(3)}',
            html,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Pattern: Start of text with <strong>Heading<br><br></strong>
        html = re.sub(
            r'^<strong>([^<]{1,100}?)<br\s*/?>\s*<br\s*/?>',
            lambda m: f'<h3>{m.group(1).strip()}</h3><br><br>',
            html,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Convert double <br> to paragraph breaks
        html = re.sub(
            r'<br\s*/?>\s*<br\s*/?>',
            '</p><p>',
            html,
            flags=re.IGNORECASE
        )
        
        # Single <br> becomes a line break within paragraph
        html = re.sub(
            r'<br\s*/?>',
            '\n',
            html,
            flags=re.IGNORECASE
        )
        
        return html
    
    @staticmethod
    def _fix_bullet_points(html: str) -> str:
        """
        Clean up bullet points and list formatting.
        """
        # Ensure <ul> and <li> tags are properly closed
        html = re.sub(r'<li>([^<]*?)(?=<li>|</ul>|$)', r'<li>\1</li>', html, flags=re.IGNORECASE)
        
        # Remove empty list items
        html = re.sub(r'<li>\s*</li>', '', html, flags=re.IGNORECASE)
        
        # Ensure lists have proper spacing
        html = re.sub(r'</ul>\s*<p>', '</ul></p><p>', html, flags=re.IGNORECASE)
        html = re.sub(r'</p>\s*<ul>', '</p><p><ul>', html, flags=re.IGNORECASE)
        
        return html
    
    @staticmethod
    def _remove_empty_elements(html: str) -> str:
        """
        Remove empty paragraphs, headings, and excessive whitespace.
        """
        # Remove empty paragraphs
        html = re.sub(r'<p>\s*</p>', '', html, flags=re.IGNORECASE)
        
        # Remove empty headings
        html = re.sub(r'<h[1-6]>\s*</h[1-6]>', '', html, flags=re.IGNORECASE)
        
        # Remove empty strong tags
        html = re.sub(r'<strong>\s*</strong>', '', html, flags=re.IGNORECASE)
        
        # Collapse multiple spaces
        html = re.sub(r'\s{2,}', ' ', html)
        
        # Remove spaces at start/end of tags
        html = re.sub(r'<p>\s+', '<p>', html, flags=re.IGNORECASE)
        html = re.sub(r'\s+</p>', '</p>', html, flags=re.IGNORECASE)
        
        return html
    
    @staticmethod
    def _wrap_paragraphs(html: str) -> str:
        """
        Ensure all text content is wrapped in paragraph tags.
        """
        # If HTML already has proper structure, don't mess with it
        if '<p>' in html or '<h' in html:
            return html
        
        # Split by existing block-level tags
        parts = re.split(r'(</?(?:p|h[1-6]|ul|ol|li|div)[^>]*>)', html, flags=re.IGNORECASE)
        
        result = []
        in_block = False
        block_stack = []
        
        for part in parts:
            if not part.strip():
                continue
            
            # Check if it's a tag
            if part.startswith('<'):
                result.append(part)
                
                # Track block-level elements
                if re.match(r'<(p|h[1-6]|ul|ol|div)', part, re.IGNORECASE):
                    in_block = True
                    tag_match = re.match(r'<(\w+)', part)
                    if tag_match:
                        block_stack.append(tag_match.group(1).lower())
                elif re.match(r'</(p|h[1-6]|ul|ol|div)', part, re.IGNORECASE):
                    if block_stack:
                        block_stack.pop()
                    in_block = len(block_stack) > 0
            else:
                # It's text content
                if not in_block and part.strip():
                    # Wrap in paragraph
                    result.append(f'<p>{part.strip()}</p>')
                else:
                    result.append(part)
        
        return ''.join(result)
    
    @staticmethod
    def _final_cleanup(html: str) -> str:
        """
        Final cleanup and normalization.
        """
        # Ensure headings have proper spacing with newlines
        html = re.sub(r'</h([1-6])>\s*<p>', r'</h\1>\n\n<p>', html, flags=re.IGNORECASE)
        html = re.sub(r'</p>\s*<h([1-6])>', r'</p>\n\n<h\1>', html, flags=re.IGNORECASE)
        
        # Ensure lists have proper spacing with newlines
        html = re.sub(r'</p>\s*<ul>', r'</p>\n\n<ul>', html, flags=re.IGNORECASE)
        html = re.sub(r'</ul>\s*<p>', r'</ul>\n\n<p>', html, flags=re.IGNORECASE)
        
        # Add newlines between consecutive paragraphs
        html = re.sub(r'</p>\s*<p>', r'</p>\n\n<p>', html, flags=re.IGNORECASE)
        
        # Remove any remaining multiple consecutive paragraph breaks
        html = re.sub(r'(</p>\s*\n\s*){2,}', '</p>\n\n', html, flags=re.IGNORECASE)
        html = re.sub(r'(<p>\s*\n\s*){2,}', '<p>', html, flags=re.IGNORECASE)
        
        # Normalize whitespace but keep newlines
        html = re.sub(r' {2,}', ' ', html)  # Multiple spaces to single space
        html = re.sub(r'\n{3,}', '\n\n', html)  # Max 2 newlines
        
        return html
    
    @staticmethod
    def extract_from_linkedin_html(raw_html: str) -> str:
        """
        Extract and format job description from LinkedIn HTML.
        
        This is the main entry point for processing LinkedIn job descriptions.
        
        Args:
            raw_html: Raw HTML from LinkedIn job posting
            
        Returns:
            Clean, formatted HTML ready for display
        """
        return JobDescriptionFormatter.clean_and_format(raw_html)


# Convenience function for easy import
def format_job_description(raw_html: str) -> str:
    """
    Format a job description from raw HTML.
    
    Args:
        raw_html: Raw HTML from job posting
        
    Returns:
        Clean, formatted HTML
    """
    return JobDescriptionFormatter.extract_from_linkedin_html(raw_html)


# Example usage and testing
if __name__ == "__main__":
    # Test with the provided LinkedIn HTML
    test_html = '''<section class="show-more-less-html" data-max-lines="5"> <div class="show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden"> Ways of working: Mandate 3 : Onsite - Office / Field: Employees are expected to work from the office on all days out of their respective base locations.<br><br><strong>About Swiggy Instamart<br><br></strong>Swiggy Instamart, is building the convenience grocery segment in India. We offer more than 30000 + assortments / products to our customers within 10-15 mins. We are striving to augment our consumer promise of enabling unparalleled convenience by making grocery delivery instant and delightful. Instamart has been operating in 90+ cities across India and plans to expand to a few more soon. We have seen immense love from the customers till now and are excited to redefine how India shops.<br><br><strong>About The Role<br><br></strong>We are looking for a Senior Manager – Partnerships to drive strategic partnerships for NOICE, our private label brand. This role will focus on building and scaling distribution and growth partnerships, including vending machine networks, D2C brand collaborations, and new channel partnerships to expand brand reach and revenue.<br><br>The ideal candidate will have strong experience in partnership development, business development, and alternate distribution channels, especially within D2C, FMCG, retail, or vending machine ecosystems.<br><br><strong>Key Responsibilities<br><br></strong><strong>Strategic Partnerships: <br><br></strong><ul><li>Identify, evaluate, and onboard strategic partners to expand the reach of NOCIE products.</li><li>Build partnerships with vending machine operators, corporate offices, co-working spaces, airports, educational institutions, and retail chains.</li><li>Drive collaborations with D2C brands and emerging consumer brands for co-selling, bundling, and cross-promotions.<br><br></li></ul><strong>Channel Expansion<br><br></strong><ul><li>Develop new distribution channels through partnerships beyond traditional retail.</li><li>Scale vending machine business across partners.<br><br></li></ul><strong>Partnership Management<br><br></strong><ul><li>Own the end-to-end lifecycle of partnerships including sourcing, negotiation, onboarding, and relationship management.</li><li>Drive commercial negotiations, revenue share models, and joint growth plans with partners.</li><li>Monitor performance metrics, P&amp;L impact, and growth opportunities across partnerships.<br><br></li></ul><strong>Cross-Functional Collaboration<br><br></strong><ul><li>Work closely with category, supply chain, marketing, and operations teams to execute partnership initiatives.</li><li>Coordinate with product and brand teams for launches, campaigns, and partner activations.<br><br></li></ul><strong>Growth &amp; Strategy<br><br></strong><ul><li>Identify new market opportunities and innovative partnership models to grow NOCIE's distribution.</li><li>Track industry trends across vending, D2C, and new-age retail ecosystems.<br><br></li></ul><strong>Key Requirements<br><br></strong><ul><li>3–6 years of experience in partnerships, business development, or channel expansion.</li><li>Experience working with D2C brands, FMCG, retail, vending machine ecosystems, or alternate distribution models.</li><li>Strong commercial acumen and negotiation skills.</li><li>Experience building B2B partnerships and strategic alliances.</li><li>Ability to manage multiple partners and drive growth initiatives at scale.</li><li>Excellent stakeholder management and cross-functional collaboration skills.<br><br></li></ul>"We are an equal opportunity employer and all qualified applicants will receive consideration for employment without regards to race, colour, religion, sex, disability status, or any other characteristic protected by the law" </div> <button class="show-more-less-html__button show-more-less-button show-more-less-html__button--more ml-0.5" data-tracking-control-name="public_jobs_show-more-html-btn" aria-label="" aria-expanded="false"> <!----> <icon class="show-more-less-html__button-icon show-more-less-button-icon lazy-loaded" aria-hidden="true" aria-busy="false"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" preserveAspectRatio="xMinYMin meet" focusable="false" class="lazy-loaded" aria-busy="false"><path d="M8 9l5.93-4L15 6.54l-6.15 4.2a1.5 1.5 0 01-1.69 0L1 6.54 2.07 5z" fill="currentColor"></path></svg></icon> </button> <button class="show-more-less-html__button show-more-less-button show-more-less-html__button--less ml-0.5" data-tracking-control-name="public_jobs_show-less-html-btn" aria-label="" aria-expanded="true"> <!----> <icon class="show-more-less-html__button-icon show-more-less-button-icon lazy-loaded" aria-hidden="true" aria-busy="false"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" preserveAspectRatio="xMinYMin meet" focusable="false" class="lazy-loaded" aria-busy="false"><path d="M8 7l-5.9 4L1 9.5l6.2-4.2c.5-.3 1.2-.3 1.7 0L15 9.5 13.9 11 8 7z" fill="currentColor"></path></svg></icon> </button> <!----> </section>'''
    
    formatted = format_job_description(test_html)
    print("=== FORMATTED OUTPUT ===")
    print(formatted)
    print("\n=== END ===")
