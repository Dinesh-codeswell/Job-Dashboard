@echo off
REM ================================================================================
REM                    Open Terminal with Python in PATH
REM         This script sets up Python PATH and opens a new command prompt
REM ================================================================================

echo.
echo ================================================================================
echo          Setting up Python in PATH for this session...
echo ================================================================================
echo.

REM Set Python PATH for this session
set PYTHON_HOME=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%

echo Python path set to: %PYTHON_HOME%
echo.
echo Testing Python...
python --version

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Python still not found. Please run as Administrator or check installation.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo  SUCCESS! Python is now available in this terminal.
echo ================================================================================
echo.
echo You can now run:
echo   - python app.py (to start dashboard)
echo   - python jobs_to_sheets.py (to scrape jobs)
echo   - python scrape_consulting_india.py (to scrape consulting jobs)
echo.
echo Opening new command prompt with Python in PATH...
echo ================================================================================
echo.

REM Start a new command prompt with the updated environment
start "Python Terminal" cmd /k "PATH=%PATH%; set PYTHON_HOME=%PYTHON_HOME%"

echo.
echo New terminal opened! You can close this window.
pause
