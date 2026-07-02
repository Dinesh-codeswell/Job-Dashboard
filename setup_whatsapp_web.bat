@echo off
REM WhatsApp Web Automation Setup Script
REM =====================================

echo.
echo ========================================
echo WhatsApp Web Automation Setup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create it first: py -m venv venv
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo [2/3] Installing Selenium and WebDriver Manager...
pip install selenium webdriver-manager

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to install dependencies!
    echo.
    pause
    exit /b 1
)

REM Check if group name is set
echo.
echo [3/3] Checking configuration...
findstr /C:"WHATSAPP_GROUP_NAME=" .env > nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: WHATSAPP_GROUP_NAME not found in .env
    echo Please add your group name to .env file
    echo.
) else (
    findstr /C:"WHATSAPP_GROUP_NAME=$" .env > nul
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo WARNING: WHATSAPP_GROUP_NAME is empty in .env
        echo Please add your group name to .env file
        echo.
    ) else (
        echo Group name configured!
    )
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Add your WhatsApp group name to .env file
echo    Example: WHATSAPP_GROUP_NAME=Job Opportunities Team
echo.
echo 2. Test the setup:
echo    python whatsapp_web_notifier.py --test
echo.
echo 3. First run will require QR code scan
echo.
echo 4. See WHATSAPP_WEB_SETUP.md for full guide
echo.
pause
