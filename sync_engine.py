"""
STRICT Production Sync Engine: 72-Hour Hard Limit
Enforces 3-day data retention with zero leakage.
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
load_dotenv()

def parse_linkedin_time(posted_str: str) -> Optional[datetime]:
    if not posted_str: return None
    s = str(posted_str).strip()
    now = datetime.now(timezone.utc)
    
    # ISO Format
    iso_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', s)
    if iso_match:
        try:
            y, m, d = map(int, iso_match.groups())
            return datetime(y, m, d, tzinfo=timezone.utc)
        except: pass

    # Relative
    s_lower = s.lower()
    if "minute" in s_lower:
        m_match = re.search(r'(\d+)', s_lower)
        if m_match: return now - timedelta(minutes=int(m_match.group(1)))
    
    rel_match = re.search(r'(\d+)\s*(h|hr|hour|d|day|w|week|m|month|y|year)', s_lower)
    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2)[0]
        if unit == 'h': return now - timedelta(hours=val)
        if unit == 'd': return now - timedelta(days=val)
        if unit == 'w': return now - timedelta(weeks=val)
        if unit in ['m', 'y']: return now - timedelta(days=val * 30 if unit == 'm' else val * 365)
    
    if "just now" in s_lower: return now
    return None

def sync_data():
    logger.info("--- Starting STRICT 3-Day Sync ---")
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    
    if not all([url, key, sheet_id]):
        logger.error("❌ Missing env vars")
        return

    try:
        supabase = create_client(url, key)
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        
        # 1. CLEANUP: Delete jobs older than 3 days OR with NULL timestamps
        logger.info(f"Purging jobs older than {cutoff.isoformat()} and NULLs...")
        supabase.table("jobs").delete().lt("posted_at_timestamp", cutoff.isoformat()).execute()
        supabase.table("jobs").delete().is_("posted_at_timestamp", "null").execute()

        # 2. FETCH
        fetcher = get_data_fetcher(sheet_id, "credentials.json")
        all_jobs = fetcher.fetch_all_jobs(use_cache=False)
        if not all_jobs: return

        # 3. STRICT TRANSFORM
        prepared_jobs = []
        for i, job in enumerate(all_jobs):
            ts = parse_linkedin_time(job.get("Posted") or job.get("posted_date") or "")
            
            # STRICT RULE: Skip if no date OR if older than 3 days
            if not ts or ts < cutoff:
                continue

            prepared_job = {
                "external_id": str(job.get("id") or i),
                "job_title": job.get("Job Title") or job.get("job_title") or "Untitled",
                "company": job.get("Company") or job.get("company") or "Unknown",
                "company_logo": job.get("Company Logo") or job.get("company_logo") or "",
                "location": job.get("Location") or job.get("location") or "",
                "search_city": job.get("Search City") or job.get("search_city") or "",
                "employment_type": job.get("Employment Type") or job.get("employment_type") or "",
                "posted_date": str(job.get("Posted") or job.get("posted_date") or ""),
                "posted_at_timestamp": ts.isoformat(),
                "job_url": job.get("Job URL") or job.get("job_url"),
                "job_description": job.get("Job Description") or job.get("job_description") or "",
                "source": job.get("source", "unknown"),
                "metadata": {"sync_date": datetime.now(timezone.utc).isoformat()}
            }
            if prepared_job["job_url"]: prepared_jobs.append(prepared_job)

        # 4. UPSERT
        logger.info(f"Upserting {len(prepared_jobs)} STRICTLY FRESH jobs...")
        for i in range(0, len(prepared_jobs), 50):
            supabase.table("jobs").upsert(prepared_jobs[i:i+50], on_conflict="job_url").execute()
            
        logger.info("✅ SUCCESS! Database is now strictly limited to 3-day-old data.")

    except Exception as e:
        logger.error(f"❌ ERROR: {e}")

if __name__ == "__main__":
    sync_data()
