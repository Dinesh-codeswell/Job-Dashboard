# 🚀 Vercel Deployment Fix Guide

## ✅ Issues Fixed

Your **500: INTERNAL_SERVER_ERROR** was caused by multiple issues:

### 1. **Missing `api/requirements.txt`**
- Vercel Python needs its own requirements file at `api/requirements.txt`
- ✅ **FIXED**: Created with all necessary dependencies (flask, flask-cors, supabase, gspread, google-auth)

### 2. **`.vercelignore` Was Too Aggressive**
- It was ignoring critical files like `dashboard/templates/`, `dashboard/data/`, and using invalid negation patterns (`!api/requirements.txt`)
- ✅ **FIXED**: Removed problematic patterns

### 3. **Missing `flask` and `flask-cors` Dependencies**
- The main `requirements.txt` didn't include Flask
- ✅ **FIXED**: Added to `api/requirements.txt`

### 4. **Supabase FTS Query Crash**
- `text_search('fts_tokens', search)` would crash if the column doesn't exist in Supabase
- ✅ **FIXED**: Added try/except fallback to basic `ilike` search

### 5. **Google Credentials Path Issues**
- Credentials file path wasn't absolute, causing failures on Vercel
- ✅ **FIXED**: Auto-converts relative paths to absolute

### 6. **No Error Handling in API Routes**
- Single failures would crash the entire endpoint
- ✅ **FIXED**: Added comprehensive try/except blocks with graceful degradation

### 7. **Missing Health Check Endpoint**
- No way to diagnose what's working/broken
- ✅ **FIXED**: Added `/api/health` endpoint

---

## 🔧 What You Need to Do

### Step 1: Configure Vercel Environment Variables

Go to **Vercel Dashboard > Your Project > Settings > Environment Variables** and add:

#### Required Variables:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://ouyfcnosxwezwsqxunlj.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your_supabase_anon_key>

# Google Sheets
GOOGLE_SHEET_ID=<your_google_sheet_id>
```

#### Google Credentials (CHOOSE ONE OPTION):

**OPTION A: Use JSON Environment Variable (RECOMMENDED)**

1. Open your `credentials.json` file
2. Copy the ENTIRE JSON content
3. In Vercel, add variable: `GOOGLE_CREDENTIALS_JSON`
4. Paste the full JSON content as the value
5. Set for all environments (Production, Preview, Development)

**OPTION B: Upload as Secret File**

1. In Vercel Dashboard, go to **Storage > Secret Files**
2. Upload your `credentials.json` file
3. Add environment variable: `GOOGLE_CREDENTIALS_FILE=credentials.json`

---

### Step 2: Deploy to Vercel

```bash
# Option 1: Using Vercel CLI (recommended)
vercel --prod

# Option 2: Git push (if connected to repo)
git add .
git commit -m "fix: resolve vercel deployment errors"
git push origin main

# Option 3: Redeploy from Vercel dashboard
# Go to your project > Deployments > ... > Redeploy
```

---

### Step 3: Verify Deployment

After deployment, test these endpoints:

```bash
# Health check (diagnoses connection issues)
curl https://your-domain.vercel.app/api/health

# Jobs endpoint
curl https://your-domain.vercel.app/api/jobs

# Stats endpoint
curl https://your-domain.vercel.app/api/stats

# Cities endpoint
curl https://your-domain.vercel.app/api/cities
```

Expected health check response:
```json
{
  "status": "ok",
  "supabase_connected": true,
  "sheets_connected": true
}
```

---

## 🔍 Troubleshooting

### Still Getting 500 Error?

1. **Check Vercel Function Logs:**
   - Go to Vercel Dashboard > Your Project > Functions
   - Click on the failed invocation
   - Review the error logs

2. **Common Issues:**

   | Issue | Solution |
   |-------|----------|
   | `Supabase query failed` | Check if `jobs` table exists and has `posted_at_timestamp` column |
   | `Credentials error` | Verify `GOOGLE_CREDENTIALS_JSON` is valid JSON in Vercel env vars |
   | `Worksheet not found` | Ensure `GOOGLE_SHEET_ID` is correct and service account has access |
   | `Module not found: flask` | Verify `api/requirements.txt` is deployed |

3. **Test Locally First:**
   ```bash
   # Install dependencies
   pip install -r api/requirements.txt
   
   # Run the API locally
   python api/index.py
   
   # Test endpoints
   curl http://localhost:5000/api/health
   curl http://localhost:5000/api/jobs
   ```

---

## 📋 File Changes Made

| File | Change |
|------|--------|
| `api/requirements.txt` | **CREATED** - All Vercel Python dependencies |
| `.vercelignore` | **FIXED** - Removed overly aggressive patterns |
| `api/index.py` | **ENHANCED** - Added error handling, health check, FTS fallback |
| `api/data_fetcher.py` | **IMPROVED** - Better credentials handling, detailed error logging |
| `.env.vercel` | **CREATED** - Template for Vercel environment variables |

---

## 🎯 Next Steps

1. ✅ Add environment variables to Vercel
2. ✅ Redeploy (`vercel --prod`)
3. ✅ Test `/api/health` endpoint
4. ✅ Verify dashboard loads at `/`
5. ✅ Monitor function logs for any remaining issues

---

## 💡 Pro Tips

- Use `/api/health` as your first diagnostic tool
- Vercel free tier has **10 second timeout** - if queries are slow, optimize them
- Google Sheets API is slower than Supabase - consider making Supabase primary
- Enable Vercel Analytics to monitor function performance

---

**Need more help?** Check the Vercel function logs after deployment and share the error message!
