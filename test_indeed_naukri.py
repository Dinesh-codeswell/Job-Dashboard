#!/usr/bin/env python3
"""
Test script for Indeed and Naukri scraper integration.

This script verifies that:
1. All modules can be imported
2. Scraper classes can be instantiated
3. API connections work (test with small request)

Usage:
    python test_indeed_naukri.py
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules can be imported"""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    try:
        from jobspy import scrape_jobs
        print("✅ jobspy.scrape_jobs imported")
    except ImportError as e:
        print(f"❌ Failed to import jobspy.scrape_jobs: {e}")
        return False
    
    try:
        from jobspy.model import Site, JobPost, ScraperInput, Country, JobType
        print("✅ jobspy.model modules imported")
    except ImportError as e:
        print(f"❌ Failed to import jobspy.model: {e}")
        return False
    
    try:
        from jobspy.indeed import Indeed
        print("✅ jobspy.indeed.Imported imported")
    except ImportError as e:
        print(f"❌ Failed to import jobspy.indeed: {e}")
        return False
    
    try:
        from jobspy.naukri import Naukri
        print("✅ jobspy.naukri.Imported imported")
    except ImportError as e:
        print(f"❌ Failed to import jobspy.naukri: {e}")
        return False
    
    try:
        from linkedin_scraper.integrations import (
            scrape_multi_platform,
            scrape_indeed,
            scrape_naukri,
        )
        print("✅ linkedin_scraper.integrations imported")
    except ImportError as e:
        print(f"❌ Failed to import linkedin_scraper.integrations: {e}")
        return False
    
    print("\n✅ All imports successful!")
    return True


def test_scraper_instantiation():
    """Test that scraper classes can be instantiated"""
    print("\n" + "="*60)
    print("TEST 2: Scraper Instantiation")
    print("="*60)
    
    try:
        from jobspy.indeed import Indeed
        from jobspy.naukri import Naukri
        
        indeed = Indeed()
        print(f"✅ Indeed scraper instantiated: {indeed}")
        
        naukri = Naukri()
        print(f"✅ Naukri scraper instantiated: {naukri}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to instantiate scrapers: {e}")
        return False


def test_site_enum():
    """Test Site enum values"""
    print("\n" + "="*60)
    print("TEST 3: Site Enum Values")
    print("="*60)
    
    try:
        from jobspy.model import Site
        
        print(f"✅ Site.LINKEDIN = {Site.LINKEDIN.value}")
        print(f"✅ Site.INDEED = {Site.INDEED.value}")
        print(f"✅ Site.NAUKRI = {Site.NAUKRI.value}")
        
        # Test all expected sites exist
        assert hasattr(Site, 'LINKEDIN')
        assert hasattr(Site, 'INDEED')
        assert hasattr(Site, 'NAUKRI')
        
        print("\n✅ All Site enum values correct!")
        return True
    except Exception as e:
        print(f"❌ Site enum test failed: {e}")
        return False


def test_country_enum():
    """Test Country enum values"""
    print("\n" + "="*60)
    print("TEST 4: Country Enum Values")
    print("="*60)
    
    try:
        from jobspy.model import Country
        
        india = Country.INDIA
        print(f"✅ Country.INDIA = {india.value}")
        
        usa = Country.USA
        print(f"✅ Country.USA = {usa.value}")
        
        # Test from_string method
        country_from_str = Country.from_string("india")
        print(f"✅ Country.from_string('india') = {country_from_str}")
        
        print("\n✅ All Country enum values correct!")
        return True
    except Exception as e:
        print(f"❌ Country enum test failed: {e}")
        return False


def test_scraper_input():
    """Test ScraperInput model"""
    print("\n" + "="*60)
    print("TEST 5: ScraperInput Model")
    print("="*60)
    
    try:
        from jobspy.model import ScraperInput, Site, Country
        
        scraper_input = ScraperInput(
            site_type=[Site.INDEED, Site.NAUKRI],
            search_term="software engineer",
            location="Bangalore",
            country=Country.INDIA,
            results_wanted=10,
            hours_old=48
        )
        
        print(f"✅ ScraperInput created: {scraper_input}")
        print(f"   - Sites: {scraper_input.site_type}")
        print(f"   - Search: {scraper_input.search_term}")
        print(f"   - Location: {scraper_input.location}")
        print(f"   - Results: {scraper_input.results_wanted}")
        
        print("\n✅ ScraperInput model working!")
        return True
    except Exception as e:
        print(f"❌ ScraperInput test failed: {e}")
        return False


def test_job_post_model():
    """Test JobPost model"""
    print("\n" + "="*60)
    print("TEST 6: JobPost Model")
    print("="*60)
    
    try:
        from jobspy.model import JobPost, Location, Compensation, CompensationInterval
        from datetime import date
        
        job = JobPost(
            id="test-123",
            title="Software Engineer",
            company_name="Test Corp",
            job_url="https://example.com/job/123",
            location=Location(city="Bangalore", state="Karnataka", country="India"),
            description="Test job description",
            date_posted=date.today(),
            compensation=Compensation(
                interval=CompensationInterval.YEARLY,
                min_amount=1000000,
                max_amount=2000000,
                currency="INR"
            ),
            skills=["Python", "JavaScript"],
            experience_range="3-5 years"
        )
        
        print(f"✅ JobPost created: {job.title} at {job.company_name}")
        print(f"   - Location: {job.location.display_location()}")
        print(f"   - Skills: {job.skills}")
        print(f"   - Experience: {job.experience_range}")
        
        # Test dict conversion
        job_dict = job.dict()
        print(f"   - Dict conversion: {len(job_dict)} fields")
        
        print("\n✅ JobPost model working!")
        return True
    except Exception as e:
        print(f"❌ JobPost test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indeed_api_connection():
    """Test Indeed API connection with a small request"""
    print("\n" + "="*60)
    print("TEST 7: Indeed API Connection (Test Request)")
    print("="*60)
    
    try:
        from jobspy.indeed import Indeed
        from jobspy.model import ScraperInput, Site, Country
        
        indeed = Indeed()
        
        scraper_input = ScraperInput(
            site_type=[Site.INDEED],
            search_term="python developer",
            location="Bangalore",
            country=Country.INDIA,
            results_wanted=2,  # Small test
            hours_old=72
        )
        
        logger.info("Sending test request to Indeed API...")
        response = indeed.scrape(scraper_input)
        
        print(f"✅ Indeed API responded successfully!")
        print(f"   - Jobs found: {len(response.jobs)}")
        
        if response.jobs:
            job = response.jobs[0]
            print(f"   - Sample job: {job.title} at {job.company_name}")
        
        return True
    except Exception as e:
        print(f"⚠️  Indeed API test failed (may be expected): {e}")
        print("   This could be due to network issues, API limits, or missing dependencies")
        return False  # Don't fail the test suite for this


def test_naukri_api_connection():
    """Test Naukri API connection with a small request"""
    print("\n" + "="*60)
    print("TEST 8: Naukri API Connection (Test Request)")
    print("="*60)
    
    try:
        from jobspy.naukri import Naukri
        from jobspy.model import ScraperInput, Site, Country
        
        naukri = Naukri()
        
        scraper_input = ScraperInput(
            site_type=[Site.NAUKRI],
            search_term="java developer",
            location="Mumbai",
            country=Country.INDIA,
            results_wanted=2,  # Small test
            hours_old=72
        )
        
        logger.info("Sending test request to Naukri API...")
        response = naukri.scrape(scraper_input)
        
        print(f"✅ Naukri API responded successfully!")
        print(f"   - Jobs found: {len(response.jobs)}")
        
        if response.jobs:
            job = response.jobs[0]
            print(f"   - Sample job: {job.title} at {job.company_name}")
            if hasattr(job, 'skills') and job.skills:
                print(f"   - Skills: {job.skills[:3]}")
        
        return True
    except Exception as e:
        print(f"⚠️  Naukri API test failed (may be expected): {e}")
        print("   This could be due to network issues, API limits, or missing dependencies")
        return False  # Don't fail the test suite for this


def test_integration_functions():
    """Test high-level integration functions"""
    print("\n" + "="*60)
    print("TEST 9: Integration Functions")
    print("="*60)
    
    try:
        from linkedin_scraper.integrations import (
            scrape_multi_platform,
            scrape_indeed,
            scrape_naukri,
        )
        
        print("✅ Integration functions imported successfully")
        
        # Just verify function signatures exist
        import inspect
        
        sig = inspect.signature(scrape_multi_platform)
        print(f"   - scrape_multi_platform{sig}")
        
        sig = inspect.signature(scrape_indeed)
        print(f"   - scrape_indeed{sig}")
        
        sig = inspect.signature(scrape_naukri)
        print(f"   - scrape_naukri{sig}")
        
        print("\n✅ Integration functions available!")
        return True
    except Exception as e:
        print(f"❌ Integration functions test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "🧪 "*20)
    print("INDEED & NAUKRI INTEGRATION TESTS")
    print("🧪 "*20 + "\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("Scraper Instantiation", test_scraper_instantiation),
        ("Site Enum", test_site_enum),
        ("Country Enum", test_country_enum),
        ("ScraperInput Model", test_scraper_input),
        ("JobPost Model", test_job_post_model),
        ("Indeed API Connection", test_indeed_api_connection),
        ("Naukri API Connection", test_naukri_api_connection),
        ("Integration Functions", test_integration_functions),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("   API connection tests may fail due to network/rate limits.")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Indeed & Naukri Integration"
    )
    parser.add_argument(
        "--test", "-t",
        type=int,
        choices=range(1, 10),
        help="Run specific test (1-9). If not specified, runs all tests."
    )
    
    args = parser.parse_args()
    
    if args.test:
        tests = [
            test_imports,
            test_scraper_instantiation,
            test_site_enum,
            test_country_enum,
            test_scraper_input,
            test_job_post_model,
            test_indeed_api_connection,
            test_naukri_api_connection,
            test_integration_functions,
        ]
        try:
            tests[args.test - 1]()
        except Exception as e:
            print(f"❌ Test {args.test} crashed: {e}")
            import traceback
            traceback.print_exc()
    else:
        run_all_tests()
