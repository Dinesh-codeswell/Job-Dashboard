#!/usr/bin/env python3
"""
WhatsApp Job Notification Automation
=====================================
Sends newly added jobs from Google Sheets to WhatsApp every 30 minutes.

Supports:
- Twilio WhatsApp API (recommended for ease of use)
- WhatsApp Business Cloud API (recommended for cost - FREE)

USAGE:
    python whatsapp_notifier.py              # Normal run
    python whatsapp_notifier.py --test       # Test mode (dry run)
    python whatsapp_notifier.py --force      # Force send all jobs
"""

import os
import sys
import json
import logging
import argparse
import time
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f'whatsapp_notifications_{datetime.now().strftime("%Y_%m_%d")}.log'

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
TRACKING_FILE = Path(__file__).parent / 'sent_jobs.json'
MAX_JOBS_PER_BATCH = int(os.getenv('MAX_JOBS_PER_BATCH', '30'))  # Changed default to 30
MESSAGE_DELAY_SECONDS = int(os.getenv('MESSAGE_DELAY_SECONDS', '2'))
MAX_RETRIES = 3

# Tier 1 & Tier 2 Companies Filter
TIER_1_COMPANIES = [
    # Big 4 Consulting
    'deloitte', 'pwc', 'pricewaterhousecoopers', 'ey', 'ernst & young', 'kpmg',
    
    # MBB (Top Strategy Consulting)
    'mckinsey', 'mckinsey & company', 'bain', 'bain & company', 'bcg', 
    'boston consulting group',
    
    # Big Tech (FAANG+)
    'google', 'alphabet', 'meta', 'facebook', 'amazon', 'apple', 'microsoft',
    'netflix', 'tesla', 'nvidia', 'adobe', 'salesforce', 'oracle', 'ibm',
    'intel', 'cisco', 'qualcomm', 'uber', 'airbnb', 'twitter', 'x corp',
    
    # Indian IT Giants
    'tcs', 'tata consultancy services', 'infosys', 'wipro', 'hcl', 
    'hcl technologies', 'tech mahindra', 'ltimindtree', 'lti', 'mindtree',
    
    # Indian Conglomerates
    'reliance', 'reliance industries', 'tata', 'tata group', 'aditya birla',
    'mahindra', 'mahindra & mahindra', 'larsen & toubro', 'l&t',
    
    # Top Startups (Unicorns)
    'flipkart', 'paytm', 'ola', 'swiggy', 'zomato', 'byju', 'oyo',
    'razorpay', 'cred', 'meesho', 'phonepe', 'dream11', 'upstox',
    'zerodha', 'policybazaar', 'nykaa', 'freshworks', 'postman',
    
    # E-commerce & Retail
    'walmart', 'target', 'alibaba', 'jd.com', 'shopify',
    
    # Financial Services
    'jpmorgan', 'jp morgan', 'goldman sachs', 'morgan stanley', 'citigroup',
    'citi', 'hsbc', 'barclays', 'deutsche bank', 'ubs', 'credit suisse',
    'blackrock', 'vanguard', 'fidelity', 'american express', 'amex',
    'mastercard', 'visa', 'paypal',
    
    # Indian Banks & Financial
    'hdfc', 'icici', 'sbi', 'state bank of india', 'axis bank', 'kotak',
    'kotak mahindra', 'yes bank', 'idfc',
]

TIER_2_COMPANIES = [
    # Consulting Firms
    'accenture', 'capgemini', 'cognizant', 'genpact', 'mu sigma',
    'fractal analytics', 'latentview', 'tiger analytics', 'evalueserve',
    'zs associates', 'oliver wyman', 'at kearney', 'booz allen',
    'roland berger', 'strategy&', 'pwc strategy&',
    
    # Tech Companies
    'dell', 'hp', 'hewlett packard', 'sap', 'vmware', 'servicenow',
    'workday', 'snowflake', 'databricks', 'atlassian', 'slack',
    'zoom', 'docusign', 'twilio', 'stripe', 'square', 'paypal',
    
    # Indian Mid-size Tech
    'mphasis', 'persistent', 'cyient', 'zensar', 'hexaware',
    'birlasoft', 'coforge', 'sonata software', 'mindtree',
    
    # Startups (Series B+)
    'udaan', 'sharechat', 'apna', 'vedantu', 'unacademy', 'groww',
    'licious', 'urban company', 'dunzo', 'delhivery', 'blackbuck',
    'rivigo', 'cure.fit', 'cult.fit', 'pharmeasy', '1mg',
    
    # Automotive
    'maruti', 'hyundai', 'honda', 'toyota', 'ford', 'bmw', 'mercedes',
    'audi', 'volkswagen', 'tata motors', 'mahindra automotive',
    
    # FMCG & Retail
    'unilever', 'hindustan unilever', 'hul', 'procter & gamble', 'p&g',
    'nestle', 'coca-cola', 'pepsico', 'itc', 'dabur', 'marico',
    'godrej', 'britannia', 'parle',
    
    # Pharma & Healthcare
    'pfizer', 'novartis', 'roche', 'johnson & johnson', 'abbott',
    'sun pharma', 'dr reddy', 'cipla', 'lupin', 'biocon',
    'apollo hospitals', 'fortis', 'max healthcare', 'manipal',
    
    # Telecom
    'airtel', 'bharti airtel', 'vodafone', 'jio', 'reliance jio',
    
    # Media & Entertainment
    'disney', 'hotstar', 'sony', 'zee', 'viacom', 'times internet',
    'network18', 'ndtv',
]

# Combine all approved companies
APPROVED_COMPANIES = set([company.lower() for company in TIER_1_COMPANIES + TIER_2_COMPANIES])


class WhatsAppNotifier:
    """Handles WhatsApp notifications via Twilio or WhatsApp Business Cloud API."""
    
    def __init__(self, api_provider: str = 'auto'):
        """
        Initialize WhatsApp notifier.
        
        Args:
            api_provider: 'twilio', 'cloud', or 'auto' (auto-detect)
        """
        self.api_provider = api_provider
        self.sent_jobs = self._load_sent_jobs()
        
        # Auto-detect API provider
        if api_provider == 'auto':
            if os.getenv('TWILIO_ACCOUNT_SID'):
                self.api_provider = 'twilio'
                logger.info("Using Twilio WhatsApp API")
            elif os.getenv('WHATSAPP_ACCESS_TOKEN'):
                self.api_provider = 'cloud'
                logger.info("Using WhatsApp Business Cloud API")
            else:
                logger.error("No WhatsApp API credentials found!")
                logger.error("Set either TWILIO_ACCOUNT_SID or WHATSAPP_ACCESS_TOKEN in .env")
                sys.exit(1)
        
        # Initialize API client
        if self.api_provider == 'twilio':
            self._init_twilio()
        elif self.api_provider == 'cloud':
            self._init_cloud_api()
    
    def _init_twilio(self):
        """Initialize Twilio client."""
        try:
            from twilio.rest import Client
            
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.twilio_from = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
            self.whatsapp_to = os.getenv('WHATSAPP_TO')
            
            if not all([account_sid, auth_token, self.whatsapp_to]):
                logger.error("Missing Twilio credentials in .env")
                sys.exit(1)
            
            self.twilio_client = Client(account_sid, auth_token)
            logger.info("✅ Twilio client initialized")
        
        except ImportError:
            logger.error("Twilio library not installed. Run: pip install twilio")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {e}")
            sys.exit(1)
    
    def _init_cloud_api(self):
        """Initialize WhatsApp Business Cloud API."""
        self.whatsapp_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.whatsapp_recipient = os.getenv('WHATSAPP_RECIPIENT')
        
        if not all([self.whatsapp_token, self.whatsapp_phone_id, self.whatsapp_recipient]):
            logger.error("Missing WhatsApp Cloud API credentials in .env")
            sys.exit(1)
        
        self.cloud_api_url = f"https://graph.facebook.com/v18.0/{self.whatsapp_phone_id}/messages"
        logger.info("✅ WhatsApp Cloud API initialized")
    
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
        """
        Save tracking file with automatic cleanup.
        Removes jobs older than 30 days to prevent file from growing too large.
        """
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
                    # Keep jobs with invalid dates
                    cleaned_jobs.append(sent_job)
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old entries from tracking file")
            
            self.sent_jobs['sent_jobs'] = cleaned_jobs
            
            # Save to file
            with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.sent_jobs, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Tracking file saved ({len(cleaned_jobs)} jobs tracked)")
        except Exception as e:
            logger.error(f"Failed to save tracking file: {e}")
    
    def _is_approved_company(self, company_name: str) -> bool:
        """
        Check if company is in approved tier 1 or tier 2 list.
        
        Args:
            company_name: Company name from job listing
        
        Returns:
            True if company is approved, False otherwise
        """
        if not company_name:
            return False
        
        # Handle non-string types (float, NaN, etc.)
        try:
            company_str = str(company_name).strip()
        except:
            return False
        
        # Check for empty or invalid values
        if not company_str or company_str.lower() in ['nan', 'none', '', 'unknown']:
            return False
        
        company_lower = company_str.lower()
        
        # Direct match
        if company_lower in APPROVED_COMPANIES:
            return True
        
        # Partial match (company name contains approved company)
        for approved in APPROVED_COMPANIES:
            if approved in company_lower or company_lower in approved:
                return True
        
        return False
    
    def _is_job_sent(self, job: Dict[str, Any]) -> bool:
        """
        Check if job was already sent.
        Uses both job URL and job title+company for robust deduplication.
        """
        job_url = job.get('Job URL') or job.get('job_url', '')
        job_title = job.get('Job Title') or job.get('job_title', '')
        company = job.get('Company') or job.get('company', '')
        
        # Create a unique identifier
        job_signature = f"{job_title}|{company}".lower()
        
        for sent_job in self.sent_jobs.get('sent_jobs', []):
            # Check by URL (primary method)
            if job_url and sent_job.get('job_url') == job_url:
                return True
            
            # Check by title+company (backup method for jobs with same/similar URLs)
            sent_signature = f"{sent_job.get('job_title', '')}|{sent_job.get('company', '')}".lower()
            if job_signature and sent_signature and job_signature == sent_signature:
                return True
        
        return False
    
    def _mark_job_sent(self, job: Dict[str, Any]):
        """
        Mark job as sent in tracking file and save immediately.
        This ensures the tracking file is updated even if the script is aborted.
        """
        job_url = job.get('Job URL') or job.get('job_url', '')
        
        # Add to sent jobs list
        self.sent_jobs['sent_jobs'].append({
            'job_id': job.get('id', ''),
            'job_url': job_url,
            'job_title': job.get('Job Title') or job.get('job_title', ''),
            'company': job.get('Company') or job.get('company', ''),
            'sent_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Update last sync timestamp
        self.sent_jobs['last_sync'] = datetime.now(timezone.utc).isoformat()
        
        # IMPORTANT: Save immediately after each job is sent
        # This prevents duplicates if the script is aborted mid-run
        self._save_sent_jobs()
        
        logger.debug(f"Marked job as sent and saved to tracking file: {job_url}")
    
    def _clean_posted_date(self, posted_date: str) -> str:
        """
        Clean posted date by removing applicant count information.
        
        Examples:
            "8 hours ago   Be among the first 25 applicants" -> "8 hours ago"
            "12 hours ago  86 applicants" -> "12 hours ago"
            "20 hours ago   Be among the first 25 applicants" -> "20 hours ago"
        
        Args:
            posted_date: Raw posted date string
        
        Returns:
            Cleaned posted date string
        """
        import re
        
        if not posted_date:
            return 'Recently'
        
        # Remove applicant count patterns
        # Pattern 1: "Be among the first X applicants"
        posted_date = re.sub(r'\s*Be among the first \d+ applicants.*', '', posted_date, flags=re.IGNORECASE)
        
        # Pattern 2: "X applicants"
        posted_date = re.sub(r'\s*\d+\s+applicants.*', '', posted_date, flags=re.IGNORECASE)
        
        # Pattern 3: "Over X applicants"
        posted_date = re.sub(r'\s*Over \d+\s+applicants.*', '', posted_date, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        posted_date = ' '.join(posted_date.split())
        
        return posted_date.strip() or 'Recently'
    
    def format_message(self, job: Dict[str, Any]) -> tuple[str, str]:
        """
        Format job as WhatsApp message with company logo.
        
        Args:
            job: Job dictionary from Google Sheets
        
        Returns:
            Tuple of (message_text, company_logo_url)
        """
        """
        Format job as WhatsApp message with company logo.
        
        Args:
            job: Job dictionary from Google Sheets
        
        Returns:
            Formatted message string
        """
        # Extract job details
        job_title = job.get('Job Title') or job.get('job_title', 'Unknown Role')
        company = job.get('Company') or job.get('company', 'Unknown Company')
        company_logo = job.get('Company Logo') or job.get('company_logo', '')
        location = job.get('Location') or job.get('location', 'Unknown Location')
        employment_type = job.get('Employment Type') or job.get('employment_type', '')
        job_url = job.get('Job URL') or job.get('job_url', '')
        posted_date_raw = job.get('Posted') or job.get('posted_date', 'Recently')
        
        # Clean posted date (remove applicant counts)
        posted_date = self._clean_posted_date(posted_date_raw)
        
        # Format message with template (without logo URL in text)
        message = f"""🚀 *New Job Alert!*

📌 *Role:* {job_title}
🏢 *Company:* {company}"""
        
        # Add employment type if available
        if employment_type and employment_type.strip():
            message += f"\n💼 *Type:* {employment_type}"
        
        message += f"""
📍 *Location:* {location}
⏰ *Posted:* {posted_date}

🔗 *Apply Now:* {job_url}"""
        
        # Return message and logo URL separately
        return message, company_logo if company_logo and company_logo.strip() else None
    
    def send_via_twilio(self, message: str, media_url: str = None) -> bool:
        """
        Send message via Twilio WhatsApp API with optional media.
        
        Args:
            message: Message to send
            media_url: Optional image URL to send with message
        
        Returns:
            True if successful
        """
        try:
            # Prepare message parameters
            msg_params = {
                'from_': self.twilio_from,
                'body': message,
                'to': self.whatsapp_to
            }
            
            # Add media URL if provided
            if media_url and media_url.strip():
                msg_params['media_url'] = [media_url]
            
            msg = self.twilio_client.messages.create(**msg_params)
            
            logger.info(f"✅ Sent via Twilio (SID: {msg.sid})")
            return True
        
        except Exception as e:
            logger.error(f"❌ Twilio send failed: {e}")
            return False
    
    def send_via_cloud_api(self, message: str, media_url: str = None) -> bool:
        """
        Send message via WhatsApp Business Cloud API with optional media.
        
        Args:
            message: Message to send
            media_url: Optional image URL to send with message
        
        Returns:
            True if successful
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.whatsapp_token}',
                'Content-Type': 'application/json'
            }
            
            # If media URL provided, send as image with caption
            if media_url and media_url.strip():
                payload = {
                    'messaging_product': 'whatsapp',
                    'recipient_type': 'individual',
                    'to': self.whatsapp_recipient,
                    'type': 'image',
                    'image': {
                        'link': media_url,
                        'caption': message
                    }
                }
            else:
                # Send as text only
                payload = {
                    'messaging_product': 'whatsapp',
                    'recipient_type': 'individual',
                    'to': self.whatsapp_recipient,
                    'type': 'text',
                    'text': {
                        'preview_url': True,
                        'body': message
                    }
                }
            
            response = requests.post(
                self.cloud_api_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Sent via Cloud API (Message ID: {response.json().get('messages', [{}])[0].get('id')})")
                return True
            else:
                logger.error(f"❌ Cloud API send failed: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Cloud API send failed: {e}")
            return False
    
    def send_message(self, message: str, media_url: str = None, retry: int = 0) -> bool:
        """
        Send message via configured API provider with optional media.
        
        Args:
            message: Message to send
            media_url: Optional image URL to send with message
            retry: Current retry attempt
        
        Returns:
            True if successful
        """
        if self.api_provider == 'twilio':
            success = self.send_via_twilio(message, media_url)
        elif self.api_provider == 'cloud':
            success = self.send_via_cloud_api(message, media_url)
        else:
            logger.error(f"Unknown API provider: {self.api_provider}")
            return False
        
        # Retry on failure
        if not success and retry < MAX_RETRIES:
            logger.warning(f"Retrying... (attempt {retry + 1}/{MAX_RETRIES})")
            time.sleep(5)  # Wait 5 seconds before retry
            return self.send_message(message, media_url, retry + 1)
        
        return success
    
    def notify_new_jobs(self, jobs: List[Dict[str, Any]], test_mode: bool = False) -> Dict[str, Any]:
        """
        Send notifications for new jobs.
        
        Args:
            jobs: List of jobs from Google Sheets
            test_mode: If True, don't actually send messages
        
        Returns:
            Summary dictionary
        """
        logger.info("="*70)
        logger.info("WHATSAPP NOTIFICATION BATCH STARTED")
        logger.info(f"Total jobs to process: {len(jobs)}")
        logger.info(f"Test mode: {test_mode}")
        logger.info("="*70)
        
        # Filter by approved companies first
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
        
        # Filter new jobs from approved list
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
        
        # Send notifications
        sent_count = 0
        failed_count = 0
        
        for i, job in enumerate(new_jobs, 1):
            job_title = job.get('Job Title') or job.get('job_title', 'Unknown')
            company = job.get('Company') or job.get('company', 'Unknown')
            
            logger.info(f"[{i}/{len(new_jobs)}] Processing: {job_title} at {company}")
            
            # Format message (returns message text and logo URL)
            message, logo_url = self.format_message(job)
            
            if test_mode:
                logger.info("TEST MODE - Would send:")
                logger.info(message)
                if logo_url:
                    logger.info(f"With company logo: {logo_url}")
                logger.info("-" * 50)
                sent_count += 1
            else:
                # Send message with logo
                success = self.send_message(message, logo_url)
                
                if success:
                    sent_count += 1
                    self._mark_job_sent(job)
                    logger.info(f"✅ Sent: {job_title} at {company}")
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed: {job_title} at {company}")
                
                # Rate limiting
                if i < len(new_jobs):
                    time.sleep(MESSAGE_DELAY_SECONDS)
        
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
        description="WhatsApp Job Notification Automation"
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
        '--api',
        choices=['twilio', 'cloud', 'auto'],
        default='auto',
        help='WhatsApp API provider'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("WHATSAPP JOB NOTIFIER STARTED")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Test mode: {args.test}")
    logger.info(f"Force mode: {args.force}")
    logger.info("="*70)
    
    try:
        # Initialize notifier
        notifier = WhatsAppNotifier(api_provider=args.api)
        
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
