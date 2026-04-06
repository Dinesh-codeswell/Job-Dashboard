@echo off
REM ========================================================================
REM Automation Manager - Start/Stop/Status for Automated Job Scraper
REM ========================================================================

setlocal enabledelayedexpansion

set TASK_NAME=LinkedInJobsScraper_Auto
set SCRIPT_DIR=%~dp0
set PYTHON_PATH=C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM If no argument provided, show menu
if "%1"=="" goto :menu

REM Process argument
if /i "%1"=="start" goto :start
if /i "%1"=="stop" goto :stop
if /i "%1"=="status" goto :status
if /i "%1"=="restart" goto :restart
if /i "%1"=="logs" goto :logs
if /i "%1"=="help" goto :help

echo Unknown command: %1
echo.
goto :help

:menu
echo.
echo ========================================================================
echo   AUTOMATED JOB SCRAPER - MANAGEMENT MENU
echo ========================================================================
echo.
echo What would you like to do?
echo.
echo   1. Start automation (run every 15 minutes)
echo   2. Stop automation
echo   3. Check status
echo   4. Restart automation
echo   5. View recent logs
echo   6. Run scraper manually (one-time)
echo   7. Help
echo   0. Exit
echo.
set /p choice="Enter your choice (0-7): "

if "%choice%"=="1" goto :start
if "%choice%"=="2" goto :stop
if "%choice%"=="3" goto :status
if "%choice%"=="4" goto :restart
if "%choice%"=="5" goto :logs
if "%choice%"=="6" goto :manual
if "%choice%"=="7" goto :help
if "%choice%"=="0" exit /b

echo Invalid choice.
pause
exit /b

:start
echo.
echo ========================================================================
echo   STARTING AUTOMATION
echo ========================================================================
echo.

schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo [INFO] Task already exists. Verifying configuration...
    echo.
) else (
    echo [INFO] Task not found. Running setup...
    echo.
    call "%SCRIPT_DIR%setup_automation.bat"
    exit /b
)

REM Verify task is enabled
schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr /i "Status" | findstr /i "Disabled" >nul
if %errorLevel% equ 0 (
    echo [INFO] Task is disabled. Enabling...
    schtasks /change /tn "%TASK_NAME%" /enable
)

echo.
echo ✅ Automation is now ACTIVE
echo.
echo The scraper will run every 15 minutes automatically.
echo.
schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr "Next Run Time"
echo.
pause
exit /b

:stop
echo.
echo ========================================================================
echo   STOPPING AUTOMATION
echo ========================================================================
echo.

schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] No automated task found. Nothing to stop.
    pause
    exit /b
)

echo [INFO] Disabling scheduled task...
schtasks /change /tn "%TASK_NAME%" /disable

echo.
echo ✅ Automation has been STOPPED
echo.
echo The scraper will no longer run automatically.
echo To restart: automation_manager.bat start
echo.
pause
exit /b

:status
echo.
echo ========================================================================
echo   AUTOMATION STATUS
echo ========================================================================
echo.

schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo [STATUS] ❌ Automated task not found
    echo.
    echo Automation is not set up yet.
    echo Run: setup_automation.bat
    echo.
    pause
    exit /b
)

echo [STATUS] Automated Task Details:
echo ----------------------------------------
schtasks /query /tn "%TASK_NAME%" /fo LIST
echo ----------------------------------------
echo.

REM Check if task is enabled or disabled
schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr /i "Status" | findstr /i "Disabled" >nul
if %errorLevel% equ 0 (
    echo [STATUS] ⚠️  Task is DISABLED
    echo.
    echo To enable: automation_manager.bat start
) else (
    echo [STATUS] ✅ Task is ENABLED
    echo.
    echo Next scheduled run:
    schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr "Next Run Time"
)

echo.

REM Show recent logs
set LOG_DIR=%SCRIPT_DIR%logs
if exist "%LOG_DIR%" (
    echo Recent Activity:
    echo ----------------------------------------
    dir /b /o-d "%LOG_DIR%\scraper_*.log" 2>nul | head -n 1 > temp_log.txt
    set /p LATEST_LOG=<temp_log.txt
    del temp_log.txt
    
    if defined LATEST_LOG (
        echo Latest log file: %LATEST_LOG%
        echo.
        echo Last 10 entries:
        powershell -Command "Get-Content '%LOG_DIR%\%LATEST_LOG%' -Tail 10" 2>nul
    ) else (
        echo No log files found yet.
    )
    echo ----------------------------------------
)

echo.
pause
exit /b

:restart
echo.
echo ========================================================================
echo   RESTARTING AUTOMATION
echo ========================================================================
echo.

echo [INFO] Stopping current task...
schtasks /end /tn "%TASK_NAME%" >nul 2>&1
schtasks /change /tn "%TASK_NAME%" /disable >nul 2>&1

timeout /t 2 /nobreak >nul

echo [INFO] Starting task...
schtasks /change /tn "%TASK_NAME%" /enable >nul 2>&1

echo.
echo ✅ Automation has been RESTARTED
echo.
schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr "Next Run Time"
echo.
pause
exit /b

:logs
echo.
echo ========================================================================
echo   VIEWING RECENT LOGS
echo ========================================================================
echo.

set LOG_DIR=%SCRIPT_DIR%logs
if not exist "%LOG_DIR%" (
    echo [INFO] No logs directory found. The scraper hasn't run yet.
    pause
    exit /b
)

echo Available log files:
echo ----------------------------------------
dir /b /o-d "%LOG_DIR%\scraper_*.log" 2>nul
echo ----------------------------------------
echo.

dir /b /o-d "%LOG_DIR%\scraper_*.log" 2>nul | head -n 1 > temp_log.txt
set /p LATEST_LOG=<temp_log.txt
del temp_log.txt

if defined LATEST_LOG (
    echo Showing latest log: %LATEST_LOG%
    echo ========================================================================
    type "%LOG_DIR%\%LATEST_LOG%"
    echo ========================================================================
) else (
    echo [INFO] No log files found.
)

echo.
pause
exit /b

:manual
echo.
echo ========================================================================
echo   RUNNING SCRAPER MANUALLY (ONE-TIME)
echo ========================================================================
echo.

echo [INFO] This will run the scraper immediately (not wait for schedule)
echo.
set /p confirm="Continue? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit /b
)

echo.
echo [INFO] Starting scraper...
echo.

cd /d "%SCRIPT_DIR%"
"%PYTHON_PATH%" auto_scraper.py

echo.
echo Manual run completed.
echo.
pause
exit /b

:help
echo.
echo ========================================================================
echo   AUTOMATION HELP
echo ========================================================================
echo.
echo USAGE:
echo   automation_manager.bat [command]
echo.
echo COMMANDS:
echo   start     - Enable automation (run every 15 minutes)
echo   stop      - Disable automation
echo   status    - Check current status and next run time
echo   restart   - Restart the automation schedule
echo   logs      - View recent log files
echo   help      - Show this help message
echo.
echo EXAMPLES:
echo   automation_manager.bat start
echo   automation_manager.bat status
echo   automation_manager.bat logs
echo.
echo FILES:
echo   setup_automation.bat    - Initial setup script (run once)
echo   automation_manager.bat  - Management script (this file)
echo   auto_scraper.py         - The actual scraper runner
echo   logs/                   - Log files directory
echo.
echo NOTES:
echo   - Requires Administrator privileges
echo   - Runs as SYSTEM user for reliability
echo   - Logs are saved in the logs/ directory
echo   - Each day gets a new log file
echo.
pause
exit /b
