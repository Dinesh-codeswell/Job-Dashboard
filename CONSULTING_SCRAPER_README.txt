================================================================================
                    CONSULTING JOBS SCRAPER - INDIA
                        Setup Complete & Ready to Use
================================================================================

🎯 FOCUS: Exclusively Consulting Roles in India
🏙️  CITIES: 25+ Indian cities (Chennai, Mumbai, Bangalore, Pune, Gurugram, etc.)
💼 ROLES: 36+ consulting keywords (Management, IT, SAP, Oracle, Financial, etc.)

================================================================================
                         WHAT WAS CREATED
================================================================================

1. scrape_consulting_india.py
   - Main scraping script for consulting jobs
   - Automatically searches all major Indian cities
   - 36+ consulting-related keywords built-in
   - Uploads to dedicated "Consulting_Jobs_India" Google Sheet

2. consulting_jobs_menu.bat
   - Interactive Windows menu for quick access
   - Pre-configured city searches
   - Google Sheets operations
   - One-click scraping

3. CONSULTING_JOBS_COMMANDS.txt
   - Complete command reference
   - City-specific commands
   - Role-specific commands
   - Google Sheets operations
   - Best practices for consulting roles

================================================================================
                         GOOGLE SHEETS COLUMNS
================================================================================

Your Consulting_Jobs_India sheet has these columns:

A. Job Title          - Position name (e.g., "Management Consultant")
B. Employment Type    - Full-time / Part-time / Contract / Internship
C. Posted             - Time ago (e.g., "2 hours ago")
D. Location           - Job location
E. Job Description    - Complete JD (no "… more" artifacts)
F. Job URL            - Direct LinkedIn application link
G. Search City        - City where job was found
H. Date Added         - When it was scraped

================================================================================
                         QUICK START COMMANDS
================================================================================

# Most Common - All Cities (10 jobs each)
python scrape_consulting_india.py

# Tier 1 Cities Only (Metros - 20 jobs each)
python scrape_consulting_india.py --tier-1-only --limit-per-city 20

# Specific City (e.g., Chennai)
python scrape_consulting_india.py --cities "Chennai" --limit-per-city 20

# Multiple Cities
python scrape_consulting_india.py --cities "Bangalore" "Mumbai" "Pune" --limit-per-city 15

# Show Browser (See scraping in action)
python scrape_consulting_india.py --headless False

# Use Interactive Menu
consulting_jobs_menu.bat

================================================================================
                         CONSULTING ROLES COVERED
================================================================================

✓ Management Consultant
✓ Business Consultant
✓ Strategy Consultant
✓ IT Consultant
✓ Technology Consultant
✓ Digital Consultant
✓ Financial Consultant
✓ Finance Consultant
✓ HR Consultant
✓ Human Resources Consultant
✓ Operations Consultant
✓ Process Consultant
✓ SAP Consultant
✓ Oracle Consultant
✓ Salesforce Consultant
✓ Cloud Consultant
✓ Cybersecurity Consultant
✓ Security Consultant
✓ Data Consultant
✓ Analytics Consultant
✓ Business Intelligence Consultant
✓ ERP Consultant
✓ CRM Consultant
✓ Risk Consultant
✓ Compliance Consultant
✓ Tax Consultant
✓ Audit Consultant
✓ Legal Consultant
✓ Senior Consultant
✓ Principal Consultant
✓ Lead Consultant
✓ Consulting Analyst
✓ Business Analyst
✓ Management Analyst

================================================================================
                         CITIES COVERED
================================================================================

Tier 1 (Metros):
✓ Bangalore       ✓ Mumbai          ✓ Chennai
✓ Pune            ✓ Hyderabad       ✓ Gurugram
✓ Gurgaon         ✓ New Delhi       ✓ Delhi
✓ Noida

Tier 2 (IT/Consulting Hubs):
✓ Kolkata         ✓ Ahmedabad       ✓ Kochi
✓ Coimbatore      ✓ Chandigarh      ✓ Jaipur
✓ Thiruvananthapuram                ✓ Visakhapatnam
✓ Nagpur          ✓ Indore

Others:
✓ Bhopal          ✓ Lucknow         ✓ Surat
✓ Vadodara        ✓ Bhubaneswar     ✓ Mangalore
✓ Nashik

================================================================================
                         DAILY WORKFLOW
================================================================================

MORNING (9 AM):
- Check overnight postings
python scrape_consulting_india.py --tier-1-only --limit-per-city 10

MID-DAY (1 PM):
- Specific city search
python scrape_consulting_india.py --cities "Bangalore" --limit-per-city 20

EVENING (6 PM):
- Full scan
python scrape_consulting_india.py --limit-per-city 15

MONDAY MORNING:
- Weekly comprehensive scrape
python scrape_consulting_india.py --limit-per-city 25 --headless False

FRIDAY:
- Export weekly report
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; import csv; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); f=open('weekly_consulting_jobs.csv','w',newline='',encoding='utf-8'); w=csv.DictWriter(f,fieldnames=jobs[0].keys()); w.writeheader(); w.writerows(jobs); f.close(); print('Exported!')"

================================================================================
                         GOOGLE SHEETS QUERIES
================================================================================

# Check total jobs
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); print(f'Total: {len(gs.get_all_jobs())}')"

# Count by city
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); cities = {}; [cities.__setitem__(j.get('Search City', 'Unknown'), cities.get(j.get('Search City', 'Unknown'), 0) + 1) for j in jobs]; [print(f'{c}: {count}') for c, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)]"

# Find SAP jobs
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); [print(f'{j.get(\"Job Title\")} - {j.get(\"Search City\")}') for j in jobs if 'SAP' in j.get('Job Title', '')]"

# Find Big 4 jobs (Deloitte, PwC, EY, KPMG)
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); big4 = ['Deloitte', 'PwC', 'EY', 'KPMG']; [print(f'{j.get(\"Job Title\")} at {j.get(\"Company\")} - {j.get(\"Search City\")}') for j in jobs if any(b in j.get('Company', '') for b in big4)]"

# Find jobs posted today
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); [print(f'{j.get(\"Job Title\")} - {j.get(\"Posted\")} - {j.get(\"Search City\")}') for j in jobs if 'hour' in j.get('Posted', '').lower()]"

# Export to CSV
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; import csv; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); f=open('consulting_jobs.csv','w',newline='',encoding='utf-8'); w=csv.DictWriter(f,fieldnames=jobs[0].keys()); w.writeheader(); w.writerows(jobs); f.close()"

================================================================================
                         TARGET CONSULTING FIRMS
================================================================================

Big 4:
- Deloitte
- PwC
- EY (Ernst & Young)
- KPMG

MBB (Elite Strategy):
- McKinsey & Company
- Boston Consulting Group (BCG)
- Bain & Company

Tier 2 Strategy:
- Oliver Wyman
- Kearney (formerly A.T. Kearney)
- L.E.K. Consulting
- Roland Berger

IT Consulting:
- Accenture
- TCS (Tata Consultancy Services)
- Infosys Consulting
- Wipro Consulting
- HCL Technologies
- Tech Mahindra
- Cognizant
- Capgemini
- IBM Consulting

Boutique/Specialized:
- ZS Associates
- Mu Sigma
- Fractal Analytics
- Crisil
- ICRA
- Grant Thornton
- BDO

================================================================================
                         BEST PRACTICES
================================================================================

1. RATE LIMITING:
   - Wait 5+ seconds between cities (built-in)
   - Use limit-per-city 10-15 for daily searches
   - Use limit-per-city 20-25 for weekly scans
   - If blocked, wait 2-3 hours

2. SESSION MANAGEMENT:
   - Re-run create_session.py every 1-2 weeks
   - Keep linkedin_session.json secure

3. ORGANIZATION:
   - Use separate worksheets for different weeks
   - Export to CSV every Friday
   - Filter by city for location-specific applications
   - Sort by "Posted" to find newest opportunities

4. SEARCH STRATEGY:
   - Focus on Tier 1 cities first
   - Run comprehensive scans on Monday mornings
   - Do quick city-specific searches daily
   - Filter for "posted in last 24 hours" on LinkedIn

================================================================================
                         TROUBLESHOOTING
================================================================================

# Rate limited?
Wait 2-3 hours, then try with lower limits:
python scrape_consulting_india.py --limit-per-city 5 --tier-1-only

# Session expired?
python samples\create_session.py

# No jobs found?
- Try different keywords
- Increase limit-per-city
- Check if LinkedIn is accessible

# Google Sheets error?
- Check credentials.json exists
- Verify Sheet ID in .env file
- Ensure sheet is shared with service account

================================================================================
                         FILE LOCATIONS
================================================================================

Main Script:
  scrape_consulting_india.py

Quick Menu:
  consulting_jobs_menu.bat

Documentation:
  CONSULTING_JOBS_COMMANDS.txt - Complete command reference
  COMMANDS_REFERENCE.txt - General commands
  QUICKSTART.md - Getting started guide

Session Files:
  linkedin_session.json - LinkedIn authentication
  credentials.json - Google API credentials
  .env - Configuration (Sheet ID, etc.)

================================================================================
                         SUPPORT
================================================================================

For issues or questions:
1. Check CONSULTING_JOBS_COMMANDS.txt
2. Review JOB_SCRAPER_WORKFLOW.md
3. Run: python scrape_consulting_india.py --help

================================================================================
                    Created for Consulting Jobs Focus - India
                         Setup Date: March 31, 2026
                              Version: 1.0
================================================================================
