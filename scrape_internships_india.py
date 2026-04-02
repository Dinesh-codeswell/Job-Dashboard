#!/usr/bin/env python3
"""
LinkedIn Internship Scraper - India
Scrapes internship opportunities from LinkedIn
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scrape_consulting_india_optimized import OptimizedJobSearchScraper, GoogleSheetsIntegration, BrowserManager, INTERNSHIP_KEYWORDS, INDIAN_CITIES_TIER_1, INDIAN_CITIES_TIER_2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to scrape internships only."""
    
    print("\n" + "="*70)
    print("🎓 LINKEDIN INTERNSHIP SCRAPER - INDIA")
    print("="*70)
    print(f"📍 Keywords: {len(INTERNSHIP_KEYWORDS)} internship-specific keywords")
    print(f"📍 Cities: {len(INDIAN_CITIES_TIER_1 + INDIAN_CITIES_TIER_2)} cities")
    print("="*70 + "\n")
    
    # Initialize scraper
    scraper = OptimizedJobSearchScraper(
        headless=False,
        session_file="session.json",
        worksheet_name="Consulting_Jobs_India",  # Same sheet, will include internships
        max_days=2  # Past 48 hours
    )
    
    # Run scraper with internships ONLY
    results = await scraper.run(
        limit_per_city=15,  # Higher limit for internships
        skip_duplicates=True,
        tier_1_only=False,
        cities=None,  # All cities
        include_internships=True  # This will include both consulting + internships
    )
    
    # Print results
    print("\n" + "="*70)
    print("📊 SCRAPER RESULTS")
    print("="*70)
    print(f"Cities Searched: {results['cities_searched']}")
    print(f"Total Jobs Found: {results['total_jobs_found']}")
    print(f"Total Jobs Scraped: {results['total_jobs_scraped']}")
    print(f"Total Jobs Uploaded: {results['total_jobs_uploaded']}")
    print(f"Duplicates Skipped: {results['total_duplicates_skipped']}")
    
    if results['errors']:
        print(f"\n⚠️  Errors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   - {error}")
    
    print("\n✅ Internship scraping complete!")
    print("="*70 + "\n")
    
    return results['success']


if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
