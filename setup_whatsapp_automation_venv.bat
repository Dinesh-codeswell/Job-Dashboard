@echo off
REM ============================================================================
REM WhatsApp Job Notification Automation - Setup Script (Virtual Environment)
REM ============================================================================
REM This script sets up Windows Task Scheduler to run WhatsApp notifications
REM every 30 minutes using the virtual environment.
REM
REM REQUIREMENTS:
REM - Run as Administrator
REM - Virtual environment created (venv folder exists)
REM - Twilio installed in venv
REM - WhatsApp API credentials configured in .env
REM ============================================================================

echo.
echo ============================================================================
echo WhatsApp Job Notification Automation - Setup (Virtual Environment)
echo ============================================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1/5] Checking virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please create it first: py -m venv venv
    pause
    exit /b 1
)
echo OK - Virtual environment found
echo.

echo [2/5] Checking Twilio installation...
venv\Scripts\python.exe -c "import twilio" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Twilio not installed in virtual environment
    echo Please install: pip install twilio
    pause
    exit /b 1
)
echo OK - Twilio installed
echo.

echo [3/5] Checking configuration...
if not exist ".env" (
    echo WARNING: .env file not found
    echo Please create .env file with WhatsApp API credentials
    pause
)
echo OK - Configuration found
echo.

echo [4/5] Creating Windows Task Scheduler task...
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=%SCRIPT_DIR%venv\Scripts\python.exe
set SCRIPT_PATH=%SCRIPT_DIR%whatsapp_notifier.py

REM Delete existing task if it exists
schtasks /query /tn "WhatsAppJobNotifier" >nul 2>&1
if %errorLevel% equ 0 (
    echo Deleting existing task...
    schtasks /delete /tn "WhatsAppJobNotifier" /f >nul 2>&1
)

REM Create new task (runs every 30 minutes)
schtasks /create ^
    /tn "WhatsAppJobNotifier" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /sc minute ^
    /mo 30 ^
    /st 00:00 ^
    /ru SYSTEM ^
    /rl HIGHEST ^
    /f

if %errorLevel% neq 0 (
    echo ERROR: Failed to create scheduled task
    pause
    exit /b 1
)

echo OK - Task created successfully
echo.

echo [5/5] Verifying task...
schtasks /query /tn "WhatsAppJobNotifier" /fo LIST
echo.

echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo.
echo Task Name: WhatsAppJobNotifier
echo Schedule: Every 30 minutes
echo Python: %PYTHON_PATH%
echo Script: %SCRIPT_PATH%
echo.
echo NEXT STEPS:
echo 1. Verify Auth Token is in .env file
echo 2. Test manually: venv\Scripts\python whatsapp_notifier.py --test
echo 3. Check logs: logs\whatsapp_notifications_YYYY_MM_DD.log
echo 4. Manage task: whatsapp_manager.bat
echo.
echo ============================================================================
pause
