#!/usr/bin/env python3
"""
Simple Notion Jobs Scraper - No Package Dependencies
⚡ FRESH JOBS - 24 HOURS ONLY ⚡

Scrapes LinkedIn jobs posted in past 24 hours and adds to Notion.
Uses Playwright directly (no linkedin_scraper package needed).

Usage:
    python simple_notion_scraper.py --limit 30
    python simple_notion_scraper.py --keywords "SDE" "Product Manager"
"""
import asyncio
import argparse
import logging
import sys
import re
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError
from playwright.async_api import async_playwright

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

TARGET_KEYWORDS = [
    "Software Development Engineer",
    "SDE",
    "Software Engineer",
    "Product Manager",
    "Data Scientist",
    "Business Analyst",
    "Growth Manager",
]

EXCLUDE_KEYWORDS = [
    "Accountant", "Copywriter", "Video Editor", "Data Entry",
    "Customer Support", "Telecaller",
]


# ============================================================================
# NOTION INTEGRATION
# ============================================================================

class NotionClient:
    def __init__(self, api_key: str, database_id: str):
        self.client = Client(auth=api_key)
        self.database_id = database_id
        self.cache_file = "notion_added_jobs_cache.json"
        self.added_urls = self._load_cache()
    
    def _load_cache(self) -> set:
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return set(json.load(f))
        except:
            pass
        return set()
    
    def _save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(list(self.added_urls), f)
        except:
            pass
    
    def is_duplicate(self, url: str) -> bool:
        return url in self.added_urls
    
    def add_job(self, job_data: Dict) -> bool:
        try:
            properties = {
                "Company": {
                    "title": [{"text": {"content": job_data.get("company", "Unknown")}}]
                },
                "Position": {
                    "rich_text": [{"text": {"content": job_data.get("role", "Unknown")}}]
                },
                "Date Posted": {
                    "date": {"start": job_data.get("date_added")}
                },
                "Location": {
                    "rich_text": [{"text": {"content": job_data.get("location", "Unknown")}}]
                },
                "Application Link": {
                    "url": job_data.get("url", "")
                }
            }
            
            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            self.added_urls.add(job_data.get("url", ""))
            self._save_cache()
            
            logger.info(f"✓ Added: {job_data.get('role')} at {job_data.get('company')}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to add job: {e}")
            return False


# ============================================================================
# LINKEDIN SCRAPER
# ============================================================================

class LinkedInScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        logger.info("✓ Browser launched")
    
    async def stop(self):
        if self.browser:
            await self.browser.close()
            logger.info("✓ Browser closed")
    
    async def search_jobs(self, keyword: str, location: str, limit: int = 10) -> List[str]:
        """Search LinkedIn for jobs and return URLs"""
        try:
            # Build search URL with 24h filter
            params = {
                'keywords': keyword,
                'location': location,
                'f_TPR': 'r86400'  # 24 hours
            }
            url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"
            
            logger.info(f"🔍 Searching: {keyword} in {location}")
            
            await self.page.goto(url, wait_until='networkidle')
            await self.page.wait_for_selector('a[href*="/jobs/view/"]', timeout=10000)
            
            # Extract job URLs
            job_urls = await self.page.evaluate('''() => {
                const links = document.querySelectorAll('a[href*="/jobs/view/"]');
                const urls = new Set();
                links.forEach(link => {
                    const href = link.href.split('?')[0];
                    if (href.includes('/jobs/view/')) {
                        urls.add(href);
                    }
                });
                return Array.from(urls);
            }''')
            
            logger.info(f"  Found {len(job_urls)} jobs")
            return job_urls[:limit]
            
        except Exception as e:
            logger.error(f"  ✗ Search failed: {e}")
            return []
    
    async def scrape_job(self, url: str) -> Optional[Dict]:
        """Scrape job details from URL"""
        try:
            await self.page.goto(url, wait_until='networkidle')
            await self.page.wait_for_selector('h1', timeout=10000)
            
            # Extract job data
            job_data = await self.page.evaluate('''() => {
                const main = document.querySelector('main');
                if (!main) return null;
                
                const text = main.innerText;
                const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                
                // Extract job title (usually after company name)
                let title = '';
                let company = '';
                
                // Try to find company link
                const companyLink = document.querySelector('a[href*="/company/"]');
                if (companyLink) {
                    company = companyLink.innerText.trim();
                }
                
                // Find title in h1 or h2
                const h1 = document.querySelector('h1');
                if (h1) {
                    title = h1.innerText.trim();
                }
                
                // Find location
                const locationMatch = text.match(/([\\w\\s,]+(?:India|Remote|Bangalore|Mumbai|Delhi|Pune|Hyderabad|Chennai)[\\w\\s,]*)/i);
                const location = locationMatch ? locationMatch[1].trim() : 'India';
                
                // Find posted time
                const postedMatch = text.match(/(\\d+\\s*(minute|hour|day|week)s?\\s*ago)/i);
                const posted = postedMatch ? postedMatch[1] : '';
                
                return {
                    title: title || 'Unknown Position',
                    company: company || 'Unknown Company',
                    location: location,
                    posted: posted,
                    description: text.substring(0, 5000)
                };
            }''')
            
            if job_data and job_data.get('title'):
                logger.info(f"  ✓ Scraped: {job_data['title']}")
                return job_data
            
            return None
            
        except Exception as e:
            logger.error(f"  ✗ Failed to scrape: {e}")
            return None


# ============================================================================
# FILTERING
# ============================================================================

def is_fresh_job(posted_date: str) -> bool:
    """Check if job was posted in past 24 hours"""
    if not posted_date:
        return False
    
    posted_lower = posted_date.lower()
    match = re.search(r'(\\d+)\\s*(minute|hour|day|week)', posted_lower)
    
    if not match:
        return False
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit in ['minute', 'hour']:
        return True
    elif unit == 'day':
        return value <= 1
    else:
        return False


def should_exclude(title: str) -> bool:
    """Check if job should be excluded"""
    title_lower = title.lower()
    return any(exclude.lower() in title_lower for exclude in EXCLUDE_KEYWORDS)


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description='Simple Notion Jobs Scraper')
    parser.add_argument('--limit', type=int, default=10, help='Jobs per keyword')
    parser.add_argument('--keywords', nargs='+', help='Keywords to search')
    parser.add_argument('--headless', type=bool, default=True, help='Headless mode')
    args = parser.parse_args()
    
    # Get Notion credentials
    notion_key = os.getenv('NOTION_API_KEY')
    notion_db = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_key or not notion_db:
        logger.error("❌ NOTION_API_KEY or NOTION_DATABASE_ID not set in .env")
        return
    
    # Initialize
    notion = NotionClient(notion_key, notion_db)
    scraper = LinkedInScraper(headless=args.headless)
    
    print("\\n" + "="*70)
    print("⚡ SIMPLE NOTION SCRAPER - 24 HOURS ONLY")
    print("="*70)
    print(f"📍 Keywords: {len(args.keywords or TARGET_KEYWORDS)}")
    print(f"📍 Limit: {args.limit} jobs/keyword")
    print(f"📍 Time Filter: PAST 24 HOURS")
    print("="*70 + "\\n")
    
    try:
        await scraper.start()
        
        keywords = args.keywords or TARGET_KEYWORDS
        stats = {'found': 0, 'fresh': 0, 'added': 0, 'skipped': 0}
        
        for keyword in keywords:
            print(f"\\n📝 Keyword: {keyword}")
            print("-" * 50)
            
            # Search
            job_urls = await scraper.search_jobs(keyword, 'India', args.limit)
            stats['found'] += len(job_urls)
            
            # Scrape each job
            for url in job_urls:
                # Check duplicate
                if notion.is_duplicate(url):
                    stats['skipped'] += 1
                    continue
                
                # Scrape
                job_data = await scraper.scrape_job(url)
                if not job_data:
                    continue
                
                # Check if fresh
                if not is_fresh_job(job_data.get('posted', '')):
                    logger.debug(f"  ⏰ Skipped (not fresh): {job_data['title']}")
                    continue
                
                stats['fresh'] += 1
                
                # Check if should exclude
                if should_exclude(job_data['title']):
                    logger.debug(f"  ❌ Excluded: {job_data['title']}")
                    continue
                
                # Add to Notion
                if notion.add_job({
                    'company': job_data['company'],
                    'role': job_data['title'],
                    'date_added': datetime.now().strftime('%Y-%m-%d'),
                    'location': job_data['location'],
                    'url': url
                }):
                    stats['added'] += 1
                
                await asyncio.sleep(1)  # Rate limit
            
            await asyncio.sleep(2)  # Between keywords
        
        # Summary
        print("\\n" + "="*70)
        print("📊 SUMMARY")
        print("="*70)
        print(f"🔍 Jobs Found: {stats['found']}")
        print(f"⚡ Fresh (24h): {stats['fresh']}")
        print(f"➕ Added to Notion: {stats['added']}")
        print(f"⏭️  Skipped (dupes): {stats['skipped']}")
        print("="*70 + "\\n")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.stop()


if __name__ == "__main__":
    asyncio.run(main())
