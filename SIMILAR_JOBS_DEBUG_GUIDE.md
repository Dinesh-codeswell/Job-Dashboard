# 🔧 Similar Jobs Not Loading - Debugging Guide

## Problem

Similar jobs section stopped working after round-robin scraping changes. No console logs appear, suggesting the function isn't being called or is failing silently.

## Changes Made

Added comprehensive console logging to `loadSimilarJobs()` function in `job_detail.html`:

```javascript
async function loadSimilarJobs() {
    console.log('=== LOADING SIMILAR JOBS ===');
    console.log('Job ID:', jobId);
    
    const response = await fetch(`/api/jobs/${jobId}/similar`);
    console.log('Response status:', response.status);
    
    const data = await response.json();
    console.log('Similar jobs response:', data);
    
    console.log(`Rendering ${data.similar_jobs.length} similar jobs`);
    // ...
}
```

## How to Debug

### 1. Open Job Detail Page

```
http://localhost:5000/job/<any-job-id>
```

### 2. Open Browser Console (F12)

### 3. Look For These Logs:

**Expected Successful Output:**
```
=== LOADING SIMILAR JOBS ===
Job ID: job_123456
Fetching from: /api/jobs/job_123456/similar
Response status: 200
Similar jobs response: {success: true, similar_jobs: Array(3), count: 3}
Rendering 3 similar jobs
```

**If Job ID is Wrong:**
```
=== LOADING SIMILAR JOBS ===
Job ID: undefined  ← PROBLEM: Job ID not extracted from URL
```

**If API Fails:**
```
=== LOADING SIMILAR JOBS ===
Job ID: job_123456
Fetching from: /api/jobs/job_123456/similar
Response status: 500  ← PROBLEM: Server error
Error loading similar jobs: ...
```

**If No Similar Jobs:**
```
=== LOADING SIMILAR JOBS ===
Job ID: job_123456
Response status: 200
Similar jobs response: {success: true, similar_jobs: [], count: 0}
No similar jobs found
```

## Possible Issues & Solutions

### Issue 1: Job ID Not Extracted from URL

**Symptom**: Console shows `Job ID: undefined`

**Solution**: Check this line in job_detail.html:
```javascript
const jobId = window.location.pathname.split('/').pop();
```

### Issue 2: API Returns 500 Error

**Symptom**: `Response status: 500`

**Solution**: Check Flask server logs for the actual error.

### Issue 3: NaN in Response

**Symptom**: Console shows JSON parse error with NaN

**Solution**: Already fixed by sanitize_job_data() in app.py

### Issue 4: No Similar Jobs Found

**Symptom**: `similar_jobs: []`

**Possible Causes**:
- Not enough jobs in Google Sheets
- All jobs have different cities/types/keywords
- Job ID mismatch

**Solution**: Ensure you have at least 4+ jobs in sheets with some overlap in:
- Search City
- Employment Type  
- Job Title keywords

## Backend Logic

The similar jobs algorithm scores based on:

```python
# Factor 1: Same city (40 points)
if current_city == job_city:
    score += 40

# Factor 2: Same type (30 points)
if current_type == job_type:
    score += 30

# Factor 3: Similar title (30 points)
common_keywords = extract_keywords(current_title) & extract_keywords(job_title)
score += len(common_keywords) * 10

# Factor 4: Same company (20 points)
if current_company == job_company:
    score += 20

# Return top 3 by score
```

## Files Modified

| File | Changes |
|------|---------|
| `dashboard/templates/job_detail.html` | Added console logging to loadSimilarJobs() |

## Next Steps

1. **Restart Flask server**
2. **Open job detail page with console open**
3. **Share the console output** with me
4. I'll identify the exact issue from the logs

---

**Created**: April 3, 2026  
**Status**: 🔍 Debugging mode with comprehensive logging  
**Next**: Test and share console output
