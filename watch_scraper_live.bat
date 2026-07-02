@echo off
REM Live Scraper Monitor - Shows real-time updates
setlocal enabledelayedexpansion

echo ========================================================================
echo LIVE SCRAPER MONITOR
echo ========================================================================
echo This will refresh every 10 seconds. Press Ctrl+C to stop.
echo ========================================================================
echo.

:loop
cls
echo ========================================================================
echo LIVE SCRAPER MONITOR - %date% %time%
echo ========================================================================
echo.

echo [TASK STATUS]
echo ----------------------------------------
schtasks /query /tn "LinkedInJobsScraper_Auto" /fo LIST 2>nul | findstr /C:"Status" /C:"Next Run Time" /C:"Last Run Time" /C:"Last Result"

echo.
echo [LATEST LOG ACTIVITY - Last 15 lines]
echo ----------------------------------------
if exist "logs\scraper_*.log" (
    for /f "delims=" %%f in ('dir /b /od logs\scraper_*.log') do set "latest=%%f"
    powershell -Command "Get-Content 'logs\!latest!' -Tail 15 | ForEach-Object { $_ }"
) else (
    echo No logs found yet.
)

echo.
echo ========================================================================
echo Refreshing in 10 seconds... (Press Ctrl+C to stop)
echo ========================================================================
timeout /t 10 /nobreak >nul
goto :loop
