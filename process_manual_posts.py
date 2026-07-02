#!/usr/bin/env python3
"""
PROCESS MANUAL POST URLs
========================
Reads LinkedIn Post/Job URLs from a Google Sheet, extracts structured data
(Company Name, Role, Location), and writes results back to the sheet.

FLOW:
    1. Reads "Linkedin Post URL" column from Google Sheet (with row numbers)
    2. Ensures output columns exist: Company, Role, Location, Status, Processed Date
    3. For each new URL (not previously processed):
       a. Opens LinkedIn in authenticated browser session
       b. Extracts Company, Role, Location using post_parser (supports both
          linkedin.com/posts/... and linkedin.com/jobs/view/... URLs)
       c. Writes extracted data + status back to the Google Sheet row
    4. Tracks processed URLs in a local cache (processed_posts_cache.json)
    5. Prints a summary of results

Once extracted, run 'python sync_posts_to_notion.py' to push results to Notion.

CREDENTIALS SETUP:
    - Google Service Account: linkedin-scraper-755@linkedin-job-scraper-491917.iam.gserviceaccount.com
    - Google Sheet: https://docs.google.com/spreadsheets/d/1RyjewL5F1PR4PWn6fRSBkNeC0WXhTqQD-YPa2IUVDIU/edit
      (Must share the sheet with the service account email)
    - LinkedIn Session: linkedin_session.json (run samples/create_session.py first)

USAGE:
    python process_manual_posts.py
    python process_manual_posts.py --headless False  # See browser
    python process_manual_posts.py --limit 10         # Process only 10 URLs
    python process_manual_posts.py --reset-cache      # Reprocess all URLs
"""

import asyncio
import logging
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

from dotenv import load_dotenv

# Fix Windows console encoding for emoji/unicode support
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from linkedin_scraper import BrowserManager
from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration
from linkedin_scraper.integrations.post_parser import extract_structured_post_data

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

# Your Google Sheet ID (from the URL you shared)
SHEET_ID = "1RyjewL5F1PR4PWn6fRSBkNeC0WXhTqQD-YPa2IUVDIU"

# Column header name in your Google Sheet
SHEET_URL_COLUMN = "Linkedin Post URL"

# Worksheet name (default is first worksheet)
WORKSHEET_NAME = "Sheet1"

# Cache file to track already-processed URLs
PROCESSED_CACHE_FILE = "processed_posts_cache.json"



# ============================================================================
# POST URL PROCESSOR
# ============================================================================

class PostURLProcessor:
    """
    Processes LinkedIn Post/Job URLs from Google Sheet and writes extracted
    data back to the sheet.

    Features:
    - Reads URLs from a single-column Google Sheet
    - Tracks processed URLs in a local cache (skip duplicates)
    - Supports both linkedin.com/posts/... and linkedin.com/jobs/view/... URLs
    - Writes extracted data (Company, Role, Location) back to the sheet
    - Progress tracking with detailed summary

    Once extraction is done, use sync_posts_to_notion.py to push to Notion.
    """

    def __init__(
        self,
        credentials_file: str = "credentials.json",
        session_file: str = "linkedin_session.json",
        headless: bool = True,
        sheet_id: str = SHEET_ID,
        worksheet_name: str = WORKSHEET_NAME,
        url_column: str = SHEET_URL_COLUMN
    ):
        """
        Initialize the processor.

        Args:
            credentials_file: Path to Google service account credentials JSON
            session_file: Path to LinkedIn session file
            headless: Run browser in headless mode
            sheet_id: Google Sheet ID
            worksheet_name: Name of worksheet tab
            url_column: Column header containing LinkedIn URLs
        """
        self.credentials_file = credentials_file
        self.session_file = session_file
        self.headless = headless
        self.sheet_id = sheet_id
        self.worksheet_name = worksheet_name
        self.url_column = url_column

        # Initialize Google Sheets integration
        self.sheets = GoogleSheetsIntegration(
            credentials_file=credentials_file,
            sheet_id=sheet_id
        )

        # Load processed URLs cache
        self.processed_urls: Set[str] = set()
        self._load_cache()
        # reset_cache is handled in run() to avoid double logic

        # Statistics
        self.stats = {
            "total_in_sheet": 0,
            "already_processed": 0,
            "new_urls": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }

    def _load_cache(self):
        """Load processed URLs from cache file."""
        try:
            if os.path.exists(PROCESSED_CACHE_FILE):
                with open(PROCESSED_CACHE_FILE, "r") as f:
                    data = json.load(f)
                    self.processed_urls = set(data)
                logger.info(f"Loaded {len(self.processed_urls)} processed URLs from cache")
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
            self.processed_urls = set()

    def _save_cache(self):
        """Save processed URLs to cache file."""
        try:
            with open(PROCESSED_CACHE_FILE, "w") as f:
                json.dump(list(self.processed_urls), f, indent=2)
            logger.debug(f"Saved {len(self.processed_urls)} URLs to cache")
        except Exception as e:
            logger.warning(f"Could not save cache: {e}")

    OUTPUT_COLUMNS = ["Company", "Role", "Location", "Status", "Processed Date"]

    def fetch_records_from_sheet(self) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the Google Sheet INCLUDING row numbers.
        Each record has an extra '_row' key with the 1-based sheet row number.

        Returns:
            List of dicts, each with row data + '_row' for the sheet row number
        """
        if not self.sheets.worksheet:
            logger.error("Not connected to Google Sheets")
            return []

        try:
            records = self.sheets.get_records_with_rows()
            logger.info(f"Fetched {len(records)} rows from Google Sheet")
            return records
        except Exception as e:
            logger.error(f"Failed to fetch data from sheet: {e}")
            return []

    def extract_urls_from_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract valid LinkedIn URLs from sheet records, preserving row numbers.

        Args:
            records: List of row dictionaries (with '_row' key) from Google Sheet

        Returns:
            List of dicts with 'url' and 'row' keys for each valid URL
        """
        entries = []
        for record in records:
            url = record.get(self.url_column, "").strip()
            row = record.get("_row", 0)
            if url and ("linkedin.com/posts/" in url or "linkedin.com/jobs/" in url or "linkedin.com/feed/" in url):
                # Strip all query params for cleaner tracking
                clean_url = url.split("?")[0]
                entries.append({"url": clean_url, "row": row})
            elif url:
                logger.debug(f"Skipping non-LinkedIn URL: {url}")

        # Remove duplicates by URL, keeping the first occurrence
        seen = set()
        unique_entries = []
        for entry in entries:
            if entry["url"] not in seen:
                seen.add(entry["url"])
                unique_entries.append(entry)

        return unique_entries

    def ensure_output_columns(self) -> Dict[str, int]:
        """
        Ensure the output columns (Company, Role, Location, Status, Processed Date)
        exist in the sheet. Adds any missing columns to the right.

        Returns:
            Dict mapping column name to 1-based column index
        """
        return self.sheets.ensure_columns(self.OUTPUT_COLUMNS)

    def write_result_to_sheet(self, row: int, company: str, role: str, location: str, status: str):
        """
        Write extracted data and status back to the Google Sheet row.

        Args:
            row: 1-based row number in the sheet
            company: Extracted company name
            role: Extracted role
            location: Extracted location
            status: Status message (e.g., "✅ Extracted" or "❌ Failed")
        """
        try:
            self.sheets.update_row_cells(row, {
                "Company": company,
                "Role": role,
                "Location": location,
                "Status": status,
                "Processed Date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            logger.debug(f"  ✓ Written to sheet row {row}")
        except Exception as e:
            logger.warning(f"  ⚠️  Failed to write to sheet row {row}: {e}")

    async def process_urls(
        self,
        browser: BrowserManager,
        entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process a list of LinkedIn URLs and write results back to the sheet.

        Args:
            browser: BrowserManager instance (must have authenticated session loaded)
            entries: List of dicts with 'url' and 'row' keys

        Returns:
            List of results for successfully processed URLs
        """
        results = []

        for i, entry in enumerate(entries, 1):
            url = entry["url"]
            row = entry.get("row", 0)

            # Check if already processed in a prior run
            if url in self.processed_urls:
                self.stats["already_processed"] += 1
                logger.info(f"[{i}/{len(entries)}] ⏭️  Already processed: {url[:80]}...")
                continue

            self.stats["new_urls"] += 1
            logger.info(f"[{i}/{len(entries)}] 🔍 Processing ({self.stats['new_urls']} new): {url[:80]}...")

            try:
                # Extract structured data from the post/job page
                data = await extract_structured_post_data(browser.page, url)

                if data and "error" not in data:
                    company = data.get("company", "Unknown")
                    role = data.get("role", "Unknown")
                    location = data.get("location", "Unknown")

                    logger.info(f"  ✓ Extracted: {company} | {role} | {location}")

                    # Write extracted data back to the sheet
                    if row > 0:
                        self.write_result_to_sheet(row, company, role, location, "✅ Extracted")

                    # Track result for summary
                    self.stats["successful"] += 1
                    results.append({"company": company, "role": role, "location": location, "url": url})

                    # Mark as processed
                    self.processed_urls.add(url)
                    self._save_cache()

                else:
                    error_msg = data.get("error", "Unknown error") if data else "No data returned"
                    logger.warning(f"  ❌ Extraction failed: {error_msg}")
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"Extraction failed: {url} - {error_msg}")

                    # Write failure status to sheet
                    if row > 0:
                        self.write_result_to_sheet(row, "", "", "", f"❌ Failed: {error_msg[:50]}")

                    # Still mark as processed to avoid retrying broken URLs
                    self.processed_urls.add(url)
                    self._save_cache()

            except Exception as e:
                logger.error(f"  ❌ Error processing {url}: {e}")
                self.stats["failed"] += 1
                self.stats["errors"].append(f"Error: {url} - {str(e)}")

                # Write error status to sheet
                if row > 0:
                    self.write_result_to_sheet(row, "", "", "", f"❌ Error: {str(e)[:50]}")

                self.processed_urls.add(url)
                self._save_cache()

            # Small delay between requests to avoid rate limiting
            if i < len(entries):
                await asyncio.sleep(1.5)

        return results

    def print_summary(self):
        """Print a detailed summary of the processing run."""
        print("\n" + "=" * 70)
        print("📊 PROCESSING SUMMARY")
        print("=" * 70)
        print(f"📍 URLs in Sheet:    {self.stats['total_in_sheet']}")
        print(f"⏭️  Already Done:     {self.stats['already_processed']}")
        print(f"🆕 Processed New:    {self.stats['new_urls']}")
        print(f"✅ Successfully Added: {self.stats['successful']}")
        print(f"❌ Failed:            {self.stats['failed']}")

        if self.stats["new_urls"] > 0:
            success_rate = (self.stats["successful"] / self.stats["new_urls"]) * 100
            print(f"🎯 Success Rate:     {success_rate:.0f}%")

        if self.stats["errors"]:
            print(f"\n⚠️  Errors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:10]:  # Show first 10
                print(f"   - {error[:120]}")
            if len(self.stats["errors"]) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more")

        print("=" * 70)
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")

    async def run(self, limit: Optional[int] = None, reset_cache: bool = False):
        """
        Run the complete workflow.

        Args:
            limit: Maximum number of NEW URLs to process (None = all)
            reset_cache: If True, reset the processed URLs cache
        """
        if reset_cache:
            self.processed_urls = set()
            self._save_cache()
            logger.info("✅ Cache reset")

        print("\n" + "=" * 70)
        print("📋 LINKEDIN POST URL PROCESSOR")
        print("=" * 70)
        print(f"📊 Google Sheet: {self.sheet_id}")
        print(f"📋 Column: '{self.url_column}'")
        print(f"🔍 Headless: {self.headless}")
        print(f"💾 Processed Cache: {len(self.processed_urls)} URLs")
        print(f"🔄 Reset Cache: {reset_cache}")
        if limit:
            print(f"🎯 Max New URLs: {limit}")
        print("=" * 70 + "\n")

        # Step 1: Connect to Google Sheets
        print("📊 Connecting to Google Sheets...")
        if not self.sheets.connect(worksheet_name=self.worksheet_name):
            logger.error("❌ Failed to connect to Google Sheets")
            print("\n💡 Make sure:")
            print("   1. credentials.json exists in the project folder")
            print(f"   2. The service account has 'Editor' access to the sheet")
            print(f"   3. Sheet ID is correct: {self.sheet_id}")
            return {"success": False, "error": "Google Sheets connection failed"}
        print("✓ Connected to Google Sheets\n")

        # Step 2: Fetch URLs from sheet with row numbers
        print("📋 Fetching URLs from Google Sheet...")
        records = self.fetch_records_from_sheet()
        if not records:
            logger.warning("No data found in sheet")
            return {"success": False, "error": "No data in sheet"}

        entries = self.extract_urls_from_records(records)
        self.stats["total_in_sheet"] = len(entries)
        print(f"✓ Found {len(entries)} LinkedIn URLs in sheet\n")

        if not entries:
            logger.warning("No valid LinkedIn URLs found in column '{}'".format(self.url_column))
            return {"success": False, "error": "No valid LinkedIn URLs"}

        # Step 3: Ensure output columns exist in the sheet
        print("📋 Ensuring output columns (Company, Role, Location, Status, Processed Date)...")
        col_map = self.ensure_output_columns()
        if col_map:
            print(f"✓ Output columns ready: {len(col_map)} columns\n")
        else:
            print("⚠️  Could not verify output columns, will try to write anyway\n")

        # Step 4: Filter out already processed URLs
        new_entries = [e for e in entries if e["url"] not in self.processed_urls]
        already_done = len(entries) - len(new_entries)
        self.stats["already_processed"] = already_done

        if not new_entries:
            print(f"✅ All {len(entries)} URLs already processed! Nothing new to do.")
            self.print_summary()
            return {"success": True, "stats": self.stats}

        print(f"🆕 {len(new_entries)} new URLs to process ({already_done} already done)\n")

        # Step 5: Process URLs with authenticated browser
        print(f"🔍 Processing {len(new_entries)} URLs...\n")

        if limit:
            new_entries = new_entries[:limit]
            print(f"(Limited to {limit} URLs)\n")

        async with BrowserManager(headless=self.headless) as browser:
            # Load LinkedIn session
            print("🔑 Loading LinkedIn session...")
            try:
                await browser.load_session(self.session_file)
                print("✓ Session loaded\n")
            except Exception as e:
                logger.error(f"❌ Failed to load LinkedIn session: {e}")
                print("\n💡 Run 'python samples/create_session.py' to create a session first")
                return {"success": False, "error": f"Session load failed: {e}"}

            # Process each entry (already limited to limit above)
            results = await self.process_urls(browser, new_entries)

        # Step 6: Print summary
        self.print_summary()

        return {
            "success": self.stats["successful"] > 0,
            "stats": self.stats,
            "results": results
        }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract LinkedIn Post/Job URL data from Google Sheet and write results back",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_manual_posts.py                    # Process all new URLs
  python process_manual_posts.py --headless False    # Show browser
  python process_manual_posts.py --limit 5           # Only process 5 URLs
  python process_manual_posts.py --reset-cache       # Reprocess all URLs
  python process_manual_posts.py --verbose           # Detailed logging
  python sync_posts_to_notion.py                     # After extraction, push to Notion

SETUP CHECKLIST:
  1. Create LinkedIn session: python samples/create_session.py
  2. Share your Google Sheet with: linkedin-scraper-755@linkedin-job-scraper-491917.iam.gserviceaccount.com
  3. Ensure credentials.json exists in the project root
        """
    )

    parser.add_argument(
        "--headless",
        type=bool,
        default=True,
        help="Run browser in headless mode (default: True). Set to False to see the browser."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of NEW URLs to process (default: all)"
    )
    parser.add_argument(
        "--reset-cache",
        action="store_true",
        help="Reset the processed URLs cache and reprocess ALL URLs"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging"
    )
    parser.add_argument(
        "--session-file",
        default="linkedin_session.json",
        help="Path to LinkedIn session file (default: linkedin_session.json)"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create processor
    processor = PostURLProcessor(
        session_file=args.session_file,
        headless=args.headless
    )

    # Run
    results = await processor.run(
        limit=args.limit,
        reset_cache=args.reset_cache
    )

    sys.exit(0 if results.get("success") else 0 if results.get("stats", {}).get("already_processed", 0) > 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
