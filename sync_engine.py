"""
STRICT Production Sync Engine: 72-Hour Hard Limit
Enforces 3-day data retention with zero leakage.
FIXED: Proper timestamp calculation using scrape time from Google Sheets
ENHANCED: Pixel-perfect JD formatting with proper spacing and line breaks
"""
import os
import sys
import logging
import math
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
sys.path.insert(0, str(Path(__file__).parent))

from supabase import create_client, Client
from dashboard.data.sheets_fetcher import get_data_fetcher
from dashboard.data.jd_formatter import format_job_description
load_dotenv()

# Configuration
BATCH_SIZE = 100  # Configurable batch size
MAX_JOB_AGE_DAYS = 3  # Jobs older than this are deleted

def parse_linkedin_time(posted_str: str, scrape_timestamp: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse LinkedIn's "X ago" text and calculate actual posting timestamp.
    
    Args:
        posted_str: Text like "1 day ago 185 applicants" or "2 hours ago"
        scrape_timestamp: When the job was scraped (from Google Sheets Timestamp column)
    
    Returns:
        Actual job posting timestamp (timezone aware)
    """
    if not posted_str:
        return None
    
    s = str(posted_str).strip()
    
    # Use scrape_timestamp as reference, or current time as fallback
    reference_time = scrape_timestamp if scrape_timestamp else datetime.now(timezone.utc)
    
    # Ensure reference time is timezone aware
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    
    # Try ISO Format first (YYYY-MM-DD)
    iso_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', s)
    if iso_match:
        try:
            y, m, d = map(int, iso_match.groups())
            return datetime(y, m, d, tzinfo=timezone.utc)
        except:
            pass

    # Parse relative time
    s_lower = s.lower()
    
    # Special case: "just now" or "just posted"
    if "just now" in s_lower or "just posted" in s_lower:
        return reference_time
    
    # Minutes
    if "minute" in s_lower:
        m_match = re.search(r'(\d+)', s_lower)
        if m_match:
            minutes = int(m_match.group(1))
            return reference_time - timedelta(minutes=minutes)
    
    # General pattern: "X hours/days/weeks ago"
    rel_match = re.search(r'(\d+)\s*(h|hr|hour|d|day|w|week|m|month|y|year)', s_lower)
    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2)[0]
        
        if unit == 'h':
            return reference_time - timedelta(hours=val)
        elif unit == 'd':
            return reference_time - timedelta(days=val)
        elif unit == 'w':
            return reference_time - timedelta(weeks=val)
        elif unit == 'm':
            return reference_time - timedelta(days=val * 30)  # Approximate
        elif unit == 'y':
            return reference_time - timedelta(days=val * 365)  # Approximate
    
    # If we can't parse, return None (will be handled by caller)
    return None

def parse_sheets_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse timestamp from Google Sheets.
    Google Sheets stores timestamps in IST (Indian Standard Time, UTC+5:30).
    This function converts IST to UTC.
    
    Args:
        timestamp_str: Timestamp string from Google Sheets (in IST)
    
    Returns:
        Parsed datetime object (timezone aware, in UTC)
    """
    if not timestamp_str:
        return None
    
    try:
        # Define IST timezone (UTC+5:30)
        from datetime import timezone as tz
        IST = tz(timedelta(hours=5, minutes=30))
        
        # Try various formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d',
        ]
        
        for fmt in formats:
            try:
                # Parse the timestamp
                dt = datetime.strptime(str(timestamp_str).strip(), fmt)
                
                # Treat as IST and convert to UTC
                dt_ist = dt.replace(tzinfo=IST)
                dt_utc = dt_ist.astimezone(timezone.utc)
                
                logger.debug(f"Parsed timestamp: {timestamp_str} (IST) -> {dt_utc.isoformat()} (UTC)")
                return dt_utc
            except ValueError:
                continue
        
        # If all formats fail, try ISO format (might already have timezone)
        dt = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
        # If it doesn't have timezone info, assume IST
        if dt.tzinfo is None:
            dt_ist = dt.replace(tzinfo=IST)
            return dt_ist.astimezone(timezone.utc)
        return dt
    
    except Exception as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
        return None

def safe_value(value):
    """Sanitize values to remove NaN/Infinity which break Supabase JSON."""
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        return value
    return value

def is_valid_job(job: Dict[str, Any]) -> bool:
    """
    Validate that a job has all required fields.
    
    Args:
        job: Job dictionary
    
    Returns:
        True if job is valid, False otherwise
    """
    # Check required fields
    title = str(safe_value(job.get("job_title", ""))).strip()
    company = str(safe_value(job.get("company", ""))).strip()
    url = str(safe_value(job.get("job_url", ""))).strip()
    
    # Reject if missing critical fields
    if not title or title.lower() in ["untitled", "unknown", ""]:
        return False
    
    if not company or company.lower() in ["unknown", ""]:
        return False
    
    if not url:
        return False
    
    return True

def sync_data():
    logger.info("--- Starting STRICT 3-Day Sync (FIXED VERSION) ---")
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    if not all([url, key, sheet_id]):
        logger.error("❌ Missing env vars")
        return

    try:
        supabase = create_client(url, key)
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_JOB_AGE_DAYS)

        # 1. CLEANUP: Delete jobs older than 3 days
        logger.info(f"Purging jobs older than {cutoff.isoformat()}...")
        delete_result = supabase.table("jobs").delete().lt("posted_at_timestamp", cutoff.isoformat()).execute()
        logger.info(f"Deleted {len(delete_result.data) if delete_result.data else 0} old jobs")

        # 2. FETCH from Google Sheets
        logger.info("Fetching jobs from Google Sheets...")
        fetcher = get_data_fetcher(sheet_id, "credentials.json")
        all_jobs = fetcher.fetch_all_jobs(use_cache=False)
        
        if not all_jobs:
            logger.warning("No jobs fetched from Google Sheets")
            return
        
        logger.info(f"Fetched {len(all_jobs)} jobs from Google Sheets")

        # 3. TRANSFORM with proper timestamp calculation
        prepared_jobs = []
        skipped_count = 0
        error_count = 0
        
        for i, job in enumerate(all_jobs):
            try:
                # Get scrape timestamp from Google Sheets "Date Added" column
                scrape_timestamp_str = job.get("Date Added") or job.get("date_added") or ""
                scrape_timestamp = parse_sheets_timestamp(scrape_timestamp_str)
                
                # Parse posted date using scrape timestamp as reference
                posted_str = job.get("Posted") or job.get("posted_date") or ""
                posted_at_timestamp = parse_linkedin_time(posted_str, scrape_timestamp)
                
                # Fallback: If parsing failed, use scrape timestamp or current time
                if not posted_at_timestamp:
                    if scrape_timestamp:
                        posted_at_timestamp = scrape_timestamp
                        logger.warning(f"Job {i}: Could not parse '{posted_str}', using Date Added time")
                    else:
                        posted_at_timestamp = datetime.now(timezone.utc)
                        logger.warning(f"Job {i}: No Date Added available, using current time")
                
                # STRICT RULE: Skip if older than 3 days
                if posted_at_timestamp < cutoff:
                    skipped_count += 1
                    continue
                
                # Prepare job data
                job_description_raw = str(safe_value(job.get("Job Description") or job.get("job_description") or ""))
                
                # Format job description for pixel-perfect display
                job_description_formatted = format_job_description(job_description_raw) if job_description_raw else ""
                
                prepared_job = {
                    "external_id": f"job_{safe_value(job.get('id') or i)}",
                    "job_title": str(safe_value(job.get("Job Title") or job.get("job_title") or "")),
                    "company": str(safe_value(job.get("Company") or job.get("company") or "")),
                    "company_logo": str(safe_value(job.get("Company Logo") or job.get("company_logo") or "")),
                    "location": str(safe_value(job.get("Location") or job.get("location") or "")),
                    "search_city": str(safe_value(job.get("Search City") or job.get("search_city") or "")),
                    "employment_type": str(safe_value(job.get("Employment Type") or job.get("employment_type") or "")),
                    "posted_date": str(safe_value(posted_str)),
                    "posted_at_timestamp": posted_at_timestamp.isoformat(),
                    "job_url": str(safe_value(job.get("Job URL") or job.get("job_url") or "")),
                    "job_description": job_description_formatted,  # Use formatted version
                    "source": str(safe_value(job.get("source", "linkedin"))),
                    "metadata": {
                        "sync_date": datetime.now(timezone.utc).isoformat(),
                        "scrape_timestamp": scrape_timestamp.isoformat() if scrape_timestamp else None,
                        "posted_text": posted_str,
                        "jd_formatted": True,  # Flag to indicate formatting was applied
                    }
                }
                
                # Validate job
                if is_valid_job(prepared_job):
                    prepared_jobs.append(prepared_job)
                else:
                    skipped_count += 1
                    logger.debug(f"Skipped invalid job: {prepared_job.get('job_title', 'Unknown')}")
            
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing job {i}: {e}")
                continue
        
        logger.info(f"Processed: {len(prepared_jobs)} valid, {skipped_count} skipped, {error_count} errors")

        # 4. DEDUPLICATE by job_url (keep most recent)
        unique_jobs = {}
        for job in prepared_jobs:
            url = job["job_url"]
            if url not in unique_jobs:
                unique_jobs[url] = job
            else:
                # Keep the one with more recent timestamp (ISO strings are sortable)
                if job["posted_at_timestamp"] > unique_jobs[url]["posted_at_timestamp"]:
                    unique_jobs[url] = job
        
        prepared_jobs = list(unique_jobs.values())
        logger.info(f"After deduplication: {len(prepared_jobs)} unique jobs")

        # 5. UPSERT in batches
        if prepared_jobs:
            logger.info(f"Upserting {len(prepared_jobs)} jobs in batches of {BATCH_SIZE}...")
            success_count = 0
            
            for i in range(0, len(prepared_jobs), BATCH_SIZE):
                batch = prepared_jobs[i:i+BATCH_SIZE]
                try:
                    result = supabase.table("jobs").upsert(batch, on_conflict="job_url").execute()
                    success_count += len(batch)
                    logger.info(f"Upserted batch {i//BATCH_SIZE + 1}: {len(batch)} jobs")
                except Exception as e:
                    logger.error(f"Error upserting batch {i//BATCH_SIZE + 1}: {e}")
            
            logger.info(f"✅ SUCCESS! Upserted {success_count}/{len(prepared_jobs)} jobs")
        else:
            logger.warning("No jobs to upsert")

        logger.info("✅ Sync complete! Database is now strictly limited to 3-day-old data.")

    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    sync_data()
