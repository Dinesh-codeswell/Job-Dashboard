"""
Notion integration for LinkedIn job scraper.

Stores scraped jobs directly into a Notion database.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import json

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


class NotionIntegration:
    """
    Integration with Notion API for storing job listings.
    
    Example:
        notion = NotionIntegration(api_key="your_key", database_id="your_db_id")
        notion.add_job({
            "company": "Google",
            "role": "Software Engineer",
            "date_added": "2024-01-15",
            "location": "Bangalore",
            "url": "https://linkedin.com/jobs/view/123"
        })
    """

    def __init__(self, api_key: str, database_id: str):
        """
        Initialize Notion client.

        Args:
            api_key: Notion integration API key
            database_id: ID of the target Notion database
        """
        self.client = Client(auth=api_key)
        self.database_id = database_id
        self._connected = False
        self._cache_file = "notion_added_jobs_cache.json"
        self._added_urls = self._load_cache()

    def _load_cache(self) -> set:
        """Load cached URLs from file."""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    data = json.load(f)
                    return set(data)
        except Exception as e:
            logger.debug(f"Could not load cache: {e}")
        return set()

    def _save_cache(self):
        """Save cached URLs to file."""
        try:
            with open(self._cache_file, 'w') as f:
                json.dump(list(self._added_urls), f)
        except Exception as e:
            logger.debug(f"Could not save cache: {e}")

    def connect(self) -> bool:
        """
        Test connection to Notion database.

        Returns:
            True if connection successful
        """
        try:
            # Verify database access
            db = self.client.databases.retrieve(self.database_id)
            self._connected = True
            logger.info(f"Connected to Notion database: {db.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            return True
        except APIResponseError as e:
            logger.error(f"Notion API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Notion: {e}")
            return False

    def check_duplicate(self, job_url: str) -> bool:
        """
        Check if a job URL already exists in the database.

        Uses a local cache file for fast duplicate detection.
        This avoids API rate limits and works reliably.

        Args:
            job_url: LinkedIn job URL to check

        Returns:
            True if duplicate exists, False otherwise
        """
        # Check local cache first (fastest)
        if job_url in self._added_urls:
            logger.debug(f"Duplicate found in cache: {job_url}")
            return True
        
        # Also try to check Notion (but don't fail if it doesn't work)
        try:
            # Use search to find if URL exists in Notion
            response = self.client.search(
                query=job_url.split('/')[-1],  # Search by job ID
                filter={"property": "object", "value": "page"}
            )
            
            for result in response.get("results", []):
                properties = result.get("properties", {})
                app_link = properties.get("Application Link", {})
                if app_link.get("url") == job_url:
                    # Add to cache
                    self._added_urls.add(job_url)
                    self._save_cache()
                    return True
        except Exception as e:
            # Search might not work, but we can still use cache
            logger.debug(f"Search check skipped: {e}")
        
        return False

    def add_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Add a job to the Notion database.

        Args:
            job_data: Dictionary with keys: company, role, date_added, location, url

        Returns:
            True if successfully added
        """
        try:
            # Prepare properties for Notion
            # Column mapping based on user's database:
            # - Company (Title) - First column in Notion database must be Title
            # - Position (Rich text)
            # - Date Posted (Date) - format: Year/Month/Day
            # - Location (Rich text)
            # - Application Link (URL)
            properties = {
                "Company": {
                    "title": [
                        {
                            "text": {
                                "content": job_data.get("company", "Unknown")
                            }
                        }
                    ]
                },
                "Position": {
                    "rich_text": [
                        {
                            "text": {
                                "content": job_data.get("role", "Unknown")
                            }
                        }
                    ]
                },
                "Date Posted": {
                    "date": {
                        "start": job_data.get("date_added", datetime.now().strftime("%Y-%m-%d"))
                    }
                },
                "Location": {
                    "rich_text": [
                        {
                            "text": {
                                "content": job_data.get("location", "Unknown")
                            }
                        }
                    ]
                },
                "Application Link": {
                    "url": job_data.get("url", "")
                }
            }

            # Create page in database
            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )

            # Add to cache
            self._added_urls.add(job_data.get("url", ""))
            self._save_cache()

            logger.info(f"Added job: {job_data.get('role')} at {job_data.get('company')}")
            return True

        except APIResponseError as e:
            logger.error(f"Notion API error adding job: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding job to Notion: {e}")
            return False

    def add_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Add multiple jobs to the Notion database.

        Args:
            jobs_data: List of job data dictionaries

        Returns:
            Dictionary with counts: added, skipped, failed
        """
        results = {"added": 0, "skipped": 0, "failed": 0}

        for job_data in jobs_data:
            # Check for duplicates
            if self.check_duplicate(job_data.get("url", "")):
                results["skipped"] += 1
                logger.debug(f"Skipping duplicate: {job_data.get('url')}")
                continue

            if self.add_job(job_data):
                results["added"] += 1
            else:
                results["failed"] += 1

        return results

    def get_database_properties(self) -> Dict[str, Any]:
        """
        Get database schema/properties.

        Returns:
            Dictionary of database properties
        """
        try:
            db = self.client.databases.retrieve(self.database_id)
            return db.get("properties", {})
        except Exception as e:
            logger.error(f"Error getting database properties: {e}")
            return {}
