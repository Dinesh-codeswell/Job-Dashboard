"""
Script to add Company Logo column to existing Google Sheets.

This script inserts a new "Company Logo" column (Column B) in your existing
Google Sheet, shifting all other columns to the right.

Run this ONCE to update your existing Google Sheet structure.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def add_company_logo_column():
    """Add Company Logo column to existing Google Sheet."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        # Get credentials
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        worksheet_name = os.getenv('WORKSHEET_NAME', 'Consulting_Jobs_India')

        if not sheet_id:
            print("❌ Error: GOOGLE_SHEET_ID not set in environment")
            return False

        # Check credentials
        creds_path = Path(creds_file)
        if not creds_path.exists():
            print(f"❌ Error: Credentials file not found: {creds_file}")
            print("   Please follow GOOGLE_SHEETS_SETUP.md to set up Google Sheets API")
            return False

        # Authenticate
        print("🔐 Authenticating with Google Sheets...")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        gc = gspread.authorize(creds)

        # Open spreadsheet
        print(f"📊 Opening spreadsheet: {sheet_id}")
        spreadsheet = gc.open_by_key(sheet_id)

        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"✓ Found worksheet: {worksheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            print(f"❌ Worksheet not found: {worksheet_name}")
            print("   Available worksheets:")
            for ws in spreadsheet.worksheets():
                print(f"     - {ws.title}")
            return False

        # Get current headers
        headers = worksheet.row_values(1)
        print(f"\n📋 Current headers ({len(headers)} columns):")
        for i, header in enumerate(headers, 1):
            print(f"   {chr(64+i)}. {header}")

        # Check if Company Logo column already exists
        if 'Company Logo' in headers:
            print("\n✅ Company Logo column already exists!")
            return True

        # Insert Company Logo column at position B (index 2)
        print("\n➕ Inserting 'Company Logo' column at position B...")
        worksheet.insert_cols([['Company Logo']], 2)

        # Verify the change
        new_headers = worksheet.row_values(1)
        print(f"\n✅ Updated headers ({len(new_headers)} columns):")
        for i, header in enumerate(new_headers, 1):
            print(f"   {chr(64+i)}. {header}")

        # Format the new header
        worksheet.format('B1', {'textFormat': {'bold': True}})

        # Adjust column width for better visibility
        worksheet.update_column_width(2, 300)  # Column B width

        print("\n✅ Successfully added Company Logo column!")
        print("\n📝 Next steps:")
        print("   1. Run your scraper again to populate logo URLs")
        print("   2. The dashboard will automatically display logos once available")
        print("   3. Existing jobs will show without logos (which is fine)")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("  Add Company Logo Column to Google Sheets")
    print("=" * 60)
    print()

    success = add_company_logo_column()

    print()
    if success:
        print("✅ Script completed successfully!")
        sys.exit(0)
    else:
        print("❌ Script failed!")
        sys.exit(1)
