# Dashboard Troubleshooting Guide

## Issue: Job Detail Page Shows "Job Not Found"

### ✅ Fixed in Latest Version

The job ID encoding issue has been fixed. If you still see this error:

### Solution 1: Test the API Directly

1. **Open test page:**
   ```
   http://localhost:5000/test
   ```

2. **Click "Test API Call"**
   - If it shows "✅ API Working!", the backend is fine
   - If it shows an error, restart the server

3. **Click on any job from the list**
   - This will navigate to the job detail page
   - If it works from here but not from dashboard, clear browser cache

### Solution 2: Clear Browser Cache

1. Press `Ctrl + Shift + Delete`
2. Select "Cached images and files"
3. Click "Clear data"
4. Refresh the dashboard (`F5`)

### Solution 3: Check Browser Console

1. Press `F12` to open Developer Tools
2. Go to "Console" tab
3. Click on a job card
4. Look for errors in the console

Expected output:
```
Loading job with ID: job_4393581078
Fetching job from API: /api/jobs/job_4393581078
API Response: {success: true, job: {...}}
```

If you see errors, share them for debugging.

### Solution 4: Verify Job IDs Match

1. **Open dashboard** and check job IDs in URLs when hovering over cards
2. **Open test page** (`/test`) and compare job IDs
3. They should match exactly

Example:
- Dashboard job ID: `job_4393581078`
- Test page job ID: `job_4393581078`
- ✅ Should match!

### Solution 5: Restart Server

```bash
# Stop current server (Ctrl+C)
# Then restart:
cd dashboard
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe app.py
```

## Testing Checklist

Run through these tests to verify everything works:

### Test 1: Health Check
```
http://localhost:5000/api/health
```
Expected: `{"status": "healthy", "jobs_count": 11, ...}`

### Test 2: Jobs List
```
http://localhost:5000/api/jobs?page=1&limit=5
```
Expected: List of 5 jobs with IDs

### Test 3: Single Job
```
http://localhost:5000/api/jobs/job_4393581078
```
Expected: `{"success": true, "job": {...}}`

### Test 4: Dashboard Page
```
http://localhost:5000/
```
Expected: Shows job cards grid

### Test 5: Job Detail Page
```
http://localhost:5000/job/job_4393581078
```
Expected: Shows complete job details

### Test 6: Test Page
```
http://localhost:5000/test
```
Expected: Test interface with job list

## Common Issues & Solutions

### Issue: "Cannot GET /api/jobs"
**Solution:** Server not running or wrong port
- Check if server is running
- Verify URL is `http://localhost:5000`

### Issue: Jobs load but detail page is blank
**Solution:** JavaScript error
- Open browser console (F12)
- Look for errors
- Clear cache and refresh

### Issue: "Job Not Found" on all jobs
**Solution:** ID mismatch
1. Check if jobs have IDs in API response
2. Verify job IDs in Google Sheets have Job URL column
3. Restart server to reload data

### Issue: Dashboard shows 0 jobs
**Solution:** Data fetch issue
1. Check credentials.json exists
2. Verify GOOGLE_SHEET_ID in .env
3. Check worksheet name is "Consulting_Jobs_India"
4. Run health check: `/api/health`

## Debug Commands

### Check if server is running:
```bash
curl http://localhost:5000/api/health
```

### Test job API:
```bash
curl http://localhost:5000/api/jobs/job_4393581078
```

### View server logs:
Check the terminal where you ran `python app.py`
- Look for request logs
- Check for errors

### Force reload data:
```bash
curl -X POST http://localhost:5000/api/refresh
```

## Quick Fix Steps

If nothing works, try this sequence:

1. **Stop server** (Ctrl+C in terminal)

2. **Clear browser cache**
   - Ctrl + Shift + Delete
   - Clear cached files

3. **Restart server:**
   ```bash
   cd dashboard
   C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe app.py
   ```

4. **Test health:**
   ```
   http://localhost:5000/api/health
   ```

5. **Test job detail:**
   ```
   http://localhost:5000/job/job_4393581078
   ```

6. **If still broken, use test page:**
   ```
   http://localhost:5000/test
   ```

## Contact/Support

If issues persist:
1. Check Flask console for errors
2. Check browser console for JavaScript errors
3. Verify all 11 jobs appear in dashboard
4. Test individual components using test page

## Working Configuration

Your dashboard should have:
- ✅ 11 jobs loaded
- ✅ Health endpoint working
- ✅ Jobs API returning data
- ✅ Job IDs in format: `job_1234567890`
- ✅ Test page accessible at `/test`

---

**Last Updated:** April 1, 2026
**Dashboard Version:** 1.0
