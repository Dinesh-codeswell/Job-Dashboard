@echo off
REM ============================================================================
REM WhatsApp Web Group Notifier - Management Script
REM ============================================================================
REM Quick commands to manage WhatsApp Web automation
REM ============================================================================

setlocal enabledelayedexpansion

if "%1"=="" goto menu

REM Command-line mode
if /i "%1"=="status" goto status
if /i "%1"=="start" goto start
if /i "%1"=="stop" goto stop
if /i "%1"=="restart" goto restart
if /i "%1"=="logs" goto logs
if /i "%1"=="test" goto test
if /i "%1"=="force" goto force
if /i "%1"=="run" goto run
goto help

:menu
cls
echo.
echo ============================================================================
echo WhatsApp Web Group Notifier - Management Menu
echo ============================================================================
echo.
echo 1. Check Status
echo 2. Start Automation
echo 3. Stop Automation
echo 4. Restart Automation
echo 5. View Logs
echo 6. Test (Dry Run)
echo 7. Force Send All Jobs
echo 8. Run Now (Manual)
echo 9. Exit
echo.
set /p choice="Select option (1-9): "

if "%choice%"=="1" goto status
if "%choice%"=="2" goto start
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto restart
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto test
if "%choice%"=="7" goto force
if "%choice%"=="8" goto run
if "%choice%"=="9" goto end
goto menu

:status
echo.
echo ============================================================================
echo Task Status
echo ============================================================================
schtasks /query /tn "WhatsAppWebGroupNotifier" /fo LIST 2>nul
if %errorLevel% neq 0 (
    echo ERROR: Task not found
    echo Run setup_whatsapp_web_automation.bat to create the task
) else (
    echo.
    echo Last Run:
    for /f "tokens=2 delims=:" %%a in ('schtasks /query /tn "WhatsAppWebGroupNotifier" /fo LIST ^| findstr /C:"Last Run Time"') do echo %%a
    echo.
    echo Next Run:
    for /f "tokens=2 delims=:" %%a in ('schtasks /query /tn "WhatsAppWebGroupNotifier" /fo LIST ^| findstr /C:"Next Run Time"') do echo %%a
    echo.
    echo Sent Jobs Tracking:
    if exist "sent_jobs_web.json" (
        for /f "tokens=*" %%a in ('powershell -Command "(Get-Content sent_jobs_web.json | ConvertFrom-Json).sent_jobs.Count"') do echo Total jobs tracked: %%a
    ) else (
        echo No tracking file found yet
    )
)
echo.
if "%1"=="" pause
goto end

:start
echo.
echo Starting WhatsApp Web automation...
schtasks /change /tn "WhatsAppWebGroupNotifier" /enable >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Failed to start task
    echo Make sure you've run setup_whatsapp_web_automation.bat first
) else (
    echo OK - Automation started
    echo Task will run every 30 minutes
    echo.
    echo IMPORTANT: Make sure you've done the first manual run
    echo to scan QR code and save session!
)
echo.
if "%1"=="" pause
goto end

:stop
echo.
echo Stopping WhatsApp Web automation...
schtasks /change /tn "WhatsAppWebGroupNotifier" /disable >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Failed to stop task
) else (
    echo OK - Automation stopped
)
echo.
if "%1"=="" pause
goto end

:restart
echo.
echo Restarting WhatsApp Web automation...
schtasks /change /tn "WhatsAppWebGroupNotifier" /disable >nul 2>&1
timeout /t 2 /nobreak >nul
schtasks /change /tn "WhatsAppWebGroupNotifier" /enable >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Failed to restart task
) else (
    echo OK - Automation restarted
)
echo.
if "%1"=="" pause
goto end

:logs
echo.
echo ============================================================================
echo Recent Logs (Last 50 lines)
echo ============================================================================
echo.
for /f %%i in ('dir /b /o-d logs\whatsapp_web_*.log 2^>nul') do (
    set LATEST_LOG=logs\%%i
    goto show_log
)
echo No log files found
goto log_end

:show_log
if exist "%LATEST_LOG%" (
    echo File: %LATEST_LOG%
    echo.
    powershell -Command "Get-Content '%LATEST_LOG%' -Tail 50"
) else (
    echo No log files found
)

:log_end
echo.
if "%1"=="" pause
goto end

:test
echo.
echo ============================================================================
echo Test Mode (Dry Run)
echo ============================================================================
echo.
echo Running WhatsApp Web notifier in test mode...
echo No actual messages will be sent.
echo Browser will open for QR scan if needed.
echo.
python whatsapp_web_notifier.py --test
echo.
if "%1"=="" pause
goto end

:force
echo.
echo ============================================================================
echo Force Send All Jobs
echo ============================================================================
echo.
echo WARNING: This will send ALL jobs from Google Sheets
echo This will ignore the sent job history
echo.
set /p confirm="Are you sure? (yes/no): "
if /i not "%confirm%"=="yes" (
    echo Cancelled
    goto end
)
echo.
echo Running WhatsApp Web notifier in force mode...
echo Browser will open...
python whatsapp_web_notifier.py --force
echo.
if "%1"=="" pause
goto end

:run
echo.
echo ============================================================================
echo Manual Run
echo ============================================================================
echo.
echo Running WhatsApp Web notifier now...
echo Browser will open...
python whatsapp_web_notifier.py
echo.
if "%1"=="" pause
goto end

:help
echo.
echo Usage: whatsapp_web_manager.bat [command]
echo.
echo Commands:
echo   status    - Check task status and tracking info
echo   start     - Start automation
echo   stop      - Stop automation
echo   restart   - Restart automation
echo   logs      - View recent logs
echo   test      - Test mode (dry run, browser opens)
echo   force     - Force send all jobs
echo   run       - Run now manually
echo.
echo Run without arguments for interactive menu
echo.
goto end

:end
endlocal
