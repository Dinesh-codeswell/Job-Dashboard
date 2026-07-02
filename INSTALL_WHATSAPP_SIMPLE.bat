@echo off
REM ============================================================================
REM Install WhatsApp Web Dependencies - Simple Version
REM ============================================================================

echo.
echo ============================================================================
echo   Installing WhatsApp Web Dependencies (Simple)
echo ============================================================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found, using global Python
)

echo.
echo [INFO] Installing minimal dependencies for WhatsApp Web...
echo.

REM Install only what's needed for WhatsApp Web
pip install python-dotenv requests gspread google-auth selenium webdriver-manager

if %errorLevel% equ 0 (
    echo.
    echo ============================================================================
    echo   ✅ SUCCESS! WhatsApp Web dependencies installed
    echo ============================================================================
    echo.
    echo Installed packages:
    echo   - python-dotenv (for .env file)
    echo   - requests (for HTTP requests)
    echo   - gspread (for Google Sheets)
    echo   - google-auth (for Google authentication)
    echo   - selenium (for WhatsApp Web automation)
    echo   - webdriver-manager (for Chrome driver)
    echo.
    echo Next steps:
    echo   1. Edit .env and add: WHATSAPP_GROUP_NAME=Your Group Name
    echo   2. Run: python whatsapp_web_notifier.py --test
    echo   3. Scan QR code when browser opens
    echo   4. Run: setup_whatsapp_web_automation.bat (as administrator)
    echo.
    echo See WHATSAPP_WEB_QUICK_START.md for detailed instructions
    echo.
) else (
    echo.
    echo ============================================================================
    echo   ❌ FAILED to install dependencies
    echo ============================================================================
    echo.
    echo Please check the error message above and try again.
    echo.
)

pause
