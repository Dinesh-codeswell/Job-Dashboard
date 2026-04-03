# 🤖 How to Run Automation Commands

## ❌ The Problem

When you type this in PowerShell:
```powershell
automation_manager.bat status
```

You get this error:
```
The term 'automation_manager.bat' is not recognized
```

**Why?** PowerShell requires `.\` prefix for files in the current directory.

---

## ✅ Solution 1: Use `.\` Prefix (Quick Fix)

Always add `.\` before `.bat` files in PowerShell:

```powershell
# ✅ Correct
.\automation_manager.bat status
.\automation_manager.bat start
.\automation_manager.bat stop
.\automation_manager.bat logs

# ❌ Wrong (missing .\ prefix)
automation_manager.bat status
```

### All Batch File Commands

```powershell
# Show interactive menu
.\automation_manager.bat

# Check status
.\automation_manager.bat status

# Stop automation
.\automation_manager.bat stop

# Start automation
.\automation_manager.bat start

# Restart automation
.\automation_manager.bat restart

# View logs
.\automation_manager.bat logs

# Run scraper manually
.\automation_manager.bat
# (Then select option 6 from menu)

# Quick reference
.\AUTOMATION_QUICK_REFERENCE.bat

# Verify setup
.\verify_automation.bat
```

---

## 🌟 Solution 2: Install PowerShell Commands (Recommended)

Install custom PowerShell commands so you can use **simple names without `.\`**:

### Step 1: Install (Run ONCE)

In PowerShell, run:
```powershell
.\install_ps_commands.ps1
```

If you get an execution policy error, run this first:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then run the installer again.

### Step 2: Restart PowerShell

Close your current PowerShell window and open a new one.

### Step 3: Use Simple Commands!

Now you can use these commands **from anywhere**:

```powershell
scraper              # Show interactive menu
scraper-status       # Check automation status
scraper-start        # Start automation
scraper-stop         # Stop automation
scraper-restart      # Restart automation
scraper-logs         # View recent logs
scraper-run          # Run scraper manually
```

**No `.\` prefix needed!** ✨

---

## 📋 Quick Reference Card

### Method 1: Batch Files (Works Immediately)
```powershell
.\automation_manager.bat status
.\automation_manager.bat start
.\automation_manager.bat stop
.\automation_manager.bat logs
```

### Method 2: PowerShell Commands (After Install)
```powershell
scraper-status
scraper-start
scraper-stop
scraper-logs
```

---

## 🎯 Most Common Use Cases

### "Is my automation running?"
```powershell
# Method 1 (Batch)
.\automation_manager.bat status

# Method 2 (PowerShell command - after install)
scraper-status
```

### "Stop the scraper temporarily"
```powershell
# Method 1
.\automation_manager.bat stop

# Method 2
scraper-stop
```

### "Start the scraper again"
```powershell
# Method 1
.\automation_manager.bat start

# Method 2
scraper-start
```

### "Show me what happened"
```powershell
# Method 1
.\automation_manager.bat logs

# Method 2
scraper-logs
```

### "Run it RIGHT NOW"
```powershell
# Method 1 (interactive menu, select option 6)
.\automation_manager.bat

# Method 2
scraper-run
```

---

## 🔧 Troubleshooting

### Error: "automation_manager.bat not found"

**Fix**: Make sure you're in the right directory:
```powershell
cd C:\linkedin_scraper
```

Then use `.\` prefix:
```powershell
.\automation_manager.bat status
```

### Error: "cannot be loaded because running scripts is disabled"

**Fix**: Enable script execution:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Error: "Task not found" when checking status

**Fix**: Run setup first:
```powershell
# Right-click this file and run as admin
setup_automation.bat
```

Or in PowerShell (as Administrator):
```powershell
.\setup_automation.bat
```

---

## 💡 Recommendation

**Install the PowerShell commands** (Solution 2) for the best experience:

```powershell
.\install_ps_commands.ps1
```

Then you get **clean, simple commands** like:
- `scraper-status`
- `scraper-start`
- `scraper-stop`

Instead of:
- `.\automation_manager.bat status`
- `.\automation_manager.bat start`

---

## 📁 File Summary

| File | Purpose | How to Run |
|------|---------|------------|
| `setup_automation.bat` | Initial setup (run once as admin) | Right-click → Run as Administrator |
| `automation_manager.bat` | Management console | `.\automation_manager.bat` |
| `verify_automation.bat` | Check prerequisites | `.\verify_automation.bat` |
| `install_ps_commands.ps1` | Install PS commands | `.\install_ps_commands.ps1` |
| `automation_tools.ps1` | PowerShell functions (don't run directly) | Loaded by install script |
| `AUTOMATION_QUICK_REFERENCE.bat` | Quick command reference | `.\AUTOMATION_QUICK_REFERENCE.bat` |

---

**Created**: April 3, 2026
