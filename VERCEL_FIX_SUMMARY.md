# 🔧 VERCEL 500 ERROR - QUICK FIX SUMMARY

## What Was Wrong

Your Vercel deployment was crashing due to **7 critical issues**:

1. ❌ Missing `api/requirements.txt` (Vercel needs this)
2. ❌ `.vercelignore` blocking important files
3. ❌ Flask not listed as dependency
4. ❌ Supabase FTS query crash (no error handling)
5. ❌ Google credentials path issues
6. ❌ No try/except in API routes
7. ❌ No health check endpoint for debugging

## ✅ What I Fixed

| File | Action |
|------|--------|
| `api/requirements.txt` | ✅ Created with all dependencies |
| `.vercelignore` | ✅ Removed aggressive patterns |
| `api/index.py` | ✅ Added error handling + health check |
| `api/data_fetcher.py` | ✅ Improved credentials handling |
| `.env.vercel` | ✅ Created template for env vars |

## 🎯 What YOU Need to Do

### 1. Add Environment Variables to Vercel

Go to: **Vercel Dashboard > Project > Settings > Environment Variables**

Add these:
```
NEXT_PUBLIC_SUPABASE_URL=https://ouyfcnosxwezwsqxunlj.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<get from your Supabase dashboard>
GOOGLE_SHEET_ID=<your Google Sheet ID>
GOOGLE_CREDENTIALS_JSON=<paste your entire credentials.json content here>
```

### 2. Redeploy

```bash
vercel --prod
```

Or push to git if connected.

### 3. Test

Visit: `https://your-domain.vercel.app/api/health`

Expected response:
```json
{
  "status": "ok",
  "supabase_connected": true,
  "sheets_connected": true
}
```

## 📖 Full Guide

See `VERCEL_DEPLOYMENT_FIX.md` for detailed instructions and troubleshooting.
