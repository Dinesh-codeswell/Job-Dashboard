@echo off
REM ========================================================================
REM Quick Update: Change Automation from 4 Hours to 2 Hours
REM ========================================================================

echo.
echo ========================================================================
echo   UPDATING AUTOMATION: 4 Hours → 2 Hours
echo ========================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo.
    echo Right-click on this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [INFO] Running with administrator privileges...
echo.

set TASK_NAME=LinkedInJobsScraper_Auto

REM Check if task exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Task "%TASK_NAME%" not found!
    echo.
    echo Please run setup_automation.bat first to create the task.
    echo.
    pause
    exit /b 1
)

echo [INFO] Current task found. Checking schedule...
echo.

REM Show current schedule
echo Current Schedule:
schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr "Repeat:"
echo.

echo [INFO] Updating to 2-hour schedule...
echo.

REM Delete old task
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Get paths
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe
set PYTHON_SCRIPT=%SCRIPT_DIR%run_scraper_and_sync.py

REM Create new task with 2-hour schedule
schtasks /create /tn "%TASK_NAME%" /tr "cmd.exe /c \"cd /d \"%SCRIPT_DIR%\" && \"%PYTHON_PATH%\" \"%PYTHON_SCRIPT%\"\"" /sc hourly /mo 2 /ru SYSTEM /f

if %errorLevel% equ 0 (
    echo.
    echo ========================================================================
    echo   ✅ SUCCESS! Automation updated to 2-hour schedule
    echo ========================================================================
    echo.
    echo New Schedule: Every 2 hours (12 times per day)
    echo.
    echo Run times:
    echo   - 12:00 AM, 2:00 AM, 4:00 AM, 6:00 AM
    echo   - 8:00 AM, 10:00 AM, 12:00 PM, 2:00 PM
    echo   - 4:00 PM, 6:00 PM, 8:00 PM, 10:00 PM
    echo.
    echo Next run:
    schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr "Next Run Time"
    echo.
    echo Verify with: scraper-status
    echo.
    echo ========================================================================
) else (
    echo.
    echo ========================================================================
    echo   ❌ FAILED to update task
    echo ========================================================================
    echo.
    echo Please run setup_automation.bat instead.
    echo.
)

pause

