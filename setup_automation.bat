@echo off
REM ========================================================================
REM Windows Task Scheduler Setup for Automated Job Scraper
REM Runs every 15 minutes without manual intervention
REM ========================================================================

echo.
echo ========================================================================
echo   SETTING UP AUTOMATED JOB SCRAPER (Every 15 Minutes)
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

REM Get the current directory (where this script is located)
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%auto_scraper.py

REM Find Python executable
set PYTHON_PATH=C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe

REM Check if Python is available
if not exist "%PYTHON_PATH%" (
    echo [ERROR] Python not found at: %PYTHON_PATH%
    echo Please update the PYTHON_PATH variable in this script
    pause
    exit /b 1
)

echo [INFO] Python found...
echo.

REM Task name
set TASK_NAME=LinkedInJobsScraper_Auto

echo ========================================================================
echo   CONFIGURATION
echo ========================================================================
echo.
echo Task Name: %TASK_NAME%
echo Schedule: Every 15 minutes
echo Script: %PYTHON_SCRIPT%
echo Working Directory: %SCRIPT_DIR%
echo.

REM Delete existing task if it exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo [INFO] Existing task found. Removing it...
    schtasks /delete /tn "%TASK_NAME%" /f
    echo.
)

REM Create the scheduled task
echo [INFO] Creating scheduled task...
echo.

schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "cmd.exe /c \"cd /d \"%SCRIPT_DIR%\" && %PYTHON_PATH% \"%PYTHON_SCRIPT%\"\"" ^
    /sc minute ^
    /mo 15 ^
    /ru SYSTEM ^
    /f

if %errorLevel% equ 0 (
    echo.
    echo ========================================================================
    echo   ✅ SUCCESS! Automated scraper is now scheduled
    echo ========================================================================
    echo.
    echo The scraper will run automatically every 15 minutes.
    echo.
    echo 📊 View logs in: %SCRIPT_DIR%logs\
    echo 📝 Log files are named: scraper_YYYY_MM_DD.log
    echo.
    echo To check task status:   automation_manager.bat status
    echo To stop automation:     automation_manager.bat stop
    echo To start automation:    automation_manager.bat start
    echo.
    echo Next run times (approximate):
    schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr "Next Run Time"
    echo.
    echo ========================================================================
) else (
    echo.
    echo ========================================================================
    echo   ❌ FAILED to create scheduled task
    echo ========================================================================
    echo.
    echo Please check the error message above and try again.
    echo.
)

pause
