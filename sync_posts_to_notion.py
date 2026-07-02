#!/usr/bin/env python3
"""
SYNC POSTS TO NOTION
====================
Reads extracted LinkedIn post data from a Google Sheet and syncs it
to a Notion database.

This is the SECOND step in the two-step workflow:
  1. python process_manual_posts.py   ← Extract post data → fills Company, Role, Location in sheet
  2. python sync_posts_to_notion.py   ← Sync to Notion    → reads sheet, pushes to Notion

FLOW:
    1. Reads rows from Google Sheet where Company, Role, Location are filled
    2. Checks a "Notion Sync Status" column - only processes rows NOT yet synced
    3. For each row:
       a. Syncs to Notion via NotionIntegration
       b. Updates "Notion Sync Status" column with result
    4. Prints a summary

USAGE:
    python sync_posts_to_notion.py
    python sync_posts_to_notion.py --worksheet Sheet1
    python sync_posts_to_notion.py --verbose
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv

# Fix Windows console encoding for emoji/unicode support
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration
from linkedin_scraper.integrations.notion import NotionIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

# Google Sheet ID (same as process_manual_posts.py)
SHEET_ID = "1RyjewL5F1PR4PWn6fRSBkNeC0WXhTqQD-YPa2IUVDIU"

# Sheet column names
SHEET_URL_COLUMN = "Linkedin Post URL"     # Column with the original URL
SHEET_COMPANY_COLUMN = "Company"            # Extracted company name
SHEET_ROLE_COLUMN = "Role"                  # Extracted role
SHEET_LOCATION_COLUMN = "Location"          # Extracted location

# Notion column this script adds
NOTION_STATUS_COLUMN = "Notion Sync Status"

# Notion config (from .env)
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID")


# ============================================================================
# NOTION SYNCER
# ============================================================================

class NotionSyncer:
    """
    Reads extracted job data from Google Sheet and syncs to Notion.
    Handles duplicate detection and status tracking.
    """

    def __init__(
        self,
        credentials_file: str = "credentials.json",
        sheet_id: str = SHEET_ID,
        worksheet_name: str = "Sheet1"
    ):
        """
        Initialize the syncer.

        Args:
            credentials_file: Path to Google service account credentials JSON
            sheet_id: Google Sheet ID
            worksheet_name: Name of worksheet tab
        """
        self.sheet_id = sheet_id
        self.sheets = GoogleSheetsIntegration(
            credentials_file=credentials_file,
            sheet_id=sheet_id
        )
        self.worksheet_name = worksheet_name

        # Initialize Notion
        self.notion = NotionIntegration(
            api_key=NOTION_API_KEY,
            database_id=NOTION_DB_ID
        ) if NOTION_API_KEY and NOTION_DB_ID else None

        # Statistics
        self.stats = {
            "total_ready": 0,
            "already_synced": 0,
            "synced": 0,
            "failed": 0,
            "errors": []
        }

    def ensure_status_column(self) -> bool:
        """
        Ensure the Notion Sync Status column exists in the sheet.
        """
        col_map = self.sheets.ensure_columns([NOTION_STATUS_COLUMN])
        return NOTION_STATUS_COLUMN in col_map

    def fetch_ready_records(self) -> List[Dict[str, Any]]:
        """
        Fetch rows that have Company, Role, Location filled but
        have not yet been synced to Notion.

        Returns:
            List of dicts with row data + '_row' key
        """
        if not self.sheets.worksheet:
            logger.error("Not connected to Google Sheets")
            return []

        try:
            records = self.sheets.get_records_with_rows()
        except Exception as e:
            logger.error(f"Failed to fetch records: {e}")
            return []

        ready = []
        for record in records:
            url = record.get(SHEET_URL_COLUMN, "").strip()
            company = record.get(SHEET_COMPANY_COLUMN, "").strip()
            role = record.get(SHEET_ROLE_COLUMN, "").strip()
            location = record.get(SHEET_LOCATION_COLUMN, "").strip()
            notion_status = record.get(NOTION_STATUS_COLUMN, "").strip()
            row = record.get("_row", 0)

            # Must have a URL, company, and role (extracted data)
            if not url or not company or not role:
                continue

            # Skip if already synced
            if notion_status:
                self.stats["already_synced"] += 1
                continue

            ready.append({
                "row": row,
                "url": url,
                "company": company,
                "role": role,
                "location": location
            })

        self.stats["total_ready"] = len(ready)
        return ready

    async def run(self) -> Dict[str, Any]:
        """
        Run the sync workflow.
        """
        print("\n" + "=" * 70)
        print("SYNC POSTS TO NOTION")
        print("=" * 70)
        print(f"Google Sheet: {self.sheet_id}")
        print(f"Notion DB ID: {NOTION_DB_ID or 'Not set'}")
        print("=" * 70 + "\n")

        # Step 1: Connect to Google Sheets
        print("Connecting to Google Sheets...")
        if not self.sheets.connect(worksheet_name=self.worksheet_name):
            logger.error("Failed to connect to Google Sheets")
            return {"success": False, "error": "Google Sheets connection failed"}
        print("Connected\n")

        # Step 2: Ensure status column exists
        print("Ensuring Notion Sync Status column...")
        self.ensure_status_column()
        print("Ready\n")

        # Step 3: Connect to Notion
        if not self.notion:
            logger.error("Notion not configured. Set NOTION_API_KEY and NOTION_DATABASE_ID in .env")
            return {"success": False, "error": "Notion not configured"}

        print("Connecting to Notion...")
        if not self.notion.connect():
            logger.error("Failed to connect to Notion")
            return {"success": False, "error": "Notion connection failed"}
        print("Connected\n")

        # Step 4: Fetch records ready for sync
        print("Fetching records ready for sync...")
        records = self.fetch_ready_records()
        print(f"Found {self.stats['total_ready']} ready, {self.stats['already_synced']} already synced\n")

        if not records:
            print("Nothing to sync!")
            self.print_summary()
            return {"success": True, "stats": self.stats}

        # Step 5: Sync each record
        print(f"Syncing {len(records)} records to Notion...\n")

        for i, record in enumerate(records, 1):
            row = record["row"]
            url = record["url"]
            company = record["company"]
            role = record["role"]
            location = record["location"]

            print(f"[{i}/{len(records)}] {company} | {role}")

            # Check Notion duplicate
            if self.notion.check_duplicate(url):
                print(f"  Already in Notion, updating sheet status")
                self._update_sheet_status(row, "Already in Notion")
                self.stats["already_synced"] += 1
                continue

            # Sync to Notion
            job_data = {
                "company": company,
                "role": role,
                "date_added": datetime.now().strftime("%Y-%m-%d"),
                "location": location,
                "url": url
            }

            if self.notion.add_job(job_data):
                print(f"  Synced to Notion")
                self._update_sheet_status(row, "Synced to Notion")
                self.stats["synced"] += 1
            else:
                print(f"  Failed to sync")
                self._update_sheet_status(row, "Sync failed")
                self.stats["failed"] += 1
                self.stats["errors"].append(f"Failed to sync {company} - {role}")

        # Summary
        self.print_summary()
        return {
            "success": self.stats["synced"] > 0,
            "stats": self.stats
        }

    def _update_sheet_status(self, row: int, status: str):
        """Update Notion Sync Status column for a given row."""
        try:
            self.sheets.update_row_cells(row, {
                NOTION_STATUS_COLUMN: status
            })
        except Exception as e:
            logger.warning(f"Failed to update status for row {row}: {e}")

    def print_summary(self):
        """Print a summary of the sync run."""
        print("\n" + "=" * 70)
        print("SYNC SUMMARY")
        print("=" * 70)
        print(f"Ready to sync:  {self.stats['total_ready']}")
        print(f"Already synced: {self.stats['already_synced']}")
        print(f"Synced now:     {self.stats['synced']}")
        print(f"Failed:         {self.stats['failed']}")

        if self.stats["errors"]:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:10]:
                print(f"  - {error[:120]}")
            if len(self.stats["errors"]) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")

        print("=" * 70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync extracted LinkedIn post data from Google Sheet to Notion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sync_posts_to_notion.py              # Sync all ready records
  python sync_posts_to_notion.py --verbose     # Detailed logging

WORKFLOW:
  1. First run: python process_manual_posts.py  (extract data to sheet)
  2. Then run:  python sync_posts_to_notion.py  (push to Notion)
        """
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    syncer = NotionSyncer()
    results = await syncer.run()

    sys.exit(0 if results.get("success") else 1)


if __name__ == "__main__":
    asyncio.run(main())
