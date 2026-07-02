#!/usr/bin/env python3
"""
LINKEDIN JOB POSTS SCRAPER - REALISTIC APPROACH
================================================
Uses authenticated browser session to scrape posts from LinkedIn feed/search.

REALITY CHECK:
- LinkedIn posts require authentication (no public API)
- Must use browser automation with logged-in session
- This is the ONLY reliable method that actually works

COMPLETELY ISOLATED - Does not interfere with other scrapers.

Target: Google Sheets "Job Posts" (ID: 11QMr5SU0Dr4JRXZ-GKKXPp_XxLQQHvpSoB8X2mg5NzE)

USAGE:
    python scrape_linkedin_job_posts.py
    python scrape_linkedin_job_posts.py --limit 100 --scroll 20
    python scrape_linkedin_job_posts.py --search "hiring software engineer"
"""

import asyncio
import argparse
import logging
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import io

from dotenv import load_dotenv
load_dotenv()

from linkedin_scraper import BrowserManager
from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_posts_scraper.log', encoding='utf-8'),
        logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

GOOGLE_SHEET_ID = "11QMr5SU0Dr4JRXZ-GKKXPp_XxLQQHvpSoB8X2mg5NzE"
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# Hiring keywords to detect in posts
HIRING_KEYWORDS = [
    "hiring", "we're hiring", "we are hiring", "join our team", "join us",
    "apply", "application", "careers", "job opening", "opportunity",
    "internship", "looking for", "seeking", "recruiting", "open position",
    "open role", "apply now", "send resume", "send cv", "interested candidates",
]


# ============================================================================
# LINKEDIN POST SCRAPER
# ============================================================================

class LinkedInPostScraper:
    """
    Scrapes LinkedIn posts using authenticated browser session.
    This is the ONLY method that actually works for posts.
    """
    
    def __init__(
        self,
        session_file: str = "linkedin_session.json",
        headless: bool = True
    ):
        """Initialize scraper."""
        self.session_file = session_file
        self.headless = headless
        self.seen_posts: Set[str] = set()
        
        # Statistics
        self.stats = {
            'posts_scanned': 0,
            'posts_with_hiring_keywords': 0,
            'posts_added': 0,
            'duplicates_skipped': 0,
        }
    
    async def scrape_feed(
        self,
        browser: BrowserManager,
        max_scrolls: int = 20,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Scrape posts from LinkedIn feed.
        
        Args:
            browser: Browser manager instance
            max_scrolls: Maximum number of scrolls
            limit: Maximum posts to collect
            
        Returns:
            List of post data
        """
        logger.info("Navigating to LinkedIn feed...")
        
        posts_data = []
        
        try:
            # Go to LinkedIn feed
            await browser.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            logger.info(f"Scrolling through feed (max {max_scrolls} scrolls)...")
            
            for scroll in range(max_scrolls):
                if len(posts_data) >= limit:
                    logger.info(f"Reached limit of {limit} posts")
                    break
                
                logger.info(f"Scroll {scroll + 1}/{max_scrolls} - Found {len(posts_data)} hiring posts so far")
                
                # Get all post containers on current view
                post_containers = await browser.page.query_selector_all('div.feed-shared-update-v2')
                
                for container in post_containers:
                    if len(posts_data) >= limit:
                        break
                    
                    try:
                        self.stats['posts_scanned'] += 1
                        
                        # Extract post URL
                        post_url = None
                        
                        # Try multiple selectors for post link
                        link_selectors = [
                            'a[href*="/posts/"]',
                            'a[href*="/feed/update/"]',
                            'a.app-aware-link[data-control-name="feed_post"]',
                        ]
                        
                        for selector in link_selectors:
                            try:
                                link_elem = await container.query_selector(selector)
                                if link_elem:
                                    href = await link_elem.get_attribute('href')
                                    if href:
                                        # Clean URL
                                        post_url = href.split('?')[0]
                                        if not post_url.startswith('http'):
                                            post_url = f"https://www.linkedin.com{post_url}"
                                        break
                            except:
                                continue
                        
                        if not post_url or post_url in self.seen_posts:
                            if post_url:
                                self.stats['duplicates_skipped'] += 1
                            continue
                        
                        # Extract post text
                        post_text = ""
                        try:
                            # Try to find "see more" button and click it
                            see_more = await container.query_selector('button[aria-label*="see more"]')
                            if see_more:
                                try:
                                    await see_more.click()
                                    await asyncio.sleep(0.5)
                                except:
                                    pass
                            
                            # Extract text
                            text_selectors = [
                                'div.feed-shared-update-v2__description',
                                'span.break-words',
                                'div.feed-shared-text',
                            ]
                            
                            for selector in text_selectors:
                                try:
                                    text_elem = await container.query_selector(selector)
                                    if text_elem:
                                        text = await text_elem.inner_text()
                                        if text and len(text.strip()) > 20:
                                            post_text = text.strip()
                                            break
                                except:
                                    continue
                        except:
                            pass
                        
                        # Check if contains hiring keywords
                        if post_text:
                            text_lower = post_text.lower()
                            has_hiring_keyword = any(keyword in text_lower for keyword in HIRING_KEYWORDS)
                            
                            if has_hiring_keyword:
                                self.seen_posts.add(post_url)
                                self.stats['posts_with_hiring_keywords'] += 1
                                
                                post_data = {
                                    'Post URL': post_url,
                                    'Date Added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                }
                                
                                posts_data.append(post_data)
                                logger.info(f"✓ Found hiring post #{len(posts_data)}: {post_url}")
                    
                    except Exception as e:
                        logger.debug(f"Error processing container: {e}")
                        continue
                
                # Scroll down
                await browser.page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(2)
            
            logger.info(f"Finished scrolling. Found {len(posts_data)} hiring posts")
            
        except Exception as e:
            logger.error(f"Error scraping feed: {e}")
        
        return posts_data
    
    async def search_posts(
        self,
        browser: BrowserManager,
        search_query: str,
        max_scrolls: int = 10,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for specific posts on LinkedIn.
        
        Args:
            browser: Browser manager instance
            search_query: Search query (e.g., "hiring software engineer")
            max_scrolls: Maximum number of scrolls
            limit: Maximum posts to collect
            
        Returns:
            List of post data
        """
        logger.info(f"Searching for posts: '{search_query}'")
        
        posts_data = []
        
        try:
            # Go to LinkedIn search
            search_url = f"https://www.linkedin.com/search/results/content/?keywords={search_query}"
            await browser.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            logger.info(f"Scrolling through search results (max {max_scrolls} scrolls)...")
            
            for scroll in range(max_scrolls):
                if len(posts_data) >= limit:
                    logger.info(f"Reached limit of {limit} posts")
                    break
                
                logger.info(f"Scroll {scroll + 1}/{max_scrolls} - Found {len(posts_data)} posts so far")
                
                # Get all search result containers
                result_containers = await browser.page.query_selector_all('div.search-results-container li')
                
                for container in result_containers:
                    if len(posts_data) >= limit:
                        break
                    
                    try:
                        self.stats['posts_scanned'] += 1
                        
                        # Extract post URL
                        post_url = None
                        link_elem = await container.query_selector('a[href*="/posts/"]')
                        if not link_elem:
                            link_elem = await container.query_selector('a[href*="/feed/update/"]')
                        
                        if link_elem:
                            href = await link_elem.get_attribute('href')
                            if href:
                                post_url = href.split('?')[0]
                                if not post_url.startswith('http'):
                                    post_url = f"https://www.linkedin.com{post_url}"
                        
                        if not post_url or post_url in self.seen_posts:
                            if post_url:
                                self.stats['duplicates_skipped'] += 1
                            continue
                        
                        self.seen_posts.add(post_url)
                        self.stats['posts_with_hiring_keywords'] += 1
                        
                        post_data = {
                            'Post URL': post_url,
                            'Date Added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        
                        posts_data.append(post_data)
                        logger.info(f"✓ Found post #{len(posts_data)}: {post_url}")
                    
                    except Exception as e:
                        logger.debug(f"Error processing result: {e}")
                        continue
                
                # Scroll down
                await browser.page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(2)
            
            logger.info(f"Finished searching. Found {len(posts_data)} posts")
            
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
        
        return posts_data
    
    async def run(
        self,
        search_query: Optional[str] = None,
        max_scrolls: int = 20,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Run the scraping workflow."""
        
        print("\n" + "="*70)
        print("LINKEDIN JOB POSTS SCRAPER - REALISTIC APPROACH")
        print("="*70)
        print(f"Method: Authenticated browser session (ONLY method that works)")
        if search_query:
            print(f"Mode: Search for '{search_query}'")
        else:
            print(f"Mode: Scrape from feed")
        print(f"Max Scrolls: {max_scrolls}")
        print(f"Limit: {limit} posts")
        print(f"Google Sheet: Job Posts")
        print("="*70 + "\n")
        
        # Connect to Google Sheets
        logger.info("Connecting to Google Sheets...")
        sheets = GoogleSheetsIntegration(
            credentials_file=GOOGLE_CREDENTIALS_FILE,
            sheet_id=GOOGLE_SHEET_ID
        )
        
        if not sheets.connect(worksheet_name="Job_Posts"):
            logger.error("Failed to connect to Google Sheets")
            return {'success': False, 'error': 'Google Sheets connection failed'}
        
        logger.info("✓ Connected to Google Sheets\n")
        
        # Load existing posts
        try:
            existing_posts = sheets.get_all_jobs()
            for post in existing_posts:
                if 'Post URL' in post:
                    self.seen_posts.add(post['Post URL'])
            logger.info(f"Loaded {len(self.seen_posts)} existing posts\n")
        except:
            logger.info("No existing posts found\n")
        
        async with BrowserManager(headless=self.headless) as browser:
            # Load LinkedIn session
            logger.info("Loading LinkedIn session...")
            try:
                await browser.load_session(self.session_file)
                logger.info("✓ Session loaded\n")
            except Exception as e:
                logger.error(f"Failed to load session: {e}")
                logger.info("💡 Run 'python samples/create_session.py' to create session\n")
                return {'success': False, 'error': 'Session load failed'}
            
            # Scrape posts
            if search_query:
                posts_data = await self.search_posts(browser, search_query, max_scrolls, limit)
            else:
                posts_data = await self.scrape_feed(browser, max_scrolls, limit)
            
            if not posts_data:
                logger.warning("No posts found")
                self._print_summary()
                return {'success': False, 'stats': self.stats}
            
            # Upload to Google Sheets
            logger.info(f"\nUploading {len(posts_data)} posts to Google Sheets...")
            
            for i, post_data in enumerate(posts_data, 1):
                try:
                    sheets.upload_job(post_data)
                    self.stats['posts_added'] += 1
                    logger.info(f"[{i}/{len(posts_data)}] ✓ Added: {post_data['Post URL']}")
                except Exception as e:
                    logger.error(f"Failed to upload post: {e}")
        
        # Print summary
        self._print_summary()
        
        return {
            'success': self.stats['posts_added'] > 0,
            'stats': self.stats
        }
    
    def _print_summary(self):
        """Print scraping summary."""
        print("\n" + "="*70)
        print("SCRAPING SUMMARY")
        print("="*70)
        print(f"Posts Scanned: {self.stats['posts_scanned']}")
        print(f"Posts with Hiring Keywords: {self.stats['posts_with_hiring_keywords']}")
        print(f"Posts Added: {self.stats['posts_added']}")
        print(f"Duplicates Skipped: {self.stats['duplicates_skipped']}")
        
        if self.stats['posts_scanned'] > 0:
            success_rate = (self.stats['posts_with_hiring_keywords'] / self.stats['posts_scanned']) * 100
            print(f"\nHiring Post Rate: {success_rate:.1f}%")
        
        print("="*70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Job Posts Scraper - Realistic Approach (Actually Works)"
    )
    
    parser.add_argument(
        '--search',
        type=str,
        help='Search query (e.g., "hiring software engineer")'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum posts to scrape (default: 100)'
    )
    parser.add_argument(
        '--scroll',
        type=int,
        default=20,
        help='Number of times to scroll (default: 20)'
    )
    parser.add_argument(
        '--headless',
        type=bool,
        default=True,
        help='Run in headless mode (default: True)'
    )
    parser.add_argument(
        '--session-file',
        default='linkedin_session.json',
        help='LinkedIn session file path'
    )
    
    args = parser.parse_args()
    
    scraper = LinkedInPostScraper(
        session_file=args.session_file,
        headless=args.headless
    )
    
    results = await scraper.run(
        search_query=args.search,
        max_scrolls=args.scroll,
        limit=args.limit
    )
    
    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    asyncio.run(main())
