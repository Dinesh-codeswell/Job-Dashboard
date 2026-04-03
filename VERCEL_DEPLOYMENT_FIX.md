# Vercel Deployment Fix - Google Sheets Integration

## Problem Fixed ✅

**Issue:** Jobs were fetching correctly in local development but failing on Vercel deployment.

**Root Cause:** The Google Sheets data fetcher (`dashboard/data/sheets_fetcher.py`) only supported file-based credentials (`credentials.json`), which doesn't exist in the Vercel deployment environment.

## What Was Fixed

Updated `dashboard/data/sheets_fetcher.py` to support **both**:
1. **Environment variable credentials** (for Vercel/cloud deployment) - `GOOGLE_CREDENTIALS_JSON`
2. **File-based credentials** (for local development) - `credentials.json`

The connect() method now:
- First tries to read `GOOGLE_CREDENTIALS_JSON` or `GOOGLE_CREDENTIALS` environment variable
- Falls back to `credentials.json` file if env var is not set
- Provides clear error logging for debugging

## Required Vercel Environment Variables

You **MUST** set these environment variables in your Vercel dashboard:

### 1. GOOGLE_SHEET_ID
Your Google Spreadsheet ID (the long string in the URL).

**Where to find it:** 
- Open your Google Sheet
- Look at the URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit`
- Copy the `YOUR_SHEET_ID_HERE` part

**Example value:** `1qul0CigJ7pMPh-xikhgpaxLXRXlyYjOaN5rhhO3LTHU`

### 2. GOOGLE_CREDENTIALS_JSON (CRITICAL)
The **entire contents** of your `credentials.json` service account file, as a single line.

**How to set it:**

1. **Open your `credentials.json` file** (the one you use locally)

2. **Convert it to a single line:**
   - On Windows, run this PowerShell command:
     ```powershell
     Get-Content credentials.json | ConvertTo-Json -Compress | Set-Clipboard
     ```
   - Or manually remove all newlines and extra spaces

3. **Go to Vercel Dashboard:**
   - Select your project
   - Go to **Settings** → **Environment Variables**
   - Add new variable:
     - **Name:** `GOOGLE_CREDENTIALS_JSON`
     - **Value:** Paste the entire JSON (single line)
     - **Environments:** Check all (Production, Preview, Development)
   - Click **Save**

**Example value (formatted for readability, but paste as single line):**
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-sa@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

### 3. WORKSHEET_NAME (Optional)
The primary worksheet name (deprecated - now fetches from all sheets).

**Default value:** `LinkedIn_Jobs`

## Step-by-Step Deployment Instructions

### Step 1: Set Environment Variables in Vercel

1. Go to https://vercel.com/dashboard
2. Select your project
3. Click **Settings** → **Environment Variables**
4. Add the following:

   | Variable Name | Value | Environments |
   |--------------|-------|--------------|
   | `GOOGLE_SHEET_ID` | Your sheet ID | All |
   | `GOOGLE_CREDENTIALS_JSON` | Your credentials JSON (single line) | All |

5. Click **Save**

### Step 2: Push the Code Fix to GitHub

```bash
git add dashboard/data/sheets_fetcher.py
git commit -m "fix: support GOOGLE_CREDENTIALS_JSON env var for Vercel deployment"
git push
```

### Step 3: Redeploy on Vercel

Vercel will automatically redeploy when you push to GitHub. Or manually:

```bash
vercel --prod
```

### Step 4: Verify the Deployment

1. Open your deployed site
2. Check that jobs are loading
3. If not, check Vercel logs:
   - Go to Vercel Dashboard → Your Project → **Deployments**
   - Click on the latest deployment → **Logs**
   - Look for any errors related to Google Sheets credentials

## Troubleshooting

### Jobs Still Not Loading?

**Check 1: Environment Variables Are Set**
```bash
# In Vercel Dashboard → Settings → Environment Variables
# Verify both GOOGLE_SHEET_ID and GOOGLE_CREDENTIALS_JSON are set
```

**Check 2: JSON Format Is Valid**
- The `GOOGLE_CREDENTIALS_JSON` must be valid JSON on a **single line**
- No trailing commas
- All quotes properly escaped

**Check 3: Service Account Has Access**
- Open your Google Sheet
- Click **Share** button
- Add the service account email (from `credentials.json`)
- Give it **Editor** access
- Click **Share**

**Check 4: Vercel Logs**
```bash
# View logs in Vercel Dashboard
# Look for these log messages:
# ✅ "Using credentials from environment variable"
# ✅ "Connected to Google Sheets: LinkedIn_Jobs"
# ❌ "Credentials file not found" (means env var not set)
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid JSON in GOOGLE_CREDENTIALS_JSON` | Multi-line JSON or syntax error | Convert to single line, check for errors |
| `Credentials file not found` | Env var not set, file doesn't exist | Set `GOOGLE_CREDENTIALS_JSON` in Vercel |
| `WorksheetNotFound` | Wrong worksheet name | Check sheet tab names in Google Sheets |
| `Failed to connect to Google Sheets` | Service account not authorized | Share the sheet with service account email |

## How It Works Now

### Local Development
```
credentials.json file exists → Used for authentication
```

### Vercel Deployment
```
GOOGLE_CREDENTIALS_JSON env var set → Used for authentication
```

### Code Flow
```python
def connect(self):
    # 1. Try env var first (Vercel)
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        creds = Credentials.from_service_account_info(json.loads(creds_json))
    
    # 2. Fallback to file (local)
    else:
        creds = Credentials.from_service_account_file('credentials.json')
```

## Files Modified

- `dashboard/data/sheets_fetcher.py` - Added env var support in `connect()` method

---

**Next Steps:** Push this fix to GitHub and set the environment variables in Vercel. Jobs should start loading immediately!
