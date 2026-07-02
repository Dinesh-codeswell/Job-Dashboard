@echo off
REM Quick Scraper Monitoring Tool
REM Run this anytime to check scraper status and view jobs

echo ========================================================================
echo SCRAPER STATUS MONITOR
echo ========================================================================
echo.

echo [1] Checking if automation task exists...
schtasks /query /tn "LinkedInJobsScraper_Auto" /fo LIST 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Task not found! Run setup_with_wrapper.ps1 first
    goto :end
)

echo.
echo ========================================================================
echo [2] TASK STATUS
echo ========================================================================
schtasks /query /tn "LinkedInJobsScraper_Auto" /fo LIST | findstr /C:"Status" /C:"Next Run Time" /C:"Last Run Time" /C:"Last Result"

echo.
echo ========================================================================
echo [3] RECENT LOGS (Last 20 lines)
echo ========================================================================
if exist "logs\scraper_*.log" (
    for /f "delims=" %%f in ('dir /b /od logs\scraper_*.log') do set "latest=%%f"
    echo Latest log: logs\!latest!
    echo.
    powershell -Command "Get-Content 'logs\!latest!' -Tail 20"
) else (
    echo No logs found yet. Scraper hasn't run.
)

echo.
echo ========================================================================
echo [4] GOOGLE SHEETS LINK
echo ========================================================================
echo Open this to see jobs being added:
echo https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
echo.
echo Worksheets to check:
echo   - LinkedIn_Jobs (main jobs)
echo   - Indeed_Jobs (indeed jobs)
echo   - Deloitte_Jobs (Deloitte-specific)
echo.

:end
echo ========================================================================
echo Press any key to exit...
pause >nul
