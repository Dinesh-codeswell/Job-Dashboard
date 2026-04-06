@echo off
REM ========================================================================
REM Quick Reference - Automation Commands
REM ========================================================================

echo.
echo ========================================================================
echo   🤖 AUTOMATED JOB SCRAPER - QUICK REFERENCE
echo ========================================================================
echo.
echo 📍 WHAT: Runs LinkedIn + Indeed + Naukri scraper every 15 minutes
echo 📍 WHERE: C:\linkedin_scraper
echo 📍 LOGS: C:\linkedin_scraper\logs\
echo.
echo ========================================================================
echo   ESSENTIAL COMMANDS
echo ========================================================================
echo.
echo 1️⃣  SETUP (Run ONCE to enable automation):
echo    Right-click: setup_automation.bat → Run as administrator
echo.
echo 2️⃣  MANAGE (Start/Stop/Check):
echo    automation_manager.bat
echo.
echo 3️⃣  CHECK STATUS:
echo    automation_manager.bat status
echo.
echo 4️⃣  STOP AUTOMATION:
echo    automation_manager.bat stop
echo.
echo 5️⃣  START AUTOMATION:
echo    automation_manager.bat start
echo.
echo 6️⃣  VIEW LOGS:
echo    automation_manager.bat logs
echo    OR
echo    Open: C:\linkedin_scraper\logs\
echo.
echo 7️⃣  RUN MANUALLY (One-time immediate execution):
echo    automation_manager.bat
echo    Select option 6
echo.
echo ========================================================================
echo   TROUBLESHOOTING
echo ========================================================================
echo.
echo ❌ Task not running?
echo    → automation_manager.bat status
echo    → Check logs for errors
echo.
echo ❌ LinkedIn failing?
echo    → python samples\create_session.py
echo.
echo ❌ Google Sheets errors?
echo    → Check credentials.json exists
echo    → Verify GOOGLE_SHEET_ID in .env
echo.
echo ❌ Need to temporarily pause?
echo    → automation_manager.bat stop
echo    → automation_manager.bat start (to resume)
echo.
echo ========================================================================
echo   FILES OVERVIEW
echo ========================================================================
echo.
echo 📄 auto_scraper.py              - Main automated runner
echo 📄 scrape_all_india_jobs.py     - Core scraper (LinkedIn+Indeed+Naukri)
echo 📄 setup_automation.bat         - Initial setup (run once)
echo 📄 automation_manager.bat       - Management console
echo 📄 AUTOMATION_GUIDE.md          - Complete documentation
echo 📁 logs/                        - Daily log files
echo.
echo ========================================================================
echo   SCHEDULE DETAILS
echo ========================================================================
echo.
echo ⏰ Frequency: Every 15 minutes
echo 🔄 Task Name: LinkedInJobsScraper_Auto
echo 👤 Runs as: SYSTEM (works even when logged out)
echo 📊 Output: Google Sheets (LinkedIn_Jobs, Indeed_Jobs, Naukri_Jobs tabs)
echo.
echo ========================================================================
echo.
pause
