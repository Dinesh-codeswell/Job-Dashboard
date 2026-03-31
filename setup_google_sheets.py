#!/usr/bin/env python3
"""
Setup script for Google Sheets integration.

This script helps you configure Google Sheets API access interactively.
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv, set_key

load_dotenv()


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def check_credentials_file() -> bool:
    """Check if credentials file exists."""
    creds_file = Path("credentials.json")
    if creds_file.exists():
        print(f"✓ Found credentials file: {creds_file.absolute()}")
        
        # Validate it's a valid JSON
        try:
            with open(creds_file) as f:
                data = json.load(f)
                if "client_email" in data:
                    print(f"✓ Valid service account: {data['client_email']}")
                    return True
                else:
                    print("✗ Invalid credentials file format")
                    return False
        except Exception as e:
            print(f"✗ Error reading credentials: {e}")
            return False
    else:
        print("✗ credentials.json not found")
        return False


def check_sheet_id() -> bool:
    """Check if sheet ID is configured."""
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if sheet_id:
        print(f"✓ Google Sheet ID configured: {sheet_id}")
        return True
    else:
        print("✗ Google Sheet ID not configured")
        return False


def get_sheet_id_from_url():
    """Extract sheet ID from a Google Sheets URL."""
    print("\n📋 To find your Sheet ID:")
    print("   1. Open your Google Sheet")
    print("   2. Look at the URL:")
    print("      https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit")
    print("   3. Copy the SPREADSHEET_ID part\n")
    
    url = input("Paste your Google Sheets URL (or press Enter to skip): ").strip()
    
    if not url:
        return None
    
    # Extract sheet ID from URL
    if "/d/" in url:
        parts = url.split("/d/")
        if len(parts) > 1:
            sheet_id = parts[1].split("/")[0]
            return sheet_id
    
    print("✗ Could not extract Sheet ID from URL")
    return None


def update_env_file(sheet_id: str):
    """Update .env file with sheet ID."""
    env_file = Path(".env")
    
    if not env_file.exists():
        # Create .env file
        with open(env_file, "w") as f:
            f.write("# LinkedIn credentials\n")
            f.write("LINKEDIN_EMAIL=your.email@example.com\n")
            f.write("LINKEDIN_PASSWORD=your_password_here\n\n")
            f.write("# Google Sheets Configuration\n")
            f.write(f"GOOGLE_SHEET_ID={sheet_id}\n")
            f.write("GOOGLE_CREDENTIALS_FILE=credentials.json\n")
        print(f"✓ Created .env file with Sheet ID")
    else:
        # Update existing .env file
        set_key(str(env_file), "GOOGLE_SHEET_ID", sheet_id)
        set_key(str(env_file), "GOOGLE_CREDENTIALS_FILE", "credentials.json")
        print(f"✓ Updated .env file with Sheet ID")


def test_connection():
    """Test Google Sheets connection."""
    print("\n🧪 Testing Google Sheets connection...")
    
    try:
        from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration
        
        sheets = GoogleSheetsIntegration()
        if sheets.connect(worksheet_name="TestConnection"):
            print("✓ Successfully connected to Google Sheets!")
            
            # Add a test row
            test_data = {
                "job_title": "Test Job (can delete)",
                "company": "Test Company",
                "location": "Test Location",
                "posted_date": "Today",
                "applicant_count": "0",
                "linkedin_url": "https://linkedin.com",
                "date_added": "Test entry"
            }
            
            if sheets.upload_job(test_data):
                print("✓ Successfully uploaded test job!")
                print("\n✓ Google Sheets integration is working correctly!")
                return True
            else:
                print("✗ Failed to upload test job")
                return False
        else:
            print("✗ Failed to connect to Google Sheets")
            return False
            
    except Exception as e:
        print(f"✗ Error testing connection: {e}")
        return False


def main():
    """Main setup flow."""
    print_header("Google Sheets Setup Wizard")
    
    # Step 1: Check credentials
    print("Step 1: Checking credentials.json")
    print("-"*60)
    has_credentials = check_credentials_file()
    
    if not has_credentials:
        print("\n📖 ACTION REQUIRED:")
        print("   Please follow the instructions in GOOGLE_SHEETS_SETUP.md")
        print("   to create a Google Cloud project and download credentials.json")
        print("\n   Quick steps:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Create a new project")
        print("   3. Enable Google Sheets API")
        print("   4. Create a service account")
        print("   5. Download JSON key and save as 'credentials.json'")
        print()
        return 1
    
    # Step 2: Check sheet ID
    print("\nStep 2: Checking Google Sheet ID")
    print("-"*60)
    has_sheet_id = check_sheet_id()
    
    if not has_sheet_id:
        sheet_id = get_sheet_id_from_url()
        if sheet_id:
            update_env_file(sheet_id)
            has_sheet_id = True
        else:
            print("\n⚠️ Sheet ID not configured. You can configure it later in .env file")
    
    # Step 3: Test connection
    if has_sheet_id:
        print("\nStep 3: Testing Connection")
        print("-"*60)
        test_connection()
    
    # Summary
    print_header("Setup Summary")
    
    if has_credentials and has_sheet_id:
        print("✓ All required configuration is complete!")
        print("\n🚀 You can now run the job scraper:")
        print("   python jobs_to_sheets.py -k \"software engineer\" -l \"San Francisco\"")
        return 0
    else:
        print("⚠️ Some configuration is still missing.")
        print("\n📖 Please complete the setup by following GOOGLE_SHEETS_SETUP.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
