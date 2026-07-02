# Comprehensive Scraper Status Checker
# Shows task status, logs, and Google Sheets info

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  SCRAPER STATUS DASHBOARD" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if task exists
Write-Host "[1] AUTOMATION TASK STATUS" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$task = schtasks /query /tn "LinkedInJobsScraper_Auto" /fo LIST 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Task exists and is configured" -ForegroundColor Green
    Write-Host ""
    
    # Parse task info
    $taskInfo = $task | Out-String
    
    if ($taskInfo -match "Status:\s+(.+)") {
        $status = $matches[1].Trim()
        if ($status -eq "Ready") {
            Write-Host "   Status: $status ✅" -ForegroundColor Green
        } else {
            Write-Host "   Status: $status ⚠️" -ForegroundColor Yellow
        }
    }
    
    if ($taskInfo -match "Next Run Time:\s+(.+)") {
        Write-Host "   Next Run: $($matches[1].Trim())" -ForegroundColor Cyan
    }
    
    if ($taskInfo -match "Last Run Time:\s+(.+)") {
        Write-Host "   Last Run: $($matches[1].Trim())" -ForegroundColor White
    }
    
    if ($taskInfo -match "Last Result:\s+(.+)") {
        $result = $matches[1].Trim()
        if ($result -eq "0") {
            Write-Host "   Last Result: Success (0) ✅" -ForegroundColor Green
        } else {
            Write-Host "   Last Result: Error ($result) ❌" -ForegroundColor Red
        }
    }
} else {
    Write-Host "❌ Task not found!" -ForegroundColor Red
    Write-Host "   Run: setup_with_wrapper.ps1 (as Administrator)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2] RECENT LOG ACTIVITY" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$logDir = ".\logs"
if (Test-Path $logDir) {
    $latestLog = Get-ChildItem "$logDir\scraper_*.log" -ErrorAction SilentlyContinue | 
                 Sort-Object LastWriteTime -Descending | 
                 Select-Object -First 1
    
    if ($latestLog) {
        Write-Host "   Latest log: $($latestLog.Name)" -ForegroundColor White
        Write-Host "   Modified: $($latestLog.LastWriteTime)" -ForegroundColor Gray
        Write-Host ""
        
        # Show last 20 lines
        $logContent = Get-Content $latestLog.FullName -Tail 20
        
        foreach ($line in $logContent) {
            # Color code important lines
            if ($line -match "ERROR|Failed|❌") {
                Write-Host "   $line" -ForegroundColor Red
            } elseif ($line -match "SUCCESS|✅|Uploaded") {
                Write-Host "   $line" -ForegroundColor Green
            } elseif ($line -match "WARNING|⚠️") {
                Write-Host "   $line" -ForegroundColor Yellow
            } elseif ($line -match "INFO|📊|🔍") {
                Write-Host "   $line" -ForegroundColor Cyan
            } else {
                Write-Host "   $line" -ForegroundColor White
            }
        }
    } else {
        Write-Host "   No log files found yet" -ForegroundColor Yellow
        Write-Host "   Scraper hasn't run yet or logs are in a different location" -ForegroundColor Gray
    }
} else {
    Write-Host "   Logs directory not found: $logDir" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3] GOOGLE SHEETS INFO" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Check if credentials exist
if (Test-Path "credentials.json") {
    Write-Host "   ✅ Google credentials found" -ForegroundColor Green
} else {
    Write-Host "   ❌ credentials.json not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "   Worksheets to check:" -ForegroundColor White
Write-Host "   • LinkedIn_Jobs    (main scraper)" -ForegroundColor Cyan
Write-Host "   • Indeed_Jobs      (indeed jobs)" -ForegroundColor Cyan
Write-Host "   • Deloitte_Jobs    (Deloitte-specific)" -ForegroundColor Cyan

Write-Host ""
Write-Host "[4] QUICK ACTIONS" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "   View live updates:  .\watch_scraper_live.bat" -ForegroundColor White
Write-Host "   Run manually:       python auto_scraper.py" -ForegroundColor White
Write-Host "   Stop automation:    schtasks /change /tn LinkedInJobsScraper_Auto /disable" -ForegroundColor White
Write-Host "   Restart automation: schtasks /change /tn LinkedInJobsScraper_Auto /enable" -ForegroundColor White

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Offer to open Google Sheets
$openSheets = Read-Host "Open Google Sheets to view jobs? (y/n)"
if ($openSheets -eq "y" -or $openSheets -eq "Y") {
    # Try to find sheet URL in config or .env
    if (Test-Path ".env") {
        $sheetId = Select-String -Path ".env" -Pattern "GOOGLE_SHEET_ID=(.+)" | 
                   ForEach-Object { $_.Matches.Groups[1].Value }
        
        if ($sheetId) {
            $url = "https://docs.google.com/spreadsheets/d/$sheetId/edit"
            Write-Host "Opening: $url" -ForegroundColor Green
            Start-Process $url
        } else {
            Write-Host "Sheet ID not found in .env file" -ForegroundColor Yellow
        }
    } else {
        Write-Host ".env file not found" -ForegroundColor Yellow
    }
}

Write-Host ""
