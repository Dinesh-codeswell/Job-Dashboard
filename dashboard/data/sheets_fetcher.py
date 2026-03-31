"""
Google Sheets Data Fetcher for Consulting Jobs Dashboard

Fetches job data from Google Sheets and provides caching for performance.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class SheetsDataFetcher:
    """
    Fetches and caches data from Google Sheets.
    """
    
    def __init__(self, sheet_id: str, credentials_file: str, worksheet_name: str):
        """
        Initialize the data fetcher.
        
        Args:
            sheet_id: Google Sheet ID
            credentials_file: Path to service account credentials
            worksheet_name: Name of worksheet to fetch from
        """
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file
        self.worksheet_name = worksheet_name
        self.gc = None
        self.worksheet = None
        self._cache = None
        self._cache_time = None
        self._stats_cache = None
        self._stats_cache_time = None
        
    def connect(self) -> bool:
        """
        Connect to Google Sheets.
        
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
            
            creds_path = Path(self.credentials_file)
            if not creds_path.exists():
                logger.error(f"Credentials file not found: {self.credentials_file}")
                return False
            
            creds = Credentials.from_service_account_file(
                str(creds_path),
                scopes=scopes
            )
            
            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open_by_key(self.sheet_id)
            
            try:
                self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.error(f"Worksheet not found: {self.worksheet_name}")
                return False
            
            logger.info(f"Connected to Google Sheets: {self.worksheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False
    
    def fetch_all_jobs(self, use_cache: bool = True, cache_timeout: int = 60) -> List[Dict[str, Any]]:
        """
        Fetch all jobs from Google Sheets.
        
        Args:
            use_cache: Use cached data if available
            cache_timeout: Cache timeout in seconds
            
        Returns:
            List of job dictionaries
        """
        # Check cache
        if use_cache and self._cache and self._cache_time:
            if datetime.now() - self._cache_time < timedelta(seconds=cache_timeout):
                return self._cache
        
        # Fetch from sheets
        try:
            if not self.worksheet:
                if not self.connect():
                    return []
            
            records = self.worksheet.get_all_records()
            
            # Add ID to each job
            for i, job in enumerate(records):
                if 'id' not in job:
                    job['id'] = self._generate_job_id(job, i)
            
            # Sort by date added (newest first)
            records.sort(key=lambda x: x.get('Date Added', ''), reverse=True)
            
            # Update cache
            self._cache = records
            self._cache_time = datetime.now()
            
            logger.info(f"Fetched {len(records)} jobs from Google Sheets")
            return records
            
        except Exception as e:
            logger.error(f"Failed to fetch jobs: {e}")
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
        
        for job in jobs:
            city = job.get('Search City', 'Unknown')
            cities[city] = cities.get(city, 0) + 1
            
            emp_type = job.get('Employment Type', 'Unknown')
            types[emp_type] = types.get(emp_type, 0) + 1
            
            company = job.get('Company', 'Unknown')
            companies[company] = companies.get(company, 0) + 1
        
        stats = {
            'total_jobs': len(jobs),
            'cities': dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)),
            'employment_types': dict(sorted(types.items(), key=lambda x: x[1], reverse=True)),
            'companies': dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:20]),
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
            # Extract job ID from LinkedIn URL
            # https://www.linkedin.com/jobs/view/123456/
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

def get_data_fetcher(sheet_id: str, credentials_file: str, worksheet_name: str) -> SheetsDataFetcher:
    """
    Get or create the data fetcher singleton.
    
    Args:
        sheet_id: Google Sheet ID
        credentials_file: Path to credentials
        worksheet_name: Worksheet name
        
    Returns:
        SheetsDataFetcher instance
    """
    global _fetcher_instance
    
    if _fetcher_instance is None:
        _fetcher_instance = SheetsDataFetcher(sheet_id, credentials_file, worksheet_name)
        _fetcher_instance.connect()
    
    return _fetcher_instance
