#!/usr/bin/env python3
"""
Job Description Restructuring Script

Fetches existing plain text job descriptions from Google Sheets,
applies intelligent formatting, and updates them with proper HTML structure.

Run this ONCE to restructure all existing job descriptions.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def format_plain_text(text: str) -> str:
    """
    Smart formatting for plain text descriptions.
    Detects paragraphs, bullet points, sections, and emoji markers.
    """
    if not text or not text.strip():
        return None
    
    # Skip if already HTML formatted
    if '<p>' in text or '<ul>' in text or '<li>' in text or '<h3>' in text:
        print("  ℹ️  Already formatted, skipping...")
        return text
    
    lines = text.split('\n')
    formatted_parts = []
    current_paragraph = []
    current_list = []
    
    # Emoji patterns that indicate section headers
    emoji_headers = ['📌', '📍', '🏢', '🕒', '🔎', '💰', '👤', '✅', '⭐', '🎯', '📋', '💼', '🏆', '📞', '📧', '🌐']
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if current_paragraph:
                formatted_parts.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            if current_list:
                formatted_parts.append(f'<ul>{"".join([f"<li>{item}</li>" for item in current_list])}</ul>')
                current_list = []
            continue
        
        # Detect bullet points
        if line.startswith(('•', '▪', '▸', '◦', '-', '*', '➤', '►', '▸')) or (len(line) > 2 and line[1] == '.' and line[0].isdigit()):
            # Save current paragraph
            if current_paragraph:
                formatted_parts.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            # Add to list
            clean_line = line[1:].strip() if len(line) > 1 else line
            current_list.append(clean_line)
        # Detect emoji-based section headers
        elif any(line.startswith(emoji) for emoji in emoji_headers):
            # Save current paragraph and list
            if current_paragraph:
                formatted_parts.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            if current_list:
                formatted_parts.append(f'<ul>{"".join([f"<li>{item}</li>" for item in current_list])}</ul>')
                current_list = []
            # Add as heading (remove emoji for cleaner look, or keep it)
            formatted_parts.append(f'<h3>{line}</h3>')
        # Detect section headings (all caps or ends with colon)
        elif line.isupper() or line.endswith(':'):
            # Save current paragraph and list
            if current_paragraph:
                formatted_parts.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            if current_list:
                formatted_parts.append(f'<ul>{"".join([f"<li>{item}</li>" for item in current_list])}</ul>')
                current_list = []
            # Add heading
            formatted_parts.append(f'<h3>{line}</h3>')
        # Regular text - add to paragraph
        else:
            if current_list:
                formatted_parts.append(f'<ul>{"".join([f"<li>{item}</li>" for item in current_list])}</ul>')
                current_list = []
            current_paragraph.append(line)
    
    # Don't forget remaining content
    if current_paragraph:
        formatted_parts.append(f'<p>{" ".join(current_paragraph)}</p>')
    if current_list:
        formatted_parts.append(f'<ul>{"".join([f"<li>{item}</li>" for item in current_list])}</ul>')
    
    result = '\n'.join(formatted_parts) if formatted_parts else None
    
    if result and len(result) < 100:
        # Too short, probably not properly formatted
        return None
    
    return result


def clean_description(text: str) -> str:
    """Clean up common issues in job descriptions."""
    if not text:
        return text
    
    # Remove common artifacts
    text = text.replace("… more", "")
    text = text.replace("... more", "")
    text = text.replace("Show less", "")
    text = text.replace("Show more", "")
    text = text.replace("See less", "")
    text = text.replace("See more", "")
    
    # Remove multiple spaces
    while "  " in text:
        text = text.replace("  ", " ")
    
    return text.strip()


def main():
    """Main function to restructure job descriptions."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("❌ Missing dependencies. Install with:")
        print("   pip install gspread google-auth")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("📝 JOB DESCRIPTION RESTRUCTURING TOOL")
    print("="*70)
    print()
    print("This script will:")
    print("  1. Fetch all job descriptions from Google Sheets")
    print("  2. Apply intelligent formatting (paragraphs, bullets, headings)")
    print("  3. Update the sheet with formatted HTML")
    print()
    print("⚠️  WARNING: This will modify your Google Sheets data!")
    print("   Make a backup copy of your sheet first!")
    print()
    
    # Get user confirmation
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Aborted by user.")
        sys.exit(0)
    
    # Connect to Google Sheets
    print("\n📊 Connecting to Google Sheets...")
    
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    worksheet_name = os.getenv('WORKSHEET_NAME', 'Consulting_Jobs_India')
    
    if not sheet_id:
        print("❌ GOOGLE_SHEET_ID not set in environment")
        sys.exit(1)
    
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(str(creds_file), scopes=scopes)
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        print(f"✅ Connected to: {worksheet_name}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    # Fetch all data
    print("\n📥 Fetching all jobs from Google Sheets...")
    try:
        all_records = worksheet.get_all_records()
        print(f"✅ Found {len(all_records)} jobs")
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        sys.exit(1)
    
    # Find column indices
    headers = worksheet.row_values(1)
    print(f"\n📋 Current columns: {', '.join(headers)}")
    
    try:
        desc_col_idx = headers.index('Job Description') + 1
        print(f"✅ Job Description column: {chr(64 + desc_col_idx)} ({desc_col_idx})")
    except ValueError:
        print("❌ 'Job Description' column not found!")
        sys.exit(1)
    
    # Process each job
    print(f"\n🔄 Processing {len(all_records)} job descriptions...")
    print()
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, job in enumerate(all_records, 1):
        job_title = job.get('Job Title', 'Unknown')
        company = job.get('Company', 'Unknown')
        description = job.get('Job Description', '')
        
        # Clean description
        description = clean_description(description)
        
        if not description or len(description) < 50:
            print(f"  [{i}/{len(all_records)}] ⚠️  Skipping '{job_title}' at {company} - Too short")
            skipped_count += 1
            continue
        
        # Format description
        formatted = format_plain_text(description)
        
        if not formatted:
            print(f"  [{i}/{len(all_records)}] ⚠️  Skipping '{job_title}' at {company} - Could not format")
            skipped_count += 1
            continue
        
        if formatted == description:
            print(f"  [{i}/{len(all_records)}] ℹ️  Skipping '{job_title}' at {company} - Already formatted")
            skipped_count += 1
            continue
        
        # Update in sheet
        try:
            worksheet.update_cell(i + 1, desc_col_idx, formatted)  # +1 for header row
            print(f"  [{i}/{len(all_records)}] ✅ Updated '{job_title}' at {company}")
            updated_count += 1
        except Exception as e:
            print(f"  [{i}/{len(all_records)}] ❌ Error updating '{job_title}' at {company}: {e}")
            error_count += 1
        
        # Progress indicator every 10 jobs
        if i % 10 == 0:
            print(f"  ... processed {i}/{len(all_records)} jobs ...")
    
    # Summary
    print("\n" + "="*70)
    print("📊 RESTRUCTURING SUMMARY")
    print("="*70)
    print(f"Total jobs processed: {len(all_records)}")
    print(f"✅ Successfully formatted: {updated_count}")
    print(f"⚠️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print()
    
    if updated_count > 0:
        print("🎉 Success! Job descriptions have been restructured.")
        print()
        print("Next steps:")
        print("  1. Open your Google Sheet and verify the formatting")
        print("  2. Hard refresh your browser (Ctrl+Shift+R)")
        print("  3. View a job detail page to see the formatted descriptions")
        print()
    else:
        print("⚠️  No descriptions were updated.")
        print("   This could mean:")
        print("   - All descriptions are already formatted")
        print("   - Descriptions are too short to format")
        print("   - There was an issue with the formatting logic")
        print()
    
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
