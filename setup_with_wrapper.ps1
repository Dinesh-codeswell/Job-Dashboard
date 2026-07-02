# ========================================================================
# Simple Setup Using Wrapper Script
# This avoids complex quote escaping issues
# ========================================================================

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  SETTING UP 2-HOUR AUTOMATION (Simple Method)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] Must run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Steps:" -ForegroundColor Yellow
    Write-Host "1. Close this window" -ForegroundColor White
    Write-Host "2. Right-click PowerShell" -ForegroundColor White
    Write-Host "3. Select 'Run as administrator'" -ForegroundColor White
    Write-Host "4. Run this script again" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[INFO] Administrator privileges confirmed" -ForegroundColor Green
Write-Host ""

# Configuration
$TASK_NAME = "LinkedInJobsScraper_Auto"
$SCRIPT_DIR = $PSScriptRoot
$WRAPPER_SCRIPT = Join-Path $SCRIPT_DIR "run_automation.bat"

# Verify wrapper exists
if (-not (Test-Path $WRAPPER_SCRIPT)) {
    Write-Host "[ERROR] Wrapper script not found: $WRAPPER_SCRIPT" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[INFO] Wrapper script: $WRAPPER_SCRIPT" -ForegroundColor Green
Write-Host ""

# Delete existing task
Write-Host "[INFO] Removing old task (if exists)..." -ForegroundColor Yellow
schtasks /delete /tn $TASK_NAME /f 2>$null | Out-Null

# Create new task (much simpler with wrapper)
Write-Host "[INFO] Creating 2-hour scheduled task..." -ForegroundColor Yellow

$createResult = schtasks /create /tn $TASK_NAME /tr "`"$WRAPPER_SCRIPT`"" /sc hourly /mo 2 /ru SYSTEM /f 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host "  ✅ SUCCESS! Automation is now scheduled" -ForegroundColor Green
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schedule: Every 2 hours (12 times per day)" -ForegroundColor White
    Write-Host ""
    Write-Host "Run times:" -ForegroundColor Cyan
    Write-Host "  12 AM → 2 AM → 4 AM → 6 AM → 8 AM → 10 AM" -ForegroundColor Gray
    Write-Host "  12 PM → 2 PM → 4 PM → 6 PM → 8 PM → 10 PM" -ForegroundColor Gray
    Write-Host ""
    Write-Host "What happens each run:" -ForegroundColor Cyan
    Write-Host "  1. Scrapes 100 jobs (80 LinkedIn, 20 Indeed)" -ForegroundColor Gray
    Write-Host "  2. Uploads to Google Sheets" -ForegroundColor Gray
    Write-Host "  3. Syncs to Supabase" -ForegroundColor Gray
    Write-Host "  4. Deletes jobs older than 3 days" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Cyan
    Write-Host "  scraper-status    - Check status" -ForegroundColor Gray
    Write-Host "  scraper-logs      - View logs" -ForegroundColor Gray
    Write-Host "  scraper-stop      - Stop automation" -ForegroundColor Gray
    Write-Host "  scraper-restart   - Restart automation" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next run:" -ForegroundColor Cyan
    $nextRun = schtasks /query /tn $TASK_NAME /fo LIST | Select-String "Next Run Time"
    if ($nextRun) {
        Write-Host "  $nextRun" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "Logs location:" -ForegroundColor Cyan
    Write-Host "  $SCRIPT_DIR\logs\" -ForegroundColor Gray
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Setup complete! Your automation is now running." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host "  ❌ FAILED to create task" -ForegroundColor Red
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error:" -ForegroundColor Yellow
    Write-Host $createResult -ForegroundColor Gray
    Write-Host ""
    Write-Host "Alternative: Use Task Scheduler GUI" -ForegroundColor Yellow
    Write-Host "1. Press Win + R" -ForegroundColor White
    Write-Host "2. Type: taskschd.msc" -ForegroundColor White
    Write-Host "3. Follow steps in FIX_SETUP_ERROR.md" -ForegroundColor White
    Write-Host ""
}

Read-Host "Press Enter to exit"
