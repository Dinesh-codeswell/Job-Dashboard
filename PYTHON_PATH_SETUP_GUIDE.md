# How to Add Python to PATH on Windows

## ✅ What Was Done

Python 3.11 has been installed and the PATH has been set for your user account.

**Python Location:**
```
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
```

## 🚀 Quick Start - Use the Scripts

### Option 1: Use the Setup Script (Recommended)
Double-click this file to open a terminal with Python ready to use:
```
setup_python_path.bat
```

### Option 2: Use Full Path
```bash
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe app.py
```

### Option 3: Use Updated Batch Files
All batch files have been updated to use the full Python path automatically:
```bash
dashboard\start_dashboard.bat
```

## 📋 Manual PATH Setup (Permanent Solution)

If you want Python available in ALL terminals permanently, follow these steps:

### Method 1: Using System Properties (Requires Admin)

1. **Open System Properties:**
   - Press `Win + R`
   - Type `sysdm.cpl` and press Enter

2. **Open Environment Variables:**
   - Click "Advanced" tab
   - Click "Environment Variables" button

3. **Edit User PATH:**
   - Under "User variables", find and select `Path`
   - Click "Edit"
   - Click "New"
   - Add: `C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\`
   - Click "New" again
   - Add: `C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\Scripts\`
   - Click "OK" on all windows

4. **Restart Terminal:**
   - Close and reopen any open command prompts
   - Test with: `python --version`

### Method 2: Using Registry (Advanced)

1. Press `Win + R`, type `regedit`, press Enter

2. Navigate to:
   ```
   HKEY_CURRENT_USER\Environment
   ```

3. Find the `Path` value and edit it to include:
   ```
   ;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\Scripts\
   ```

4. Restart your computer or log out and back in

### Method 3: Using PowerShell (If Admin Rights Available)

```powershell
# Add to user PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pythonPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311"
$pythonScripts = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts"

if ($userPath -notlike "*$pythonPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$pythonPath;$pythonScripts", "User")
}
```

Then restart your terminal.

## ✅ Verify Python is in PATH

Open a NEW command prompt and run:

```bash
python --version
```

Expected output:
```
Python 3.11.x
```

## 🎯 Using the Dashboard

Once Python is set up, start the dashboard:

### With PATH set:
```bash
cd dashboard
python app.py
```

### Without PATH (use full path):
```bash
cd dashboard
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe app.py
```

### Or use the batch file (works either way):
```bash
dashboard\start_dashboard.bat
```

## 🔧 Troubleshooting

### "Python was not found"
1. Make sure you opened a NEW terminal after setting PATH
2. Try running `setup_python_path.bat`
3. Use the full path to Python executable

### "Access Denied" when setting PATH
- The user-level PATH was already set successfully
- Machine-level PATH requires Administrator rights
- Use the batch files which don't require PATH

### Python version shows 3.11 but scripts don't work
- Make sure both paths are in PATH:
  - `...\Python311\`
  - `...\Python311\Scripts\`

## 📝 Quick Reference

| Command | Description |
|---------|-------------|
| `python --version` | Check Python version |
| `where python` | Find Python location |
| `echo %PATH%` | View current PATH |
| `setup_python_path.bat` | Open terminal with Python |
| `dashboard\start_dashboard.bat` | Start dashboard |

## 🎉 What's Ready

✅ Python 3.11 installed
✅ User PATH updated
✅ All batch files updated with full Python path
✅ Dashboard ready to run
✅ Job scrapers ready to use

## 📞 Need Help?

If you still have issues:
1. Use `setup_python_path.bat` - it sets up everything automatically
2. Use the full Python path in commands
3. All batch files now work without PATH

---

**Last Updated:** April 1, 2026
**Python Version:** 3.11.9
**Installation Path:** `C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\`
