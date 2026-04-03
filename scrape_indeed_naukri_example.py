#!/usr/bin/env python3
"""
Example script demonstrating Indeed and Naukri job scraping with AUTO-SAVE.

This script shows how to:
1. Scrape jobs from Indeed and Naukri
2. Auto-save results to CSV, Excel, SQLite, etc.
3. Filter by location, job type, and freshness
4. Handle remote jobs

Usage:
    python scrape_indeed_naukri_example.py

Requirements:
    pip install -r requirements.txt
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from linkedin_scraper.integrations import (
    scrape_multi_platform,
    scrape_indeed,
    scrape_naukri,
    scrape_linkedin_indeed_naukri,
    JobStorage,
    auto_save_jobs,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_scrape_with_auto_save():
    """
    Example 1: Basic scraping with AUTO-SAVE enabled
    """
    print("\n" + "="*60)
    print("Example 1: Basic Scraping with AUTO-SAVE")
    print("="*60)
    
    # Scrape and auto-save to CSV + Excel (default formats)
    result = scrape_multi_platform(
        sites=["indeed", "naukri"],
        search_term="software engineer",
        location="Bangalore",
        results_wanted=10,
        hours_old=168,  # Last 7 days
        verbose=2,
        auto_save=True,  # ✅ Enable auto-save
        output_dir="output/example_jobs"
    )
    
    # Access results
    df = result['dataframe']
    saved_files = result['saved_files']
    total_jobs = result['total_jobs']
    
    print(f"\n✅ Found {total_jobs} total jobs")
    print(f"\n📁 Saved to:")
    for format_type, filepath in saved_files.items():
        print(f"   - {format_type}: {filepath}")
    
    return result


def example_2_save_to_multiple_formats():
    """
    Example 2: Save to multiple formats (CSV, Excel, JSON, SQLite)
    """
    print("\n" + "="*60)
    print("Example 2: Save to Multiple Formats")
    print("="*60)
    
    result = scrape_multi_platform(
        sites=["indeed", "naukri"],
        search_term="python developer",
        location="Mumbai",
        results_wanted=15,
        auto_save=True,
        save_formats=['csv', 'excel', 'json', 'sqlite']  # ✅ Multiple formats
    )
    
    print(f"\n✅ Found {result['total_jobs']} jobs")
    print(f"\n📁 Saved to:")
    for fmt, path in result['saved_files'].items():
        print(f"   - {fmt}: {path}")
    
    return result


def example_3_manual_storage():
    """
    Example 3: Manual storage control with JobStorage class
    """
    print("\n" + "="*60)
    print("Example 3: Manual Storage with JobStorage Class")
    print("="*60)
    
    # Scrape without auto-save
    df = scrape_multi_platform(
        sites=["indeed", "naukri"],
        search_term="data scientist",
        location="Pune",
        results_wanted=10,
        auto_save=False  # Manual save
    )
    
    print(f"\n✅ Found {len(df)} jobs")
    
    # Manual storage with custom logic
    storage = JobStorage(output_dir="output/manual_jobs")
    
    # Save to all formats
    saved = storage.save_all(
        df,
        save_csv=True,
        save_excel=True,
        save_json=True,
        save_parquet=False,
        save_sqlite=True
    )
    
    print(f"\n📁 Manually saved to:")
    for fmt, path in saved.items():
        print(f"   - {fmt}: {path}")
    
    # Save per-platform
    for site in df['site'].unique():
        site_df = df[df['site'] == site]
        storage.save_to_csv(site_df, filename=f"{site}_jobs.csv")
        print(f"   - Saved {len(site_df)} {site} jobs to {site}_jobs.csv")
    
    return df


def example_4_remote_jobs():
    """
    Example 4: Find remote jobs only
    """
    print("\n" + "="*60)
    print("Example 4: Remote Jobs Only")
    print("="*60)
    
    result = scrape_multi_platform(
        sites=["indeed", "naukri"],
        search_term="full stack developer",
        is_remote=True,
        results_wanted=15,
        hours_old=72,
        auto_save=True,
        save_formats=['csv', 'excel']
    )
    
    print(f"\n✅ Found {result['total_jobs']} remote jobs")
    
    return result


def example_5_single_platform():
    """
    Example 5: Scrape from a single platform with auto-save
    """
    print("\n" + "="*60)
    print("Example 5: Single Platform Scraping")
    print("="*60)
    
    # Indeed only
    print("\n--- Indeed ---")
    indeed_result = scrape_multi_platform(
        sites=["indeed"],
        search_term="java developer",
        location="Hyderabad",
        results_wanted=10,
        auto_save=True,
        output_dir="output/indeed_jobs"
    )
    print(f"Found {indeed_result['total_jobs']} jobs on Indeed")
    
    # Naukri only
    print("\n--- Naukri ---")
    naukri_result = scrape_multi_platform(
        sites=["naukri"],
        search_term="java developer",
        location="Chennai",
        results_wanted=10,
        auto_save=True,
        output_dir="output/naukri_jobs"
    )
    print(f"Found {naukri_result['total_jobs']} jobs on Naukri")
    
    return indeed_result, naukri_result


def example_6_convenience_function():
    """
    Example 6: Using auto_save_jobs() convenience function
    """
    print("\n" + "="*60)
    print("Example 6: Using auto_save_jobs() Convenience Function")
    print("="*60)
    
    # Scrape first
    df = scrape_multi_platform(
        sites=["indeed", "naukri"],
        search_term="machine learning",
        location="Bangalore",
        results_wanted=10,
        auto_save=False
    )
    
    # Then auto-save with convenience function
    saved = auto_save_jobs(
        df,
        output_dir="output/quick_save",
        formats=['csv', 'excel']  # Quick formats
    )
    
    print(f"\n✅ Found {len(df)} jobs")
    print(f"\n📁 Auto-saved to:")
    for fmt, path in saved.items():
        print(f"   - {fmt}: {path}")
    
    return df


def example_7_all_three_platforms():
    """
    Example 7: Scrape from LinkedIn, Indeed, and Naukri
    """
    print("\n" + "="*60)
    print("Example 7: All Three Platforms")
    print("="*60)
    
    result = scrape_multi_platform(
        sites=["linkedin", "indeed", "naukri"],
        search_term="consultant",
        location="Gurugram",
        results_wanted=10,
        hours_old=240,
        auto_save=True,
        save_formats=['csv', 'excel', 'sqlite']
    )
    
    print(f"\n✅ Found {result['total_jobs']} total jobs")
    print(f"\n📁 Saved to:")
    for fmt, path in result['saved_files'].items():
        print(f"   - {fmt}: {path}")
    
    return result


def example_8_custom_storage_options():
    """
    Example 8: Custom storage configuration
    """
    print("\n" + "="*60)
    print("Example 8: Custom Storage Configuration")
    print("="*60)
    
    df = scrape_multi_platform(
        sites=["indeed", "naukri"],
        search_term="devops engineer",
        results_wanted=10
    )
    
    print(f"\n✅ Found {len(df)} jobs")
    
    # Custom storage with Google Sheets config (if available)
    storage = JobStorage(
        output_dir="output/custom_jobs",
        # google_sheet_id="your-sheet-id",  # Uncomment if configured
        # google_credentials_file="credentials.json"
    )
    
    # Save with custom filenames
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    storage.save_to_csv(
        df,
        filename=f"devops_jobs_{timestamp}.csv",
        include_timestamp=False
    )
    
    storage.save_to_excel(
        df,
        filename=f"devops_report_{timestamp}.xlsx",
        include_summary=True,
        split_by_site=True
    )
    
    storage.save_to_sqlite(
        df,
        table_name="devops_jobs",
        database_path="output/custom_jobs/jobs.db"
    )
    
    print(f"\n📁 Custom saved to output/custom_jobs/")
    
    return df


def run_all_examples():
    """
    Run all examples sequentially
    """
    print("\n" + "🚀 "*20)
    print("INDEED & NAUKRI SCRAPER EXAMPLES (WITH AUTO-SAVE)")
    print("🚀 "*20 + "\n")
    
    results = {}
    
    try:
        results['basic_auto_save'] = example_1_basic_scrape_with_auto_save()
    except Exception as e:
        print(f"❌ Example 1 failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['multi_format'] = example_2_save_to_multiple_formats()
    except Exception as e:
        print(f"❌ Example 2 failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['manual'] = example_3_manual_storage()
    except Exception as e:
        print(f"❌ Example 3 failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['remote'] = example_4_remote_jobs()
    except Exception as e:
        print(f"❌ Example 4 failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['single'] = example_5_single_platform()
    except Exception as e:
        print(f"❌ Example 5 failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['convenience'] = example_6_convenience_function()
    except Exception as e:
        print(f"❌ Example 6 failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['all_three'] = example_7_all_three_platforms()
    except Exception as e:
        print(f"❌ Example 7 failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['custom'] = example_8_custom_storage_options()
    except Exception as e:
        print(f"❌ Example 8 failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ ALL EXAMPLES COMPLETED")
    print("="*60)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Indeed & Naukri Job Scraper Examples (with Auto-Save)"
    )
    parser.add_argument(
        "--example", "-e",
        type=int,
        choices=range(1, 9),
        help="Run specific example (1-8). If not specified, runs all examples."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for saved files"
    )
    
    args = parser.parse_args()
    
    if args.example:
        examples = {
            1: example_1_basic_scrape_with_auto_save,
            2: example_2_save_to_multiple_formats,
            3: example_3_manual_storage,
            4: example_4_remote_jobs,
            5: example_5_single_platform,
            6: example_6_convenience_function,
            7: example_7_all_three_platforms,
            8: example_8_custom_storage_options,
        }
        try:
            examples[args.example]()
        except Exception as e:
            print(f"❌ Example {args.example} failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        run_all_examples()
