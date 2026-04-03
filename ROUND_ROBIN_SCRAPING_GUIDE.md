# 🎯 Round-Robin Scraping Strategy - Implementation Guide

## ✅ Implemented: Option A (Full Round-Robin with Maximum Diversity)

---

## 📊 What Changed

### Before (Sequential/Biased):
```
LinkedIn → Chennai (all 36 keywords) → Mumbai (all 36 keywords) → ...
Then: Indeed → Chennai (all keywords) → Mumbai (all keywords) → ...
Then: Naukri → Chennai (all keywords) → Mumbai (all keywords) → ...

Result: Jobs appear in clusters - all LinkedIn first, then Indeed, then Naukri
```

### After (Round-Robin/Diverse):
```
Task Pool Generated: 648 tasks (3 platforms × 6 cities × 36 keywords)
Shuffled: Complete randomization

Execution:
Batch 1: LinkedIn+Bangalore+Consultant, Naukri+Mumbai+Analyst, Indeed+Chennai+SAP...
Batch 2: Indeed+Pune+Consultant, LinkedIn+Hyderabad+IT, Naukri+Bangalore+Strategy...
Batch 3: Naukri+Chennai+Business, Indeed+Bangalore+Senior, LinkedIn+Mumbai+Cloud...

Result: Jobs from all platforms, cities, and keywords mixed evenly throughout
```

## 🔧 Implementation Details

### New Methods Added

#### 1. `_generate_task_pool()`
Creates all possible combinations and shuffles them:
```python
tasks = []
for platform in platforms:          # 3 platforms
    for city in cities:              # 6 cities
        for keyword in keywords:     # 36 keywords
            tasks.append({...})      # 3 × 6 × 36 = 648 tasks

random.shuffle(tasks)  # Eliminate all bias
```

#### 2. `_execute_linkedin_task()`
Executes a single LinkedIn task (platform + city + keyword):
```python
# Instead of scraping all jobs for a city/keyword combo
# Now scrapes just one combination at a time
job_urls = await search_scraper.search(keyword, city, limit)
for job_url in job_urls:
    upload_to_sheets_immediately(job)  # Real-time mixing
```

#### 3. `_execute_api_task()`
Executes a single Indeed/Naukri task:
```python
# Scrapes both Indeed and Naukri for one keyword+city
df = scrape_multi_platform(keyword, city)
for job in df:
    upload_to_sheets_immediately(job)  # Immediate upload
```

#### 4. `run_round_robin()` (Main Method)
Orchestrates the entire round-robin process:
```python
# 1. Generate task pool
task_pool = _generate_task_pool(platforms, cities, keywords)

# 2. Execute in batches
for batch in chunks(task_pool, batch_size=10):
    # Separate by type
    linkedin_tasks = [t for t in batch if t['platform'] == 'linkedin']
    api_tasks = [t for t in batch if t['platform'] in ['indeed', 'naukri']]
    
    # Execute LinkedIn (needs browser)
    for task in linkedin_tasks:
        _execute_linkedin_task(task)
    
    # Execute API (Indeed/Naukri)
    for task in api_tasks:
        _execute_api_task(task)
    
    # Progress update
    print(f"Progress: {completed}/{total} ({percent}%)")
    
    # Pause between batches (rate limiting)
    await asyncio.sleep(5)
```

---

## 📈 Expected Results

### Visual Comparison

#### Before (Biased):
```
Google Sheets Order:
Row 1-50:   LinkedIn jobs from Chennai
Row 51-100: LinkedIn jobs from Mumbai
Row 101-150: LinkedIn jobs from Bangalore
...
Row 400-450: Indeed jobs from Chennai
Row 450-500: Indeed jobs from Mumbai
...
Row 700-750: Naukri jobs from Chennai
...
```
❌ All LinkedIn jobs appear first
❌ Same city jobs cluster together
❌ Predictable patterns

#### After (Diverse):
```
Google Sheets Order:
Row 1:   LinkedIn - Bangalore - Management Consultant
Row 2:   Naukri - Mumbai - SAP Consultant
Row 3:   Indeed - Chennai - Business Analyst
Row 4:   LinkedIn - Pune - IT Consultant
Row 5:   Naukri - Hyderabad - Strategy Consultant
Row 6:   Indeed - Bangalore - Senior Consultant
Row 7:   LinkedIn - Mumbai - Cloud Consultant
Row 8:   Naukri - Chennai - Financial Analyst
...
```
✅ Jobs from all platforms mixed
✅ Cities interleaved
✅ Keywords distributed evenly
✅ Maximum diversity

---

## 🎯 Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Platform Diversity** | All LinkedIn → All Indeed → All Naukri | Mixed throughout |
| **City Distribution** | Chennai cluster → Mumbai cluster → ... | Cities interleaved |
| **Keyword Spread** | Similar roles group together | Different roles mixed |
| **User Experience** | Sees clusters of similar jobs | Diverse jobs on every page |
| **Bias Level** | High (predictable) | Low (randomized) |
| **Rate Limiting** | Long continuous scraping | Natural pauses between batches |

---

## ⚙️ Configuration

### Batch Size
```python
batch_size=10  # Process 10 tasks at a time
```
- **Smaller (5)**: More pauses, slower but safer from rate limits
- **Larger (20)**: Fewer pauses, faster but higher rate limit risk
- **Current (10)**: Balanced approach

### Pause Duration
```python
pause_time = 5  # Seconds between batches
```
- Prevents rate limiting
- Natural delay between task batches

### Task Pool Size
```
With current settings:
- 3 platforms (LinkedIn, Indeed, Naukri)
- 6 cities (Chennai, Mumbai, Pune, Gurugram, Bangalore, Hyderabad)
- 36 keywords (consulting roles + internships)

Total tasks: 3 × 6 × 36 = 648 tasks
```

---

## 📊 Execution Flow

```
1. Generate Task Pool (648 tasks)
   ↓
2. Shuffle randomly
   ↓
3. Split into batches (10 tasks each = ~65 batches)
   ↓
4. For each batch:
   ├─ Execute LinkedIn tasks (open browser, scrape, close)
   ├─ Execute API tasks (Indeed + Naukri)
   ├─ Upload jobs immediately to Google Sheets
   ├─ Update progress
   └─ Pause 5 seconds
   ↓
5. Upload summary statistics
   ↓
6. Complete!
```

---

## 🔍 Monitoring Progress

### Console Output
```
======================================================================
📦 BATCH 1/65 (10 tasks)
======================================================================
🔍 LinkedIn: 'Management Consultant' in Bangalore
  ✓ LinkedIn: Senior Consultant at Deloitte
  ✅ LinkedIn: 3 jobs from 'Management Consultant' in Bangalore

🔍 API: 'SAP Consultant' in Mumbai
  ✓ Indeed: SAP Analyst at Accenture
  ✓ Naukri: SAP Lead at TCS
  ✅ API: 5 jobs from 'SAP Consultant' in Mumbai

✅ Progress: 10/648 tasks (1.5%)
📊 Total jobs uploaded: 47
⏸️  Pausing 5s before next batch...
```

### Logs
```
2026-04-03 14:00:00 - INFO - 📋 Generated 648 tasks with randomized order
2026-04-03 14:00:01 - INFO - 🎯 Platforms: 3 | Cities: 6 | Keywords: 36
2026-04-03 14:00:05 - INFO - 🔍 LinkedIn: 'IT Consultant' in Mumbai
2026-04-03 14:01:30 - INFO -   ✅ LinkedIn: 2 jobs from 'IT Consultant' in Mumbai
...
```

---

## 🚀 Files Modified

| File | Changes |
|------|---------|
| `scrape_all_india_jobs.py` | Added round-robin methods, updated main() |
| `auto_scraper.py` | Updated to use run_round_robin() |

### New Methods:
- `_generate_task_pool()` - Creates randomized task combinations
- `_execute_linkedin_task()` - Single LinkedIn task execution
- `_execute_api_task()` - Single Indeed/Naukri task execution
- `run_round_robin()` - Main orchestration method

---

## 🧪 Testing

### Manual Test
```bash
cd C:\linkedin_scraper
python scrape_all_india_jobs.py --limit-per-city 5
```

Watch the output - you should see:
1. "ROUND-ROBIN MODE" in header
2. Tasks from different platforms mixed together
3. Cities changing randomly (not sequential)
4. Keywords varying (not all same keyword)

### Automation Test
The automation script now uses round-robin automatically:
```bash
.\automation_manager.bat
# Select option 6 (Run manually)
```

### Verify Diversity in Google Sheets
After scraping:
1. Open your Google Sheet
2. Check the order of jobs
3. Should see: LinkedIn, Naukri, Indeed, LinkedIn, Naukri... (mixed)
4. Should NOT see: All LinkedIn first, then all Indeed, then all Naukri

---

## 📝 Notes

### Why Batch Processing?
Instead of executing 648 tasks one by one (too slow) or all at once (rate limits), we:
- Process 10 tasks at a time
- Open/close browser once per batch (for LinkedIn)
- Natural 5-second pause between batches
- Balanced speed vs. safety

### Immediate Upload
Jobs are uploaded to Google Sheets **immediately** after scraping, not batched. This ensures:
- Real-time mixing in sheets
- No data loss if scraper crashes
- Can monitor progress live

### Backward Compatibility
Old methods (`scrape_linkedin`, `scrape_indeed_naukri`, `run`) are still available but not used by default. You can still call them manually if needed.

---

**Created**: April 3, 2026  
**Status**: ✅ Implemented and ready to use  
**Strategy**: Full Round-Robin with Maximum Diversity  
**Next**: Test and verify diversity in Google Sheets
