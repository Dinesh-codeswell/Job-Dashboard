#!/usr/bin/env python3
"""
Automated Job Scraper Runner

This script runs the unified India jobs scraper (LinkedIn + Indeed + Naukri)
with proper error handling, logging, and crash recovery.

Designed to be executed every 15 minutes via Windows Task Scheduler.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import traceback

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"scraper_{datetime.now().strftime('%Y_%m_%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_prerequisites():
    """Check if all prerequisites are met."""
    logger.info("=" * 70)
    logger.info("🔍 CHECKING PREREQUISITES")
    logger.info("=" * 70)
    
    # Check .env file
    if not os.path.exists('.env'):
        logger.error("❌ .env file not found. Please create it from .env.example")
        return False
    logger.info("✓ .env file found")
    
    # Check credentials
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    if not os.path.exists(credentials_file):
        logger.error(f"❌ Google credentials file not found: {credentials_file}")
        return False
    logger.info(f"✓ Google credentials file found: {credentials_file}")
    
    # Check LinkedIn session
    if not os.path.exists('linkedin_session.json'):
        logger.warning("⚠️  LinkedIn session file not found. LinkedIn scraping may fail.")
        logger.warning("   Run: python samples/create_session.py")
    else:
        logger.info("✓ LinkedIn session file found")
    
    # Check required environment variables
    required_vars = ['GOOGLE_SHEET_ID']
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"❌ Missing required environment variable: {var}")
            return False
    logger.info("✓ Required environment variables set")
    
    logger.info("✅ All prerequisites met\n")
    return True


async def run_scraper():
    """Run the unified India jobs scraper."""
    try:
        logger.info("=" * 70)
        logger.info("🚀 STARTING AUTOMATED JOB SCRAPER")
        logger.info(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        # Import the scraper
        from scrape_all_india_jobs import UnifiedIndiaJobsScraper
        
        # Create scraper instance with updated settings
        scraper = UnifiedIndiaJobsScraper(
            platforms=['linkedin', 'indeed', 'naukri'],
            max_days=3,  # 3-day window to match dashboard
            headless=True  # Run in headless mode for automation
        )

        # Run with round-robin strategy for maximum diversity
        # Includes both consulting roles AND internships
        results = await scraper.run_round_robin(
            cities=None,  # Use default cities from .env
            include_internships=True,  # Include consulting internships
            limit_per_city=30,  # Moderate limit to avoid rate limiting
            tier_1_only=False,
            batch_size=10  # Process 10 tasks at a time
        )
        
        if results.get('success'):
            logger.info("=" * 70)
            logger.info("✅ SCRAPER COMPLETED SUCCESSFULLY")
            logger.info(f"📊 Total jobs processed: {results.get('total_jobs', 0)}")
            logger.info(f"📈 Stats: {results.get('stats', {})}")
            logger.info("=" * 70)
            return True
        else:
            logger.error("❌ Scraper failed: " + results.get('error', 'Unknown error'))
            return False
            
    except Exception as e:
        logger.error("=" * 70)
        logger.error("❌ FATAL ERROR IN SCRAPER")
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())
        logger.error("=" * 70)
        return False


def log_completion(success: bool, duration: float):
    """Log completion summary."""
    logger.info("=" * 70)
    if success:
        logger.info("✅ AUTOMATED RUN COMPLETED SUCCESSFULLY")
    else:
        logger.warning("⚠️  AUTOMATED RUN COMPLETED WITH ERRORS")
    logger.info(f"⏱️  Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
    logger.info(f"⏰ Next run in 15 minutes")
    logger.info("=" * 70 + "\n")


async def main():
    """Main entry point."""
    import time
    
    start_time = time.time()
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("❌ Prerequisites check failed. Aborting.")
        sys.exit(1)
    
    # Run the scraper
    success = await run_scraper()
    
    # Log completion
    duration = time.time() - start_time
    log_completion(success, duration)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️  Scraper interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
