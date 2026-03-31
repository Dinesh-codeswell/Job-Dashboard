# Vercel Deployment Guide - Consulting Jobs Dashboard

Complete guide to deploy your consulting jobs dashboard to Vercel.

---

## 📋 Prerequisites

1. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
2. **Google Sheets API** - Already configured
3. **Vercel CLI** (optional) - Install with `npm i -g vercel`

---

## 🚀 Quick Deploy (One-Click)

### Option 1: Vercel Dashboard

1. **Go to [vercel.com/new](https://vercel.com/new)**
2. **Import Git Repository**
   - Connect your GitHub/GitLab/Bitbucket
   - Select your repository
3. **Configure Project**
   - Framework Preset: `Other`
   - Root Directory: `./`
   - Build Command: (leave empty)
   - Output Directory: `dashboard`
4. **Add Environment Variables** (see below)
5. **Click Deploy**

### Option 2: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Navigate to project
cd C:\linkedin_scraper

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Y
# - Which scope? (select your account)
# - Link to existing project? N
# - Project name? consulting-jobs-dashboard
# - Directory? ./
# - Override settings? N

# Deploy to production
vercel --prod
```

---

## 🔐 Environment Variables

Add these in Vercel Dashboard → Project Settings → Environment Variables:

| Variable | Value | Environment |
|----------|-------|-------------|
| `GOOGLE_SHEET_ID` | Your Sheet ID | Production, Preview, Development |
| `GOOGLE_CREDENTIALS_FILE` | `credentials.json` | All |
| `WORKSHEET_NAME` | `Consulting_Jobs_India` | All |
| `SECRET_KEY` | Random string (e.g., `vercel-secret-xyz123`) | All |
| `PYTHON_VERSION` | `3.11` | All |

### How to Add Environment Variables

1. Go to Vercel Dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Click **Add New**
5. Add each variable above
6. Click **Save**

---

## 📁 Upload Credentials File

### Method 1: Vercel Dashboard (Recommended)

1. Go to Project Settings → **Git** → **Ignored Build Step**
2. Upload `credentials.json` as a secret file

### Method 2: Vercel CLI Secrets

```bash
# Upload credentials as secret
vercel secrets add credentials-json "$(cat credentials.json)"

# Update vercel.json to use secret
# (Already configured in vercel.json)
```

### Method 3: Include in Git (Not Recommended for Private Repos)

⚠️ **Only for private repositories!**

```bash
# Add credentials to git
git add credentials.json
git commit -m "Add Google credentials"
git push
```

**Better Approach:** Use Vercel Environment Variables for the credentials JSON content.

---

## 📂 Project Structure for Vercel

```
linkedin_scraper/
├── api/
│   ├── index.py              # Main API handler ✅
│   ├── data_fetcher.py       # Google Sheets integration ✅
│   ├── requirements.txt      # Python dependencies ✅
│   └── __init__.py
├── dashboard/
│   ├── static/               # CSS, JS ✅
│   └── templates/            # HTML templates ✅
├── credentials.json          # Google credentials (upload separately)
├── vercel.json              # Vercel configuration ✅
├── package.json             # NPM package (for Vercel CLI) ✅
├── .vercelignore            # Files to ignore ✅
└── VERCEL_DEPLOYMENT.md     # This file ✅
```

---

## 🧪 Test Locally Before Deploy

### Install Vercel CLI

```bash
npm i -g vercel
```

### Run Vercel Dev

```bash
# Navigate to project
cd C:\linkedin_scraper

# Start local dev server
vercel dev

# Open browser
http://localhost:3000
```

### Test Endpoints

```bash
# Health check
curl http://localhost:3000/api/health

# Get jobs
curl http://localhost:3000/api/jobs

# Get stats
curl http://localhost:3000/api/stats
```

---

## 🎯 Deploy Steps

### Step 1: Prepare Files

✅ All files created in `api/` folder  
✅ `vercel.json` configured  
✅ `requirements.txt` in `api/`  
✅ `.vercelignore` created  

### Step 2: Upload Credentials

Choose one method from above and upload `credentials.json`

### Step 3: Deploy to Vercel

```bash
# Login
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

### Step 4: Add Environment Variables

In Vercel Dashboard:
1. Project Settings → Environment Variables
2. Add all required variables
3. Redeploy

### Step 5: Test Deployment

```bash
# Your production URL
https://your-project.vercel.app

# Test endpoints
https://your-project.vercel.app/api/health
https://your-project.vercel.app/api/jobs
https://your-project.vercel.app/
```

---

## 🔧 Troubleshooting

### Issue: "Module not found: flask"

**Solution:** Ensure `requirements.txt` is in `api/` folder

### Issue: "Credentials file not found"

**Solution:** 
1. Upload `credentials.json` to Vercel
2. Or use Vercel Secrets:
   ```bash
   vercel secrets add credentials-json "$(cat credentials.json)"
   ```

### Issue: "Function timeout"

**Solution:** Increase timeout in `vercel.json`:
```json
{
  "functions": {
    "api/**/*.py": {
      "maxDuration": 60
    }
  }
}
```

### Issue: "CORS errors"

**Solution:** Already configured in `api/index.py` with Flask-CORS

### Issue: Static files not loading

**Solution:** Check routes in `vercel.json` - already configured

---

## 📊 Post-Deployment Checklist

- [ ] Environment variables added
- [ ] Credentials file uploaded
- [ ] Deployment successful
- [ ] Homepage loads (`/`)
- [ ] API health works (`/api/health`)
- [ ] Jobs list works (`/api/jobs`)
- [ ] Job detail works (`/job/<id>`)
- [ ] Static files load (CSS, JS)
- [ ] Auto-refresh works
- [ ] Mobile responsive

---

## 🔄 Auto-Deploy on Git Push

Once connected to Git:

```bash
# Make changes
git add .
git commit -m "Update dashboard"
git push

# Vercel automatically deploys!
```

**Preview Deployments:** Every push creates a preview URL

**Production Deployments:** Push to `main` branch deploys to production

---

## 🌐 Custom Domain (Optional)

1. Go to Project Settings → **Domains**
2. Add your domain
3. Update DNS records as shown
4. Wait for propagation (5-10 minutes)

---

## 💰 Vercel Pricing

**Hobby Plan (Free):**
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Serverless functions (60s timeout)
- ✅ Automatic SSL
- ✅ Custom domains

**Pro Plan ($20/month):**
- More bandwidth
- Longer timeouts
- Priority support

---

## 📈 Monitoring

### Vercel Dashboard

- **Analytics:** Traffic, performance
- **Logs:** Function logs, errors
- **Deployments:** Status, history

### Check Logs

```bash
# View deployment logs
vercel logs <deployment-url>

# Real-time logs
vercel logs --follow
```

---

## 🎯 Quick Commands

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# View logs
vercel logs

# List deployments
vercel ls

# Remove deployment
vercel rm <deployment-name>
```

---

## ✅ What's Already Configured

| Item | Status |
|------|--------|
| `vercel.json` | ✅ Created |
| API routes | ✅ Created |
| Static files config | ✅ Configured |
| Flask-CORS | ✅ Enabled |
| Requirements | ✅ In `api/requirements.txt` |
| .vercelignore | ✅ Created |
| Environment setup | ✅ Documented |

---

## 🚀 Deploy Now!

```bash
# Quick deploy
cd C:\linkedin_scraper
vercel login
vercel
vercel --prod
```

**Your dashboard will be live at:** `https://your-project.vercel.app`

---

**Last Updated:** April 1, 2026  
**Vercel Version:** 2.0  
**Python Version:** 3.11
