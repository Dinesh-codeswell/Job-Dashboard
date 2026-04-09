#!/usr/bin/env python3
"""
UNIFIED AUTOMATION SCRIPT: Scrape + Sync
=========================================
Industry-standard automation workflow:
1. Scrape jobs from LinkedIn + Indeed
2. Sync to Supabase (with 3-day cleanup)
3. Comprehensive logging and error handling
4. Graceful failure handling (continues even if one step fails)

USAGE:
    python run_scraper_and_sync.py
    python run_scraper_and_sync.py --skip-scrape  # Only sync
    python run_scraper_and_sync.py --skip-sync    # Only scrape
"""

import sys
import os
import logging
import argparse
import asyncio
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f'automation_{datetime.now().strftime("%Y_%m_%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_scraper() -> bool:
    """
    Run the hybrid optimized scraper.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("="*70)
    logger.info("STEP 1: SCRAPING JOBS")
    logger.info("="*70)
    
    try:
        # Import scraper
        from scrape_hybrid_optimized import HybridOptimizedScraper
        
        # Create scraper instance
        scraper = HybridOptimizedScraper(
            platforms=["linkedin", "indeed"],
            max_days=2,  # Only jobs from past 2 days
            headless=True
        )
        
        # Run scraper
        logger.info("Starting scraper...")
        results = asyncio.run(scraper.run(
            target_total_jobs=100,  # Target 100 jobs
            linkedin_ratio=0.80     # 80% LinkedIn, 20% Indeed
        ))
        
        if results.get("success"):
            logger.info(f"✅ Scraping completed: {results['total_jobs']} jobs scraped")
            return True
        else:
            logger.error(f"❌ Scraping failed: {results.get('error', 'Unknown error')}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Scraping error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def run_sync() -> bool:
    """
    Run the sync engine to upload jobs to Supabase.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("="*70)
    logger.info("STEP 2: SYNCING TO SUPABASE")
    logger.info("="*70)
    
    try:
        # Import sync engine
        from sync_engine import sync_data
        
        # Run sync
        logger.info("Starting sync...")
        sync_data()
        
        logger.info("✅ Sync completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"❌ Sync error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main automation workflow."""
    parser = argparse.ArgumentParser(
        description="Unified automation: Scrape jobs and sync to Supabase"
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping, only run sync"
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Skip sync, only run scraping"
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("UNIFIED AUTOMATION STARTED")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*70)
    
    scrape_success = True
    sync_success = True
    
    # Step 1: Scrape (if not skipped)
    if not args.skip_scrape:
        scrape_success = run_scraper()
        
        if not scrape_success:
            logger.warning("⚠️  Scraping failed, but continuing to sync...")
    else:
        logger.info("⏭️  Scraping skipped (--skip-scrape)")
    
    # Step 2: Sync (if not skipped)
    if not args.skip_sync:
        sync_success = run_sync()
        
        if not sync_success:
            logger.error("❌ Sync failed")
    else:
        logger.info("⏭️  Sync skipped (--skip-sync)")
    
    # Summary
    logger.info("="*70)
    logger.info("AUTOMATION SUMMARY")
    logger.info("="*70)
    
    if not args.skip_scrape:
        logger.info(f"Scraping: {'✅ Success' if scrape_success else '❌ Failed'}")
    
    if not args.skip_sync:
        logger.info(f"Sync:     {'✅ Success' if sync_success else '❌ Failed'}")
    
    overall_success = scrape_success and sync_success
    
    if overall_success:
        logger.info("="*70)
        logger.info("✅ AUTOMATION COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        sys.exit(0)
    else:
        logger.info("="*70)
        logger.info("⚠️  AUTOMATION COMPLETED WITH ERRORS")
        logger.info("="*70)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
