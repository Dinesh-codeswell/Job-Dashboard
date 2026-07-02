#!/usr/bin/env python3
"""
WhatsApp Web Group Notifier
============================
Sends job notifications to WhatsApp group using WhatsApp Web automation.
Messages appear as sent by YOU (not a bot).

SAFETY FEATURES:
- Low risk configuration
- Rate limiting (3 seconds between messages)
- Session persistence (no repeated logins)
- Error handling and recovery
- Detailed logging

USAGE:
    python whatsapp_web_notifier.py --test       # Test mode (dry run)
    python whatsapp_web_notifier.py --force      # Send all jobs
    python whatsapp_web_notifier.py              # Normal run (new jobs only)
"""

import os
import sys
import json
import logging
import argparse
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Selenium not installed!")
    print("Run: pip install selenium webdriver-manager")
    sys.exit(1)

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f'whatsapp_web_{datetime.now().strftime("%Y_%m_%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
TRACKING_FILE = Path(__file__).parent / 'sent_jobs_web.json'
SESSION_FILE = Path(__file__).parent / 'whatsapp_session.json'
MAX_JOBS_PER_BATCH = int(os.getenv('MAX_JOBS_PER_BATCH', '30'))
MESSAGE_DELAY_SECONDS = 3  # 3 seconds for safety (low risk)
MAX_RETRIES = 2
WHATSAPP_GROUP_NAME = os.getenv('WHATSAPP_GROUP_NAME', '')

# Import company filter from main notifier
sys.path.insert(0, str(Path(__file__).parent))
from whatsapp_notifier import APPROVED_COMPANIES


class WhatsAppWebNotifier:
    """Handles WhatsApp Web automation for group messaging."""
    
    def __init__(self, headless: bool = False):
        """
        Initialize WhatsApp Web notifier.
        
        Args:
            headless: Run browser in headless mode (not recommended for first run)
        """
        self.driver = None
        self.headless = headless
        self.sent_jobs = self._load_sent_jobs()
        self.group_name = WHATSAPP_GROUP_NAME
        
        if not self.group_name:
            logger.error("WHATSAPP_GROUP_NAME not set in .env file!")
            raise ValueError("Please set WHATSAPP_GROUP_NAME in .env")
    
    def _load_sent_jobs(self) -> Dict[str, Any]:
        """Load tracking file of sent jobs."""
        if TRACKING_FILE.exists():
            try:
                with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('sent_jobs', []))} previously sent jobs")
                    return data
            except Exception as e:
                logger.warning(f"Failed to load tracking file: {e}")
        
        return {
            'last_sync': None,
            'sent_jobs': []
        }
    
    def _save_sent_jobs(self):
        """Save tracking file with automatic cleanup."""
        try:
            # Cleanup old entries (older than 30 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            cleaned_jobs = []
            removed_count = 0
            
            for sent_job in self.sent_jobs.get('sent_jobs', []):
                sent_at_str = sent_job.get('sent_at', '')
                try:
                    sent_at = datetime.fromisoformat(sent_at_str.replace('Z', '+00:00'))
                    if sent_at > cutoff_date:
                        cleaned_jobs.append(sent_job)
                    else:
                        removed_count += 1
                except:
                    cleaned_jobs.append(sent_job)
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old entries from tracking file")
            
            self.sent_jobs['sent_jobs'] = cleaned_jobs
            
            with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.sent_jobs, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Tracking file saved ({len(cleaned_jobs)} jobs tracked)")
        except Exception as e:
            logger.error(f"Failed to save tracking file: {e}")
    
    def _is_approved_company(self, company_name: str) -> bool:
        """Check if company is in approved tier 1 or tier 2 list."""
        if not company_name:
            return False
        
        try:
            company_str = str(company_name).strip()
        except:
            return False
        
        if not company_str or company_str.lower() in ['nan', 'none', '', 'unknown']:
            return False
        
        company_lower = company_str.lower()
        
        if company_lower in APPROVED_COMPANIES:
            return True
        
        for approved in APPROVED_COMPANIES:
            if approved in company_lower or company_lower in approved:
                return True
        
        return False
    
    def _is_job_sent(self, job: Dict[str, Any]) -> bool:
        """Check if job was already sent."""
        job_url = job.get('Job URL') or job.get('job_url', '')
        job_title = job.get('Job Title') or job.get('job_title', '')
        company = job.get('Company') or job.get('company', '')
        
        job_signature = f"{job_title}|{company}".lower()
        
        for sent_job in self.sent_jobs.get('sent_jobs', []):
            if job_url and sent_job.get('job_url') == job_url:
                return True
            
            sent_signature = f"{sent_job.get('job_title', '')}|{sent_job.get('company', '')}".lower()
            if job_signature and sent_signature and job_signature == sent_signature:
                return True
        
        return False
    
    def _mark_job_sent(self, job: Dict[str, Any]):
        """Mark job as sent and save immediately."""
        job_url = job.get('Job URL') or job.get('job_url', '')
        
        self.sent_jobs['sent_jobs'].append({
            'job_id': job.get('id', ''),
            'job_url': job_url,
            'job_title': job.get('Job Title') or job.get('job_title', ''),
            'company': job.get('Company') or job.get('company', ''),
            'sent_at': datetime.now(timezone.utc).isoformat()
        })
        
        self.sent_jobs['last_sync'] = datetime.now(timezone.utc).isoformat()
        self._save_sent_jobs()
        
        logger.debug(f"Marked job as sent: {job_url}")
    
    def _clean_posted_date(self, posted_date: str) -> str:
        """Clean posted date by removing applicant count information."""
        import re
        
        if not posted_date:
            return 'Recently'
        
        posted_date = re.sub(r'\s*Be among the first \d+ applicants.*', '', posted_date, flags=re.IGNORECASE)
        posted_date = re.sub(r'\s*\d+\s+applicants.*', '', posted_date, flags=re.IGNORECASE)
        posted_date = re.sub(r'\s*Over \d+\s+applicants.*', '', posted_date, flags=re.IGNORECASE)
        posted_date = ' '.join(posted_date.split())
        
        return posted_date.strip() or 'Recently'
    
    def format_message(self, job: Dict[str, Any]) -> str:
        """Format job as WhatsApp message (text only for group)."""
        job_title = job.get('Job Title') or job.get('job_title', 'Unknown Role')
        company = job.get('Company') or job.get('company', 'Unknown Company')
        location = job.get('Location') or job.get('location', 'Unknown Location')
        employment_type = job.get('Employment Type') or job.get('employment_type', '')
        job_url = job.get('Job URL') or job.get('job_url', '')
        posted_date_raw = job.get('Posted') or job.get('posted_date', 'Recently')
        
        posted_date = self._clean_posted_date(posted_date_raw)
        
        message = f"""🚀 *New Job Alert!*

📌 *Role:* {job_title}
🏢 *Company:* {company}"""
        
        if employment_type and employment_type.strip():
            message += f"\n💼 *Type:* {employment_type}"
        
        message += f"""
📍 *Location:* {location}
⏰ *Posted:* {posted_date}

🔗 *Apply Now:* {job_url}"""
        
        return message
    
    def init_driver(self):
        """Initialize Chrome driver with WhatsApp Web."""
        logger.info("Initializing Chrome driver...")
        
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # Add options for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Use user data directory to persist session
            user_data_dir = Path(__file__).parent / 'chrome_profile'
            user_data_dir.mkdir(exist_ok=True)
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("✅ Chrome driver initialized")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            return False
    
    def login_whatsapp(self):
        """Login to WhatsApp Web."""
        logger.info("Opening WhatsApp Web...")
        
        try:
            self.driver.get('https://web.whatsapp.com')
            
            # Wait for either QR code or chat list (already logged in)
            logger.info("Waiting for WhatsApp Web to load...")
            
            try:
                # Check if already logged in (chat list appears)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                )
                logger.info("✅ Already logged in!")
                return True
            except TimeoutException:
                # Need to scan QR code
                logger.info("⚠️  Please scan the QR code in the browser window...")
                logger.info("Waiting up to 60 seconds for QR code scan...")
                
                # Wait for login (chat list appears)
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                )
                
                logger.info("✅ QR code scanned successfully!")
                time.sleep(3)  # Wait for full load
                return True
        
        except TimeoutException:
            logger.error("❌ Timeout waiting for WhatsApp Web login")
            logger.error("Please scan the QR code within 60 seconds")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to login to WhatsApp Web: {e}")
            return False
    
    def open_group(self):
        """Open the specified WhatsApp group."""
        logger.info(f"Opening group: {self.group_name}")
        
        try:
            # Find search box
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            
            # Click and clear search box
            search_box.click()
            time.sleep(1)
            search_box.clear()
            
            # Type group name
            search_box.send_keys(self.group_name)
            time.sleep(2)
            
            # Press Enter to open group
            search_box.send_keys(Keys.ENTER)
            time.sleep(2)
            
            logger.info(f"✅ Opened group: {self.group_name}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to open group: {e}")
            logger.error(f"Make sure group name '{self.group_name}' is correct")
            return False
    
    def send_message(self, message: str) -> bool:
        """Send message to the open group."""
        try:
            # Find message input box
            message_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
            
            # Click message box
            message_box.click()
            time.sleep(0.5)
            
            # Type message (line by line to preserve formatting)
            lines = message.split('\n')
            for i, line in enumerate(lines):
                message_box.send_keys(line)
                if i < len(lines) - 1:
                    # Shift+Enter for new line
                    message_box.send_keys(Keys.SHIFT, Keys.ENTER)
            
            time.sleep(0.5)
            
            # Send message
            message_box.send_keys(Keys.ENTER)
            
            logger.debug("Message sent successfully")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False
    
    def notify_new_jobs(self, jobs: List[Dict[str, Any]], test_mode: bool = False) -> Dict[str, Any]:
        """Send notifications for new jobs to WhatsApp group."""
        logger.info("="*70)
        logger.info("WHATSAPP WEB NOTIFICATION BATCH STARTED")
        logger.info(f"Total jobs to process: {len(jobs)}")
        logger.info(f"Test mode: {test_mode}")
        logger.info(f"Target group: {self.group_name}")
        logger.info("="*70)
        
        # Filter by approved companies
        approved_jobs = []
        filtered_count = 0
        
        for job in jobs:
            company = job.get('Company') or job.get('company', '')
            if self._is_approved_company(company):
                approved_jobs.append(job)
            else:
                filtered_count += 1
        
        logger.info(f"Approved companies: {len(approved_jobs)} jobs")
        logger.info(f"Filtered out: {filtered_count} jobs (not tier 1/2 companies)")
        
        # Filter new jobs
        new_jobs = [job for job in approved_jobs if not self._is_job_sent(job)]
        
        if not new_jobs:
            logger.info("✅ No new jobs from approved companies to send")
            return {
                'total_jobs': len(jobs),
                'approved_jobs': len(approved_jobs),
                'filtered_jobs': filtered_count,
                'new_jobs': 0,
                'sent': 0,
                'failed': 0
            }
        
        logger.info(f"Found {len(new_jobs)} new jobs from approved companies")
        
        # Limit batch size
        if len(new_jobs) > MAX_JOBS_PER_BATCH:
            logger.warning(f"Limiting batch to {MAX_JOBS_PER_BATCH} jobs (found {len(new_jobs)})")
            new_jobs = new_jobs[:MAX_JOBS_PER_BATCH]
        
        # Test mode - just show what would be sent
        if test_mode:
            logger.info("TEST MODE - Would send these messages:")
            for i, job in enumerate(new_jobs, 1):
                job_title = job.get('Job Title') or job.get('job_title', 'Unknown')
                company = job.get('Company') or job.get('company', 'Unknown')
                logger.info(f"[{i}/{len(new_jobs)}] {job_title} at {company}")
                message = self.format_message(job)
                print(f"\n{message}\n{'-'*70}\n")
            
            return {
                'total_jobs': len(jobs),
                'approved_jobs': len(approved_jobs),
                'filtered_jobs': filtered_count,
                'new_jobs': len(new_jobs),
                'sent': len(new_jobs),
                'failed': 0
            }
        
        # Initialize browser and login
        if not self.init_driver():
            logger.error("Failed to initialize driver")
            return {'total_jobs': len(jobs), 'new_jobs': len(new_jobs), 'sent': 0, 'failed': len(new_jobs)}
        
        if not self.login_whatsapp():
            logger.error("Failed to login to WhatsApp Web")
            self.cleanup()
            return {'total_jobs': len(jobs), 'new_jobs': len(new_jobs), 'sent': 0, 'failed': len(new_jobs)}
        
        if not self.open_group():
            logger.error("Failed to open group")
            self.cleanup()
            return {'total_jobs': len(jobs), 'new_jobs': len(new_jobs), 'sent': 0, 'failed': len(new_jobs)}
        
        # Send messages
        sent_count = 0
        failed_count = 0
        
        for i, job in enumerate(new_jobs, 1):
            job_title = job.get('Job Title') or job.get('job_title', 'Unknown')
            company = job.get('Company') or job.get('company', 'Unknown')
            
            logger.info(f"[{i}/{len(new_jobs)}] Processing: {job_title} at {company}")
            
            message = self.format_message(job)
            
            if self.send_message(message):
                sent_count += 1
                self._mark_job_sent(job)
                logger.info(f"✅ Sent: {job_title} at {company}")
            else:
                failed_count += 1
                logger.error(f"❌ Failed: {job_title} at {company}")
            
            # Rate limiting (3 seconds for safety)
            if i < len(new_jobs):
                logger.debug(f"Waiting {MESSAGE_DELAY_SECONDS} seconds...")
                time.sleep(MESSAGE_DELAY_SECONDS)
        
        # Cleanup
        self.cleanup()
        
        # Summary
        logger.info("="*70)
        logger.info("BATCH SUMMARY")
        logger.info(f"Total jobs: {len(jobs)}")
        logger.info(f"Approved companies: {len(approved_jobs)}")
        logger.info(f"Filtered out: {filtered_count}")
        logger.info(f"New jobs: {len(new_jobs)}")
        logger.info(f"Sent: {sent_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info("="*70)
        
        return {
            'total_jobs': len(jobs),
            'approved_jobs': len(approved_jobs),
            'filtered_jobs': filtered_count,
            'new_jobs': len(new_jobs),
            'sent': sent_count,
            'failed': failed_count
        }
    
    def cleanup(self):
        """Cleanup browser resources."""
        if self.driver:
            try:
                logger.info("Closing browser...")
                self.driver.quit()
                logger.info("✅ Browser closed")
            except:
                pass


def fetch_jobs_from_sheets() -> List[Dict[str, Any]]:
    """Fetch jobs from Google Sheets."""
    logger.info("Fetching jobs from Google Sheets...")
    
    try:
        from dashboard.data.sheets_fetcher import get_data_fetcher
        
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        
        if not sheet_id:
            logger.error("GOOGLE_SHEET_ID not set in .env")
            return []
        
        fetcher = get_data_fetcher(sheet_id, credentials_file)
        jobs = fetcher.fetch_all_jobs(use_cache=False)
        
        logger.info(f"✅ Fetched {len(jobs)} jobs from Google Sheets")
        return jobs
    
    except Exception as e:
        logger.error(f"❌ Failed to fetch jobs: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WhatsApp Web Group Notification Automation"
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode (dry run, no actual messages sent)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force send all jobs (ignore sent history)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (not recommended for first run)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("WHATSAPP WEB GROUP NOTIFIER STARTED")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Test mode: {args.test}")
    logger.info(f"Force mode: {args.force}")
    logger.info(f"Headless: {args.headless}")
    logger.info("="*70)
    
    try:
        # Initialize notifier
        notifier = WhatsAppWebNotifier(headless=args.headless)
        
        # Force mode: clear sent history
        if args.force:
            logger.warning("FORCE MODE: Clearing sent job history")
            notifier.sent_jobs = {'last_sync': None, 'sent_jobs': []}
        
        # Fetch jobs
        jobs = fetch_jobs_from_sheets()
        
        if not jobs:
            logger.warning("No jobs fetched, exiting")
            sys.exit(0)
        
        # Send notifications
        summary = notifier.notify_new_jobs(jobs, test_mode=args.test)
        
        # Exit code
        if summary['failed'] > 0:
            logger.warning("⚠️ Some messages failed to send")
            sys.exit(1)
        else:
            logger.info("✅ All messages sent successfully")
            sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
