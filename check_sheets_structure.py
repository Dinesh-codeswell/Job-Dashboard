"""
Quick diagnostic to check if Company Logo column exists in Google Sheets.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import gspread
    from google.oauth2.service_account import Credentials

    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    worksheet_name = os.getenv('WORKSHEET_NAME', 'Consulting_Jobs_India')

    if not sheet_id:
        print("❌ GOOGLE_SHEET_ID not set!")
        sys.exit(1)

    print(f"📊 Checking Google Sheet: {sheet_id}")
    print(f"📄 Worksheet: {worksheet_name}")
    print()

    # Connect
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(str(creds_file), scopes=scopes)
    gc = gspread.authorize(creds)

    spreadsheet = gc.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(worksheet_name)

    # Get headers
    headers = worksheet.row_values(1)
    
    print("✅ Current Columns:")
    for i, header in enumerate(headers, 1):
        col_letter = chr(64 + i)
        print(f"   {col_letter}. {header}")
    
    print()
    
    # Check for Company Logo
    if 'Company Logo' in headers:
        col_index = headers.index('Company Logo') + 1
        col_letter = chr(64 + col_index)
        print(f"✅ 'Company Logo' column FOUND at {col_letter}")
        
        # Check if any data exists
        logo_column = worksheet.col_values(col_index)
        logos_with_data = [x for x in logo_column[1:] if x.strip()]  # Skip header, count non-empty
        
        print(f"   Total rows: {len(logo_column) - 1}")
        print(f"   Rows with logos: {logos_with_data}")
        
        if logos_with_data:
            print(f"   ✅ Some jobs have logo URLs!")
            print(f"   Sample: {logos_with_data[0][:100]}...")
        else:
            print(f"   ⚠️  Column exists but NO logo URLs populated yet")
            print(f"   → Run scraper to populate logos")
    else:
        print("❌ 'Company Logo' column NOT FOUND!")
        print()
        print("   Run this to add it:")
        print("   python add_company_logo_column.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
