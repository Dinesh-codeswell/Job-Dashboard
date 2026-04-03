"""
Google Sheets integration for LinkedIn Job Scraper.

Handles connecting to Google Sheets and uploading job data.
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleSheetsIntegration:
    """
    Integration class for Google Sheets API.
    
    Handles authentication and data upload to Google Sheets.
    """
    
    def __init__(self, credentials_file: Optional[str] = None, sheet_id: Optional[str] = None):
        """
        Initialize Google Sheets integration.
        
        Args:
            credentials_file: Path to Google service account credentials JSON
            sheet_id: Google Sheet ID (from URL)
        """
        self.credentials_file = credentials_file or os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        self.sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID")
        self.gc = None
        self.spreadsheet = None
        self.worksheet = None
        
        if not self.sheet_id:
            logger.warning("GOOGLE_SHEET_ID not set. Call set_sheet_id() before using.")
    
    def connect(self, worksheet_name: str = "Jobs") -> bool:
        """
        Connect to Google Sheets and open/create worksheet.
        
        Args:
            worksheet_name: Name of the worksheet tab
            
        Returns:
            True if connection successful
        """
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            # Define scopes
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Load credentials
            creds_path = Path(self.credentials_file)
            if not creds_path.exists():
                logger.error(f"Credentials file not found: {self.credentials_file}")
                logger.error("Please follow GOOGLE_SHEETS_SETUP.md to set up Google Sheets API")
                return False
            
            creds = Credentials.from_service_account_file(
                str(creds_path),
                scopes=scopes
            )
            
            # Initialize client
            self.gc = gspread.authorize(creds)
            
            # Open spreadsheet
            if not self.sheet_id:
                logger.error("Sheet ID not set")
                return False
            
            self.spreadsheet = self.gc.open_by_key(self.sheet_id)
            
            # Get or create worksheet
            try:
                self.worksheet = self.spreadsheet.worksheet(worksheet_name)
                logger.info(f"Connected to existing worksheet: {worksheet_name}")
            except gspread.exceptions.WorksheetNotFound:
                self.worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=20
                )
                logger.info(f"Created new worksheet: {worksheet_name}")
                # Setup headers
                self._setup_headers()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            return False
    
    def _setup_headers(self):
        """Setup column headers in the worksheet."""
        headers = [
            "Company",         # Column A
            "Company Logo",    # Column B - NEW: Company Logo URL
            "Job Title",       # Column C
            "Employment Type", # Column D
            "Posted",          # Column E
            "Location",        # Column F
            "Job Description", # Column G
            "Job URL",         # Column H
            "Search City",     # Column I
            "Date Added"       # Column J
        ]
        self.worksheet.append_row(headers, value_input_option="USER_ENTERED")

        # Format header row (bold)
        self.worksheet.format('A1:J1', {'textFormat': {'bold': True}})
    
    def upload_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Upload a single job to Google Sheets.

        Args:
            job_data: Dictionary containing job information

        Returns:
            True if upload successful
        """
        try:
            from datetime import datetime

            # Fix: Use 'job_url' field (works for LinkedIn, Indeed, and Naukri)
            # Fallback to 'linkedin_url' for backward compatibility
            job_url = job_data.get("job_url") or job_data.get("linkedin_url", "")

            row_data = [
                job_data.get("company", ""),           # Column A: Company
                job_data.get("company_logo", ""),      # Column B: Company Logo URL - NEW
                job_data.get("job_title", ""),         # Column C: Job Title
                job_data.get("employment_type", ""),   # Column D: Employment Type
                job_data.get("posted_date", ""),       # Column E: Posted
                job_data.get("location", ""),          # Column F: Location
                self._clean_description(job_data.get("job_description", "")),  # Column G: Description
                job_url,                               # Column H: Job URL (FIXED)
                job_data.get("search_city", ""),       # Column I: Search City
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Column J: Date Added
            ]

            self.worksheet.append_row(row_data, value_input_option="USER_ENTERED")
            logger.info(f"Uploaded job: {job_data.get('job_title')} at {job_data.get('company')}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload job: {e}")
            return False
    
    def upload_jobs(self, jobs_data: List[Dict[str, Any]]) -> int:
        """
        Upload multiple jobs to Google Sheets.
        
        Args:
            jobs_data: List of job data dictionaries
            
        Returns:
            Number of successfully uploaded jobs
        """
        success_count = 0
        for job_data in jobs_data:
            if self.upload_job(job_data):
                success_count += 1
        return success_count
    
    def _clean_description(self, description: str) -> str:
        """
        Clean job description for Google Sheets.
        
        - Removes "… more" and similar LinkedIn artifacts
        - Truncates if too long (Google Sheets has limits)
        - Removes extra newlines
        - Escapes special characters
        """
        if not description:
            return ""
        
        # Remove LinkedIn "Show more" artifacts
        description = description.replace("… more", "")
        description = description.replace("... more", "")
        description = description.replace("Show less", "")
        description = description.replace("Show more", "")
        
        # Remove other common LinkedIn artifacts
        description = description.replace("See less", "")
        description = description.replace("See more", "")
        
        # Replace newlines with spaces for cleaner display
        cleaned = description.replace("\n", " ").replace("\r", "")
        
        # Remove multiple spaces
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")
        
        # Truncate if too long (Google Sheets cell limit is ~50,000 chars)
        max_length = 45000
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length - 100] + "..."
        
        return cleaned.strip()
    
    def get_all_jobs(self) -> List[Dict[str, str]]:
        """
        Get all jobs from the worksheet.
        
        Returns:
            List of job dictionaries
        """
        if not self.worksheet:
            logger.error("Not connected to Google Sheets")
            return []
        
        all_records = self.worksheet.get_all_records()
        return all_records
    
    def check_duplicate(self, job_url: str) -> bool:
        """
        Check if a job URL already exists in the sheet.

        Args:
            job_url: LinkedIn job URL to check

        Returns:
            True if duplicate found
        """
        if not self.worksheet:
            return False

        try:
            all_values = self.worksheet.col_values(8)  # Job URL column (column H = 8, after Company Logo)
            return job_url in all_values
        except Exception:
            return False
