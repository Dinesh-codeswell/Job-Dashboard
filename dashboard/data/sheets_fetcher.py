"""
Google Sheets Data Fetcher for Consulting Jobs Dashboard

Fetches job data from Google Sheets and provides caching for performance.
Supports multiple worksheets (LinkedIn, Indeed, Naukri) for unified dashboard.
"""
import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SheetsDataFetcher:
    """
    Fetches and caches data from Google Sheets.
    Supports multiple worksheets for unified job dashboard.
    """

    def __init__(self, sheet_id: str, credentials_file: str, worksheet_name: str = None):
        """
        Initialize the data fetcher.

        Args:
            sheet_id: Google Sheet ID
            credentials_file: Path to service account credentials
            worksheet_name: Name of primary worksheet (deprecated - now fetches from all sheets)
        """
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file
        self.worksheet_name = worksheet_name or 'LinkedIn_Jobs'
        self.gc = None
        self.worksheet = None
        self._cache = None
        self._cache_time = None
        self._stats_cache = None
        self._stats_cache_time = None

        # All worksheets to fetch from (unified dashboard)
        self.all_worksheets = [
            'LinkedIn_Jobs',
            'Indeed_Jobs',
            'Naukri_Jobs'
        ]

        # Fallback: if specific worksheets don't exist, try these common names
        self.fallback_worksheets = [
            'Consulting_Jobs_India',
            'Jobs',
            'Consulting Jobs India'
        ]

    def connect(self) -> bool:
        """
        Connect to Google Sheets.
        Supports both file-based credentials (local) and JSON env var (Vercel).

        Returns:
            True if connection successful
        """
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]

            # Try environment variable first (for Vercel/cloud deployment)
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON') or os.getenv('GOOGLE_CREDENTIALS')
            
            if creds_json:
                logger.info("Using credentials from environment variable")
                try:
                    creds_info = json.loads(creds_json)
                    creds = Credentials.from_service_account_info(
                        creds_info,
                        scopes=scopes
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
                    return False
                except Exception as e:
                    logger.error(f"Failed to load credentials from env var: {e}")
                    return False
            else:
                # Fallback to file-based credentials (for local development)
                creds_path = Path(self.credentials_file)
                if not creds_path.exists():
                    logger.error(f"Credentials file not found: {self.credentials_file}")
                    logger.error("Set GOOGLE_CREDENTIALS_JSON env var with your service account JSON for cloud deployment")
                    return False

                logger.info(f"Using credentials from file: {creds_path}")
                creds = Credentials.from_service_account_file(
                    str(creds_path),
                    scopes=scopes
                )

            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open_by_key(self.sheet_id)

            # Try to connect to primary worksheet, but don't fail if it doesn't exist
            try:
                self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
                logger.info(f"Connected to Google Sheets: {self.worksheet_name}")
            except gspread.exceptions.WorksheetNotFound:
                logger.warning(f"Primary worksheet '{self.worksheet_name}' not found, will fetch from all available worksheets")
                self.worksheet = None

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def fetch_all_jobs(self, use_cache: bool = True, cache_timeout: int = 60) -> List[Dict[str, Any]]:
        """
        Fetch all jobs from all worksheets (LinkedIn, Indeed, Naukri).

        Args:
            use_cache: Use cached data if available
            cache_timeout: Cache timeout in seconds

        Returns:
            List of job dictionaries (unified from all sources)
        """
        # Check cache
        if use_cache and self._cache and self._cache_time:
            if datetime.now() - self._cache_time < timedelta(seconds=cache_timeout):
                logger.info(f"Returning cached jobs ({len(self._cache)} jobs)")
                return self._cache

        # Fetch from all sheets
        try:
            if not self.spreadsheet:
                logger.info("Connecting to Google Sheets...")
                if not self.connect():
                    logger.error("Failed to connect to Google Sheets")
                    return []
                else:
                    logger.info("✅ Connected to Google Sheets successfully")

            all_jobs = []
            
            # Try primary worksheets first
            worksheets_to_try = self.all_worksheets.copy()
            
            # If no jobs found, try fallback worksheets
            worksheets_to_try.extend(self.fallback_worksheets)
            
            # If still no jobs, try ALL worksheets in the spreadsheet
            try:
                all_sheets = self.spreadsheet.worksheets()
                all_sheet_names = [ws.title for ws in all_sheets]
                logger.info(f"📊 Available worksheets: {all_sheet_names}")
                
                # Add any worksheets not already in the list
                for sheet_name in all_sheet_names:
                    if sheet_name not in worksheets_to_try:
                        worksheets_to_try.append(sheet_name)
            except Exception as e:
                logger.warning(f"Could not list worksheets: {e}")
            
            # Try each worksheet
            for ws_name in worksheets_to_try:
                try:
                    logger.info(f"📊 Trying to fetch from worksheet: {ws_name}")
                    worksheet = self.spreadsheet.worksheet(ws_name)
                    records = worksheet.get_all_records()
                    
                    if not records:
                        logger.info(f"⚠️ No jobs found in {ws_name}")
                        continue
                    
                    logger.info(f"✅ Found {len(records)} jobs in {ws_name}")
                    
                    # Add ID and source to each job
                    for i, job in enumerate(records):
                        if 'id' not in job or not job['id']:
                            job['id'] = self._generate_job_id(job, i)
                        
                        # Add source platform for unified display
                        if 'source' not in job:
                            job['source'] = ws_name.replace('_Jobs', '').lower()
                        
                        all_jobs.append(job)
                    
                    logger.info(f"✅ Successfully fetched {len(records)} jobs from {ws_name}")
                except Exception as e:
                    logger.debug(f"⚠️ Could not fetch from {ws_name}: {e}")
                    continue

            # Sort by date added (newest first)
            all_jobs.sort(key=lambda x: x.get('Date Added', ''), reverse=True)

            # Update cache
            self._cache = all_jobs
            self._cache_time = datetime.now()

            logger.info(f"✅ Total fetched {len(all_jobs)} jobs from all sources")
            
            if len(all_jobs) == 0:
                logger.warning("⚠️ No jobs found in any worksheet")
            
            return all_jobs

        except Exception as e:
            logger.error(f"❌ Failed to fetch jobs: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._cache or []
    
    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job dictionary or None
        """
        jobs = self.fetch_all_jobs()
        for job in jobs:
            if job.get('id') == job_id:
                return job
        return None

    def get_stats(self, use_cache: bool = True, cache_timeout: int = 120) -> Dict[str, Any]:
        """
        Get dashboard statistics.

        Args:
            use_cache: Use cached data
            cache_timeout: Cache timeout in seconds

        Returns:
            Statistics dictionary
        """
        # Check cache
        if use_cache and self._stats_cache and self._stats_cache_time:
            if datetime.now() - self._stats_cache_time < timedelta(seconds=cache_timeout):
                return self._stats_cache

        jobs = self.fetch_all_jobs()

        # Calculate stats
        cities = {}
        types = {}
        companies = {}
        sources = {}

        for job in jobs:
            city = job.get('Search City', 'Unknown')
            cities[city] = cities.get(city, 0) + 1

            emp_type = job.get('Employment Type', 'Unknown')
            types[emp_type] = types.get(emp_type, 0) + 1

            company = job.get('Company', 'Unknown')
            companies[company] = companies.get(company, 0) + 1
            
            source = job.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

        stats = {
            'total_jobs': len(jobs),
            'cities': dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)),
            'employment_types': dict(sorted(types.items(), key=lambda x: x[1], reverse=True)),
            'companies': dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:20]),
            'sources': dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)),
            'last_updated': self._cache_time.isoformat() if self._cache_time else None,
            'worksheet': self.worksheet_name
        }

        self._stats_cache = stats
        self._stats_cache_time = datetime.now()

        return stats

    def get_unique_cities(self) -> List[str]:
        """Get list of unique cities."""
        stats = self.get_stats()
        return list(stats['cities'].keys())

    def get_unique_employment_types(self) -> List[str]:
        """Get list of unique employment types."""
        stats = self.get_stats()
        return list(stats['employment_types'].keys())

    def search_jobs(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        employment_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search jobs with filters.

        Args:
            query: Search query (matches title, company, description)
            city: Filter by city
            employment_type: Filter by employment type
            limit: Maximum results

        Returns:
            Filtered list of jobs
        """
        jobs = self.fetch_all_jobs()
        results = []

        for job in jobs:
            # Apply filters
            if city and job.get('Search City') != city:
                continue

            if employment_type and employment_type.lower() not in job.get('Employment Type', '').lower():
                continue

            if query:
                query_lower = query.lower()
                searchable = f"{job.get('Job Title', '')} {job.get('Company', '')} {job.get('Job Description', '')}".lower()
                if query_lower not in searchable:
                    continue

            results.append(job)

            if len(results) >= limit:
                break

        return results

    def _generate_job_id(self, job: Dict[str, Any], index: int) -> str:
        """
        Generate a unique ID for a job.

        Args:
            job: Job dictionary
            index: Index in the list

        Returns:
            Unique job ID
        """
        # Use URL as base for ID if available
        url = job.get('Job URL', '')
        if url:
            # Extract job ID from URL
            parts = url.rstrip('/').split('/')
            if parts:
                return f"job_{parts[-1]}"

        # Fallback: generate from title + company + index
        title = job.get('Job Title', '')[:20].replace(' ', '_').lower()
        company = job.get('Company', '')[:20].replace(' ', '_').lower()
        return f"job_{title}_{company}_{index}"

    def clear_cache(self):
        """Clear all caches."""
        self._cache = None
        self._cache_time = None
        self._stats_cache = None
        self._stats_cache_time = None
        logger.info("Cache cleared")


# Singleton instance
_fetcher_instance = None

def get_data_fetcher(sheet_id: str, credentials_file: str, worksheet_name: str = None) -> SheetsDataFetcher:
    """
    Get or create the data fetcher singleton.

    Args:
        sheet_id: Google Sheet ID
        credentials_file: Path to credentials
        worksheet_name: Worksheet name (deprecated)

    Returns:
        SheetsDataFetcher instance
    """
    global _fetcher_instance

    if _fetcher_instance is None:
        _fetcher_instance = SheetsDataFetcher(sheet_id, credentials_file, worksheet_name)
        _fetcher_instance.connect()

    return _fetcher_instance
