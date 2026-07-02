@echo off
REM ========================================================================
REM Simple Setup: 2-Hour Automation (No Multi-line Commands)
REM ========================================================================

echo.
echo ========================================================================
echo   SETTING UP 2-HOUR AUTOMATION
echo ========================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Must run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo [INFO] Administrator privileges confirmed
echo.

REM Configuration
set TASK_NAME=LinkedInJobsScraper_Auto
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe
set PYTHON_SCRIPT=%SCRIPT_DIR%run_scraper_and_sync.py

REM Verify Python exists
if not exist "%PYTHON_PATH%" (
    echo [ERROR] Python not found at: %PYTHON_PATH%
    echo Please update PYTHON_PATH in this script
    pause
    exit /b 1
)

echo [INFO] Python found: %PYTHON_PATH%
echo [INFO] Script: %PYTHON_SCRIPT%
echo.

REM Delete existing task if present
echo [INFO] Removing old task (if exists)...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create new task (single line command)
echo [INFO] Creating 2-hour scheduled task...
schtasks /create /tn "%TASK_NAME%" /tr "cmd.exe /c \"cd /d \"%SCRIPT_DIR%\" && \"%PYTHON_PATH%\" \"%PYTHON_SCRIPT%\"\"" /sc hourly /mo 2 /ru SYSTEM /f

if %errorLevel% equ 0 (
    echo.
    echo ========================================================================
    echo   SUCCESS! Automation is now scheduled
    echo ========================================================================
    echo.
    echo Schedule: Every 2 hours (12 times per day)
    echo.
    echo Run times:
    echo   12 AM, 2 AM, 4 AM, 6 AM, 8 AM, 10 AM
    echo   12 PM, 2 PM, 4 PM, 6 PM, 8 PM, 10 PM
    echo.
    echo Commands:
    echo   scraper-status    - Check status
    echo   scraper-logs      - View logs
    echo   scraper-stop      - Stop automation
    echo.
    echo Next run:
    schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr "Next Run Time"
    echo.
    echo ========================================================================
) else (
    echo.
    echo ========================================================================
    echo   FAILED to create task
    echo ========================================================================
    echo.
    echo Error code: %errorLevel%
    echo.
    echo Troubleshooting:
    echo 1. Make sure you ran as Administrator
    echo 2. Check Python path is correct
    echo 3. Try running this command manually:
    echo.
    echo schtasks /create /tn "%TASK_NAME%" /tr "cmd.exe /c \"cd /d \"%SCRIPT_DIR%\" && \"%PYTHON_PATH%\" \"%PYTHON_SCRIPT%\"\"" /sc hourly /mo 2 /ru SYSTEM /f
    echo.
)

pause
