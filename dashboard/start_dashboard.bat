@echo off
REM ================================================================================
REM                    Consulting Jobs Dashboard - Startup Script
REM ================================================================================

echo.
echo ================================================================================
echo                    Consulting Jobs Dashboard - India
echo ================================================================================
echo.

REM Set Python path explicitly
set PYTHON_CMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe

REM Check if Python exists
if not exist "%PYTHON_CMD%" (
    echo ERROR: Python not found at: %PYTHON_CMD%
    echo Please install Python 3.8+ or update the path in this script
    pause
    exit /b 1
)

echo Using Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM Check if we're in the dashboard directory
if not exist "app.py" (
    echo Changing to dashboard directory...
    cd /d "%~dp0"
)

REM Check if credentials exist
if not exist "..\credentials.json" (
    echo.
    echo WARNING: credentials.json not found in parent directory
    echo Please ensure Google Sheets credentials are set up
    echo.
)

REM Check if .env exists
if not exist ".env" (
    echo.
    echo Creating .env from .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo Please edit .env and add your GOOGLE_SHEET_ID
        echo.
        pause
    )
)

echo.
echo Starting Dashboard Server...
echo.
echo ================================================================================
echo  Dashboard will be available at: http://localhost:5000
echo  API Health Check: http://localhost:5000/api/health
echo ================================================================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask server
%PYTHON_CMD% app.py

pause
