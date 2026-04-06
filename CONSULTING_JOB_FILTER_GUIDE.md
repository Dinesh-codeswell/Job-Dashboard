# 🔧 Consulting Job Filter System

## Overview

The `scrape_all_india_jobs.py` script now includes **intelligent job filtering** to ensure only **actual consulting roles** are captured, rejecting irrelevant positions like interns, founder's office, data analysts, etc.

---

## How It Works

### **3-Layer Filtering Logic**

```
Job Title → Layer 1: Blocklist → Layer 2: Role Validation → Layer 3: Consulting Check → Result
```

#### **Layer 1: Hard Blocklist**
Immediately rejects jobs containing these patterns:
- `intern`, `trainee`, `apprentice`
- `founder's office`, `founder office`
- `chief of staff`, `executive assistant`, `personal assistant`
- `receptionist`, `data entry`, `back office`

#### **Layer 2: Role-Based Validation**
For certain role types, requires explicit "consultant/consulting" keyword:
- `analyst`, `associate`, `manager`, `director`
- `architect`, `engineer`, `developer`, `administrator`
- `specialist`, `coordinator`, `lead`, `head`
- `principal`, `senior`, `junior`, `staff`, `officer`, `executive`

**Example:**
- ❌ `"Data Analyst"` → Rejected (no "consulting" keyword)
- ✅ `"Analyst - Business Consulting Risk"` → Accepted (has "consulting")

#### **Layer 3: Consulting Term Check**
Must have at least one consulting-related term:
- `consultant`, `consulting`
- `advisory`, `advisor`
- `strategy`, `transformation`

---

## Examples

### ✅ **Accepted Jobs**

| Job Title | Reason |
|-----------|--------|
| `Management Consultant` | Has "consultant" |
| `Business Consultant` | Has "consultant" |
| `Analyst - Business Consulting Risk` | Has "consulting" + analyst validated |
| `EY - GDS Consulting - AIA - Gen AI - Manager` | Has "consulting" |
| `Computer Vision Consultant` | Has "consultant" |
| `Functional Consultant - RTP` | Has "consultant" |
| `SAP FIORI CONSULTANT` | Has "consultant" |
| `Solution Consultant II` | Has "consultant" |
| `Freelance Strategy Consultant` | Has "consultant" + "strategy" |
| `Consultant - Performance Transformation` | Has "consultant" |

### ❌ **Rejected Jobs**

| Job Title | Reason |
|-----------|--------|
| `Founder's Office Intern` | Blocklisted: "intern" + "founder's office" |
| `Data Analyst` | No consulting keyword |
| `Product Development Internship` | Blocklisted: "internship" |
| `Business Development Intern` | Blocklisted: "intern" |
| `Oracle Tech Architecture and Middleware` | Architect without consulting |
| `Network Engineer - IT Service` | Engineer without consulting |
| `Security Technical Engineer` | Engineer without consulting |
| `Oracle Cloud Infrastructure Admin` | Admin without consulting |
| `Cyber Security Architect - Team Leader` | Architect without consulting |
| `Post a job` | Invalid title |

---

## Configuration

### **Modify Blocklist**

Edit `BLOCKED_TITLE_PATTERNS` in `scrape_all_india_jobs.py`:

```python
BLOCKED_TITLE_PATTERNS = [
    "intern",
    "trainee",
    "apprentice",
    "founder's office",
    # Add more patterns here...
]
```

### **Modify Role Validation**

Edit `REQUIRES_CONSULTANT_KEYWORD` to add roles that need explicit consulting mention:

```python
REQUIRES_CONSULTANT_KEYWORD = [
    "analyst",
    "associate",
    "manager",
    # Add more role types...
]
```

### **Modify Valid Consulting Terms**

Edit `VALID_CONSULTING_TERMS` to change what counts as consulting:

```python
VALID_CONSULTING_TERMS = [
    "consultant",
    "consulting",
    "advisory",
    "advisor",
    "strategy",
    "transformation",
    # Add more terms...
]
```

---

## Statistics

The filter tracks how many jobs are rejected:

```
📊 WORKFLOW SUMMARY
🔗 LinkedIn Jobs:  45
📡 Indeed Jobs:   23
🇮🇳  Naukri Jobs:    31
📈 Total Jobs:    99
🚫 Filtered Out:  67    ← Jobs rejected by filter
⚠️  Duplicates:     12
❌ Errors:         3
```

---

## Testing

Run the test script to verify filter logic:

```bash
python test_consulting_filter.py
```

This tests all the problematic job titles you reported and validates they're being filtered correctly.

---

## Troubleshooting

### **Issue: Too many jobs being rejected**
- Check if your consulting keywords in `.env` are too broad
- Review `VALID_CONSULTING_TERMS` - you may need to add more terms

### **Issue: Not enough jobs being rejected**
- Add more patterns to `BLOCKED_TITLE_PATTERNS`
- Add more role types to `REQUIRES_CONSULTANT_KEYWORD`

### **Issue: Valid jobs being rejected**
- Check the debug logs: `✗ Filtered: <title> - <reason>`
- Adjust the filter lists accordingly

---

## Data Flow

```
LinkedIn/Indeed/Naukri → Scrape Jobs
                              ↓
                    Validate Job Title
                              ↓
                    ┌─────────┴─────────┐
                    │                   │
               ✅ Valid            ❌ Invalid
                    │                   │
                    ↓                   ↓
            Upload to Sheets      Skip + Count
```

---

**This ensures your Google Sheets only contains actual consulting roles!** 🎯
