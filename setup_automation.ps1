# ========================================================================
# PowerShell Setup: 2-Hour Automation
# Run this as Administrator
# ========================================================================

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  SETTING UP 2-HOUR AUTOMATION" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] Must run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as administrator'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[INFO] Administrator privileges confirmed" -ForegroundColor Green
Write-Host ""

# Configuration
$TASK_NAME = "LinkedInJobsScraper_Auto"
$SCRIPT_DIR = $PSScriptRoot
$PYTHON_PATH = "C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe"
$PYTHON_SCRIPT = Join-Path $SCRIPT_DIR "run_scraper_and_sync.py"

# Verify Python exists
if (-not (Test-Path $PYTHON_PATH)) {
    Write-Host "[ERROR] Python not found at: $PYTHON_PATH" -ForegroundColor Red
    Write-Host "Please update PYTHON_PATH in this script" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[INFO] Python found: $PYTHON_PATH" -ForegroundColor Green
Write-Host "[INFO] Script: $PYTHON_SCRIPT" -ForegroundColor Green
Write-Host ""

# Delete existing task if present
Write-Host "[INFO] Removing old task (if exists)..." -ForegroundColor Yellow
schtasks /delete /tn $TASK_NAME /f 2>$null | Out-Null

# Create the command
$command = "cmd.exe"
$arguments = "/c `"cd /d `"$SCRIPT_DIR`" && `"$PYTHON_PATH`" `"$PYTHON_SCRIPT`"`""

Write-Host "[INFO] Creating 2-hour scheduled task..." -ForegroundColor Yellow
Write-Host ""

# Create new task using schtasks
$result = schtasks /create /tn $TASK_NAME /tr "$command $arguments" /sc hourly /mo 2 /ru SYSTEM /f 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host "  SUCCESS! Automation is now scheduled" -ForegroundColor Green
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schedule: Every 2 hours (12 times per day)" -ForegroundColor White
    Write-Host ""
    Write-Host "Run times:" -ForegroundColor White
    Write-Host "  12 AM, 2 AM, 4 AM, 6 AM, 8 AM, 10 AM" -ForegroundColor Gray
    Write-Host "  12 PM, 2 PM, 4 PM, 6 PM, 8 PM, 10 PM" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  scraper-status    - Check status" -ForegroundColor Gray
    Write-Host "  scraper-logs      - View logs" -ForegroundColor Gray
    Write-Host "  scraper-stop      - Stop automation" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next run:" -ForegroundColor White
    $taskInfo = schtasks /query /tn $TASK_NAME /fo LIST | Select-String "Next Run Time"
    Write-Host "  $taskInfo" -ForegroundColor Gray
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host "  FAILED to create task" -ForegroundColor Red
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error output:" -ForegroundColor Yellow
    Write-Host $result -ForegroundColor Gray
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Make sure you ran PowerShell as Administrator" -ForegroundColor White
    Write-Host "2. Check Python path is correct: $PYTHON_PATH" -ForegroundColor White
    Write-Host "3. Try using Task Scheduler GUI (see FIX_SETUP_ERROR.md)" -ForegroundColor White
    Write-Host ""
}

Read-Host "Press Enter to exit"
