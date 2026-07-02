@echo off
REM ========================================================================
REM WhatsApp Web Group Notifier - Automated Setup
REM Runs every 30 minutes to send new jobs to WhatsApp group
REM ========================================================================

echo.
echo ========================================================================
echo   SETTING UP WHATSAPP WEB GROUP NOTIFIER (Every 30 Minutes)
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
set PYTHON_SCRIPT=%SCRIPT_DIR%whatsapp_web_notifier.py

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

REM Check if .env has group name configured
findstr /C:"WHATSAPP_GROUP_NAME=" .env | findstr /V /C:"WHATSAPP_GROUP_NAME=$" >nul
if %errorLevel% neq 0 (
    echo [ERROR] WHATSAPP_GROUP_NAME not set in .env file!
    echo.
    echo Please edit .env and add your WhatsApp group name:
    echo WHATSAPP_GROUP_NAME=Your Group Name Here
    echo.
    pause
    exit /b 1
)

echo [INFO] WhatsApp group name configured...
echo.

REM Task name
set TASK_NAME=WhatsAppWebGroupNotifier

echo ========================================================================
echo   CONFIGURATION
echo ========================================================================
echo.
echo Task Name: %TASK_NAME%
echo Schedule: Every 30 minutes
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

REM Create the scheduled task (every 30 minutes)
echo [INFO] Creating scheduled task...
echo.

schtasks /create /tn "%TASK_NAME%" /tr "cmd.exe /c \"cd /d \"%SCRIPT_DIR%\" && \"%PYTHON_PATH%\" \"%PYTHON_SCRIPT%\"\"" /sc minute /mo 30 /ru SYSTEM /f

if %errorLevel% equ 0 (
    echo.
    echo ========================================================================
    echo   ✅ SUCCESS! WhatsApp Web automation is now scheduled
    echo ========================================================================
    echo.
    echo The notifier will run automatically every 30 minutes.
    echo Each run will:
    echo   1. Fetch new jobs from Google Sheets
    echo   2. Filter for tier 1 and tier 2 companies only
    echo   3. Send to your WhatsApp group (appears as YOU)
    echo   4. Track sent jobs to avoid duplicates
    echo.
    echo 📊 View logs in: %SCRIPT_DIR%logs\
    echo 📝 Log files are named: whatsapp_web_YYYY_MM_DD.log
    echo.
    echo IMPORTANT - FIRST RUN:
    echo   1. Run manually first: python whatsapp_web_notifier.py --test
    echo   2. Scan QR code when browser opens
    echo   3. Session will be saved for future runs
    echo   4. Subsequent runs will NOT require QR scan
    echo.
    echo To manage automation:
    echo   Check status:   whatsapp_web_manager.bat status
    echo   Stop:           whatsapp_web_manager.bat stop
    echo   Start:          whatsapp_web_manager.bat start
    echo   Test:           whatsapp_web_manager.bat test
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
