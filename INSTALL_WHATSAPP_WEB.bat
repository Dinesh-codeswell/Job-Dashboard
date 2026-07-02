@echo off
REM ============================================================================
REM Install WhatsApp Web Dependencies
REM ============================================================================

echo.
echo ============================================================================
echo   Installing WhatsApp Web Dependencies
echo ============================================================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found!
    echo Please run setup first or create venv manually
    pause
    exit /b 1
)

echo.
echo [INFO] Installing WhatsApp Web dependencies...
echo.

pip install -r requirements_whatsapp.txt

if %errorLevel% equ 0 (
    echo.
    echo ============================================================================
    echo   ✅ SUCCESS! WhatsApp Web dependencies installed
    echo ============================================================================
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
