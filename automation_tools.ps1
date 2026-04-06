# PowerShell Helper Functions for Job Scraper Automation
# Add these to your PowerShell profile for permanent access

# Automation management functions
function Start-Scraper {
    Write-Host "🚀 Starting automation..." -ForegroundColor Green
    & "$PSScriptRoot\setup_automation.bat"
}

function Stop-Scraper {
    Write-Host "🛑 Stopping automation..." -ForegroundColor Yellow
    schtasks /change /tn "LinkedInJobsScraper_Auto" /disable
    Write-Host "✅ Automation stopped" -ForegroundColor Green
}

function Get-ScraperStatus {
    Write-Host "📊 Checking automation status..." -ForegroundColor Cyan
    schtasks /query /tn "LinkedInJobsScraper_Auto" /fo LIST 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Automated task not found" -ForegroundColor Red
        Write-Host "Run: Start-Scraper (as Administrator)" -ForegroundColor Yellow
    }
}

function Restart-Scraper {
    Write-Host "🔄 Restarting automation..." -ForegroundColor Magenta
    schtasks /end /tn "LinkedInJobsScraper_Auto" -ErrorAction SilentlyContinue
    schtasks /change /tn "LinkedInJobsScraper_Auto" /disable -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    schtasks /change /tn "LinkedInJobsScraper_Auto" /enable -ErrorAction SilentlyContinue
    Write-Host "✅ Automation restarted" -ForegroundColor Green
}

function Get-ScraperLogs {
    Write-Host "📄 Viewing recent logs..." -ForegroundColor Cyan
    $logDir = "$PSScriptRoot\logs"
    
    if (-not (Test-Path $logDir)) {
        Write-Host "⚠️  No logs directory found" -ForegroundColor Yellow
        return
    }
    
    $latestLog = Get-ChildItem "$logDir\scraper_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($latestLog) {
        Write-Host "Latest log file: $($latestLog.Name)" -ForegroundColor Green
        Write-Host "=" * 70 -ForegroundColor Gray
        Get-Content $latestLog.FullName -Tail 30
        Write-Host "=" * 70 -ForegroundColor Gray
    } else {
        Write-Host "⚠️  No log files found yet" -ForegroundColor Yellow
    }
}

function Run-ScraperManual {
    Write-Host "🔧 Running scraper manually..." -ForegroundColor Magenta
    Set-Location $PSScriptRoot
    & "$PSScriptRoot\auto_scraper.py"
}

function Show-ScraperMenu {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host "  🤖 JOB SCRAPER AUTOMATION MENU" -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Start automation" -ForegroundColor White
    Write-Host "2. Stop automation" -ForegroundColor White
    Write-Host "3. Check status" -ForegroundColor White
    Write-Host "4. Restart automation" -ForegroundColor White
    Write-Host "5. View logs" -ForegroundColor White
    Write-Host "6. Run manually" -ForegroundColor White
    Write-Host "0. Exit" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (0-6)"
    
    switch ($choice) {
        "1" { Start-Scraper }
        "2" { Stop-Scraper }
        "3" { Get-ScraperStatus }
        "4" { Restart-Scraper }
        "5" { Get-ScraperLogs }
        "6" { Run-ScraperManual }
        "0" { return }
        default { Write-Host "Invalid choice" -ForegroundColor Red }
    }
}

# Export functions as aliases for easy use
Set-Alias -Name scraper -Value Show-ScraperMenu
Set-Alias -Name scraper-status -Value Get-ScraperStatus
Set-Alias -Name scraper-start -Value Start-Scraper
Set-Alias -Name scraper-stop -Value Stop-Scraper
Set-Alias -Name scraper-restart -Value Restart-Scraper
Set-Alias -Name scraper-logs -Value Get-ScraperLogs
Set-Alias -Name scraper-run -Value Run-ScraperManual

# Display help on import
Write-Host ""
Write-Host "✅ Job Scraper Automation Tools Loaded!" -ForegroundColor Green
Write-Host ""
Write-Host "Available Commands:" -ForegroundColor Cyan
Write-Host "  scraper              - Show interactive menu" -ForegroundColor White
Write-Host "  scraper-status       - Check automation status" -ForegroundColor White
Write-Host "  scraper-start        - Start automation (requires Admin)" -ForegroundColor White
Write-Host "  scraper-stop         - Stop automation" -ForegroundColor White
Write-Host "  scraper-restart      - Restart automation" -ForegroundColor White
Write-Host "  scraper-logs         - View recent logs" -ForegroundColor White
Write-Host "  scraper-run          - Run scraper manually" -ForegroundColor White
Write-Host ""
