# Installer - Adds scraper automation to PowerShell profile
# Run this ONCE to make commands permanently available

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  🔧 INSTALLING JOB SCRAPER POWERSHELL COMMANDS" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

$profilePath = $PROFILE
$scriptPath = "$PSScriptRoot\automation_tools.ps1"

Write-Host "📍 PowerShell Profile: $profilePath" -ForegroundColor White
Write-Host "📍 Script Location: $scriptPath" -ForegroundColor White
Write-Host ""

# Check if profile exists
if (-not (Test-Path $profilePath)) {
    Write-Host "ℹ️  Creating PowerShell profile..." -ForegroundColor Yellow
    New-Item -ItemType File -Path $profilePath -Force | Out-Null
    Write-Host "✅ Profile created" -ForegroundColor Green
}

# Check if already installed
$profileContent = Get-Content $profilePath -ErrorAction SilentlyContinue
if ($profileContent -match "automation_tools\.ps1") {
    Write-Host "⚠️  Commands already installed!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To reinstall, remove this line from your profile:" -ForegroundColor White
    Write-Host "  . `$PSScriptRoot\automation_tools.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Then run this installer again." -ForegroundColor White
    pause
    exit
}

# Add to profile
Write-Host "📝 Adding commands to PowerShell profile..." -ForegroundColor Yellow
Write-Host ""

$installLine = @"

# Job Scraper Automation Tools
. "$scriptPath"
"@

Add-Content -Path $profilePath -Value $installLine

Write-Host "✅ Commands installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  AVAILABLE COMMANDS (in any PowerShell window)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  scraper              - Show interactive menu" -ForegroundColor White
Write-Host "  scraper-status       - Check automation status" -ForegroundColor White
Write-Host "  scraper-start        - Start automation (requires Admin)" -ForegroundColor White
Write-Host "  scraper-stop         - Stop automation" -ForegroundColor White
Write-Host "  scraper-restart      - Restart automation" -ForegroundColor White
Write-Host "  scraper-logs         - View recent logs" -ForegroundColor White
Write-Host "  scraper-run          - Run scraper manually" -ForegroundColor White
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 To start using these commands:" -ForegroundColor Green
Write-Host ""
Write-Host "  1. Close this PowerShell window" -ForegroundColor White
Write-Host "  2. Open a NEW PowerShell window" -ForegroundColor White
Write-Host "  3. Type: scraper" -ForegroundColor White
Write-Host ""
Write-Host "Or use them right now by running:" -ForegroundColor Yellow
Write-Host "  . $scriptPath" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

pause
