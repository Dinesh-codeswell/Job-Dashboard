#!/usr/bin/env python3
"""
Fix Google Sheets Column Structure for Consulting Jobs

This script will:
1. Connect to your Google Sheet
2. Check current column structure
3. Add "Company" column if missing
4. Reorder columns to match expected structure

Expected structure:
| Company | Job Title | Employment Type | Posted | Location | Job Description | Job URL | Search City | Date Added |
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def fix_google_sheets():
    """Fix Google Sheets column structure."""
    
    print("="*70)
    print("🔧 Google Sheets Column Structure Fixer")
    print("="*70)
    print()
    
    # Get credentials
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    
    if not sheet_id:
        print("❌ ERROR: GOOGLE_SHEET_ID not set in .env file")
        return False
    
    if not Path(credentials_file).exists():
        print(f"❌ ERROR: Credentials file not found: {credentials_file}")
        print("   Please follow GOOGLE_SHEETS_SETUP.md to set up Google Sheets API")
        return False
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Define scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Load credentials
        creds = Credentials.from_service_account_file(
            credentials_file,
            scopes=scopes
        )
        
        # Initialize client
        gc = gspread.authorize(creds)
        
        # Open spreadsheet
        spreadsheet = gc.open_by_key(sheet_id)
        
        print(f"✓ Connected to Google Sheet: {spreadsheet.title}")
        print()
        
        # Get or create worksheet
        worksheet_name = "Consulting_Jobs_India"
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"✓ Found worksheet: {worksheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            print(f"⚠️  Worksheet '{worksheet_name}' not found")
            print("   Creating new worksheet...")
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=1000,
                cols=20
            )
            print(f"✓ Created worksheet: {worksheet_name}")
        
        # Get current headers
        try:
            current_headers = worksheet.row_values(1)
            print(f"✓ Current headers: {current_headers}")
            print()
        except:
            current_headers = []
        
        # Expected headers
        expected_headers = [
            "Company",
            "Job Title",
            "Employment Type",
            "Posted",
            "Location",
            "Job Description",
            "Job URL",
            "Search City",
            "Date Added"
        ]
        
        print("Expected headers:")
        print(f"   {expected_headers}")
        print()
        
        # Check if headers match
        if current_headers == expected_headers:
            print("✅ Headers already match! No changes needed.")
            print()
            print("Your Google Sheets structure is correct.")
            print("The scraper should work correctly now.")
            return True
        
        # Check if Company column is missing
        if "Company" not in current_headers:
            print("⚠️  'Company' column is MISSING!")
            print()
            
            # Option 1: Insert Company column at the beginning
            print("🔧 Fixing: Inserting 'Company' column at position A...")
            try:
                worksheet.insert_cols([["Company"]], 1)
                print("✓ Inserted 'Company' column")
                
                # Now update other headers if needed
                current_headers = worksheet.row_values(1)
                
                # Update header row to match expected structure
                worksheet.update('A1:I1', [expected_headers])
                print("✓ Updated all headers to match expected structure")
                
                # Format header row (bold)
                worksheet.format('A1:I1', {'textFormat': {'bold': True}})
                print("✓ Formatted header row (bold)")
                
            except Exception as e:
                print(f"❌ Error updating headers: {e}")
                print()
                print("Alternative solution:")
                print("1. Create a NEW worksheet with correct structure")
                print("2. Or manually add 'Company' column in Google Sheets")
                return False
        else:
            # Headers exist but might be in wrong order
            print("⚠️  Headers exist but might be in wrong order")
            print("🔧 Reordering headers to match expected structure...")
            try:
                worksheet.update('A1:I1', [expected_headers])
                print("✓ Updated headers to match expected structure")
                
                # Format header row (bold)
                worksheet.format('A1:I1', {'textFormat': {'bold': True}})
                print("✓ Formatted header row (bold)")
                
            except Exception as e:
                print(f"❌ Error updating headers: {e}")
                return False
        
        print()
        print("="*70)
        print("✅ Google Sheets Structure Fixed!")
        print("="*70)
        print()
        print("New column structure:")
        print("   | Company | Job Title | Employment Type | Posted | Location |")
        print("   | Job Description | Job URL | Search City | Date Added |")
        print()
        print("Next steps:")
        print("1. Run the scraper: python scrape_consulting_india.py")
        print("2. Check Google Sheets to verify data is in correct columns")
        print()
        
        return True
        
    except gspread.exceptions.APIError as e:
        print(f"❌ Google Sheets API Error: {e}")
        print()
        print("Possible issues:")
        print("1. Invalid credentials - check credentials.json")
        print("2. Sheet not shared with service account")
        print("3. Invalid sheet ID")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_google_sheets()
    sys.exit(0 if success else 1)
