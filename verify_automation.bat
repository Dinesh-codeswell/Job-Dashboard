@echo off
REM ========================================================================
REM Pre-Setup Verification - Check if everything is ready for automation
REM ========================================================================

set SCRIPT_DIR=%~dp0
set PYTHON_PATH=C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe
set ERRORS=0

echo.
echo ========================================================================
echo   🔍 AUTOMATION SETUP VERIFICATION
echo ========================================================================
echo.

REM Check Python
echo [1/7] Checking Python installation...
if exist "%PYTHON_PATH%" (
    echo     ✅ Python found at: %PYTHON_PATH%
    "%PYTHON_PATH%" --version
) else (
    echo     ❌ Python NOT found at: %PYTHON_PATH%
    echo     Please update PYTHON_PATH in setup_automation.bat
    set /a ERRORS+=1
)
echo.

REM Check .env file
echo [2/7] Checking .env file...
if exist "%SCRIPT_DIR%.env" (
    echo     ✅ .env file exists
) else (
    echo     ❌ .env file NOT found
    echo     → Copy .env.example to .env and configure
    set /a ERRORS+=1
)
echo.

REM Check credentials.json
echo [3/7] Checking Google Sheets credentials...
if exist "%SCRIPT_DIR%credentials.json" (
    echo     ✅ credentials.json exists
) else (
    echo     ⚠️  credentials.json NOT found
    echo     → Required for Google Sheets integration
    set /a ERRORS+=1
)
echo.

REM Check LinkedIn session
echo [4/7] Checking LinkedIn session...
if exist "%SCRIPT_DIR%linkedin_session.json" (
    echo     ✅ linkedin_session.json exists
) else (
    echo     ⚠️  linkedin_session.json NOT found
    echo     → LinkedIn scraping will fail
    echo     → Run: "%PYTHON_PATH%" samples\create_session.py
    set /a ERRORS+=1
)
echo.

REM Check main scraper
echo [5/7] Checking main scraper script...
if exist "%SCRIPT_DIR%scrape_all_india_jobs.py" (
    echo     ✅ scrape_all_india_jobs.py exists
) else (
    echo     ❌ scrape_all_india_jobs.py NOT found
    set /a ERRORS+=1
)
echo.

REM Check auto_scraper
echo [6/7] Checking automated runner...
if exist "%SCRIPT_DIR%auto_scraper.py" (
    echo     ✅ auto_scraper.py exists
) else (
    echo     ❌ auto_scraper.py NOT found
    set /a ERRORS+=1
)
echo.

REM Check logs directory
echo [7/7] Checking logs directory...
if exist "%SCRIPT_DIR%logs" (
    echo     ✅ logs/ directory exists
) else (
    echo     ℹ️  logs/ directory not found (will be created on first run)
)
echo.

REM Summary
echo ========================================================================
if %ERRORS%==0 (
    echo   ✅ ALL CHECKS PASSED! Ready to setup automation
    echo.
    echo   Next step: Right-click setup_automation.bat → Run as administrator
) else (
    echo   ⚠️  Found %ERRORS% issue(s) that need attention
    echo.
    echo   Please fix the issues above before running setup_automation.bat
)
echo ========================================================================
echo.

pause
