# 🤖 Automation Scraper - Quick Reference

## ✅ **Verified: Automation Script Uses Correct Logic**

### **File: `auto_scraper.py`**

| Feature | Status | Notes |
|---------|--------|-------|
| **Scraping Algorithm** | ✅ Updated | Uses `scrape_all_india_jobs.py` with round-robin strategy |
| **Consulting Job Filter** | ✅ Active | `is_valid_consulting_job()` automatically filters non-consulting roles |
| **Internship Filter** | ✅ Active | `BLOCKED_TITLE_PATTERNS` blocks interns automatically |
| **Employment Type Normalization** | ✅ Active | Indeed `fulltime` → `Full Time`, `nan` → `Full Time` |
| **Job Description Cleaning** | ✅ Active | Removes heading artifacts like "About the Job" |
| **3-Day Window** | ✅ Active | `max_days=3` matches dashboard |
| **Google Sheets Upload** | ✅ Active | Uploads to `LinkedIn_Jobs`, `Indeed_Jobs`, `Naukri_Jobs` tabs |

---

## 📋 **What Happens When You Run Automation:**

```
1. auto_scraper.py starts
   ↓
2. Checks prerequisites (.env, credentials, session)
   ↓
3. Creates UnifiedIndiaJobsScraper(max_days=3, headless=True)
   ↓
4. Runs round-robin: platform × city × keyword combinations
   ↓
5. For each job scraped:
   - Validates consulting role (blocks interns, founder's office, etc.)
   - Normalizes employment type (Indeed formats → standard format)
   - Cleans job description (removes heading artifacts)
   - Detects duplicates across platforms
   ↓
6. Uploads to Google Sheets (separate tabs per platform)
   ↓
7. Logs results to logs/scraper_YYYY_MM_DD.log
```

---

## 🔧 **How to Run:**

### **Manual Run:**
```bash
py auto_scraper.py
```

### **Automated (Every 15 minutes via Task Scheduler):**
```powershell
# Run the PowerShell automation script
.\automation_tools.ps1
```

### **Via Batch File:**
```cmd
automation_manager.bat
```

---

## 📊 **Current Configuration:**

| Setting | Value | Location |
|---------|-------|----------|
| **Platforms** | LinkedIn, Indeed, Naukri | `auto_scraper.py` line 89 |
| **Time Window** | 3 days | `auto_scraper.py` line 91 |
| **Limit per Keyword** | 30 jobs | `auto_scraper.py` line 97 |
| **Batch Size** | 10 tasks | `auto_scraper.py` line 99 |
| **Headless Mode** | True (no browser UI) | `auto_scraper.py` line 92 |
| **Consulting Filter** | Enabled | `scrape_all_india_jobs.py` |
| **Intern Filter** | Enabled | `scrape_all_india_jobs.py` |
| **Employment Type Norm** | Enabled | `scrape_all_india_jobs.py` |

---

## 🎯 **Consulting Job Filter - Active During Automation:**

### **Blocked Roles (Automatically Rejected):**
- Interns, Traines, Apprentices
- Founder's Office roles
- Executive/Personal Assistants
- Data Entry, Back Office

### **Accepted Roles:**
- Management/Business/Strategy Consultants
- IT/Technology/Digital Consultants
- SAP/Oracle/Cloud Consultants
- Analysts with "consulting" in title

### **Filtered Stats Logged:**
```
🚫 Filtered Out: 67  ← Jobs rejected by filter
🔗 LinkedIn Jobs: 45
📡 Indeed Jobs: 23
🇮🇳 Naukri Jobs: 31
📈 Total Jobs: 99
```

---

## 📝 **Employment Type Normalization - Active During Automation:**

### **Indeed → Standard Format:**
| Before | After |
|--------|-------|
| `fulltime` | `Full Time` |
| `parttime` | `Part Time` |
| `contract` | `Contract` |
| `internship` | `Internship` |
| `nan` | `Full Time` |
| `remote` | `Remote` |

---

## 🔄 **Sync to Supabase:**

After automation runs, sync to Supabase for dashboard:
```bash
py sync_engine.py
```

This:
1. Deletes jobs older than 3 days from Supabase
2. Fetches fresh jobs from Google Sheets
3. Normalizes timestamps
4. Upserts to Supabase

---

## 📁 **Log Files:**

- **Automation Logs:** `logs/scraper_YYYY_MM_DD.log`
- **Consulting Filter Stats:** Logged during each run
- **Employment Type Normalization:** Applied silently (no extra logging)

---

## ✅ **Verification Checklist:**

Run this to verify automation is using correct logic:
```bash
py auto_scraper.py
```

Check logs for:
- ✅ `Multi-column search for: '...'` (search working)
- ✅ `✗ Filtered: <title> - <reason>` (consulting filter active)
- ✅ `Search matched X jobs` (search filtering correctly)
- ✅ `Uploaded to Google Sheets` (upload working)

---

**Your automation scraper is fully up-to-date with all the latest changes!** 🚀
