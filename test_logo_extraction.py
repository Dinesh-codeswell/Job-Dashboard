"""
Test script to verify company logo extraction is working.

Run this to test if logo URLs are being extracted correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from linkedin_scraper import BrowserManager
from linkedin_scraper.scrapers.job import JobScraper


async def test_logo_extraction(job_url: str):
    """Test logo extraction from a specific job URL."""
    
    print("=" * 70)
    print("  Company Logo Extraction Test")
    print("=" * 70)
    print(f"\nTesting URL: {job_url}\n")
    
    async with BrowserManager(headless=False) as browser:
        # Load session
        print("🔑 Loading LinkedIn session...")
        try:
            await browser.load_session("session.json")
            print("✓ Session loaded\n")
        except Exception as e:
            print(f"❌ Failed to load session: {e}")
            return None
        
        # Scrape job
        print("🔍 Scraping job...")
        scraper = JobScraper(browser.page)
        
        try:
            job = await scraper.scrape(job_url)
            
            print("\n" + "=" * 70)
            print("  EXTRACTION RESULTS")
            print("=" * 70)
            print(f"\n✅ Job Title: {job.job_title}")
            print(f"✅ Company: {job.company}")
            print(f"✅ Logo URL: {job.company_logo}")
            print(f"✅ Location: {job.location}")
            print(f"✅ Posted: {job.posted_date}")
            
            if job.company_logo:
                print("\n🎉 SUCCESS! Company logo was extracted!")
                print(f"   URL: {job.company_logo}")
                
                # Test if URL is valid
                if job.company_logo.startswith('http'):
                    print("   ✓ URL is absolute (valid)")
                else:
                    print("   ⚠ URL might be relative (invalid)")
            else:
                print("\n⚠️  WARNING: No company logo was extracted!")
                print("   This could mean:")
                print("   1. Company doesn't have a logo on LinkedIn")
                print("   2. Logo is loaded dynamically (needs different selector)")
                print("   3. LinkedIn structure changed")
            
            return job
            
        except Exception as e:
            print(f"\n❌ Error scraping job: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == '__main__':
    # Test with a sample job URL
    # Replace with an actual LinkedIn job URL
    test_url = input("Enter LinkedIn job URL to test: ").strip()
    
    if not test_url:
        print("\n❌ No URL provided!")
        print("   Example: https://www.linkedin.com/jobs/view/1234567890/")
        sys.exit(1)
    
    if 'linkedin.com/jobs' not in test_url:
        print("\n❌ Invalid LinkedIn job URL!")
        print("   URL must contain '/jobs/'")
        sys.exit(1)
    
    # Run test
    result = asyncio.run(test_logo_extraction(test_url))
    
    if result and result.company_logo:
        print("\n✅ Test PASSED! Logo extraction is working.\n")
        sys.exit(0)
    else:
        print("\n⚠️  Test completed but no logo was extracted.\n")
        sys.exit(0)
