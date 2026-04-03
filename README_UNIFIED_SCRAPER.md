# 🚀 Quick Start: Unified India Jobs Scraper

## One Command to Scrape All Platforms

```bash
python scrape_all_india_jobs.py
```

That's it! This will:
- ✅ Scrape **LinkedIn**, **Indeed**, and **Naukri**
- ✅ Filter jobs from past **48 hours**
- ✅ Search **6 Tier 1 cities**
- ✅ Upload to **Google Sheets** automatically
- ✅ Skip **duplicates** across platforms

---

## ⚡ 3-Minute Setup

### Step 1: Install Dependencies (1 min)

```bash
pip install -r requirements.txt
```

### Step 2: Configure .env (1 min)

```bash
# Copy example
cp .env.example .env

# Edit .env with your credentials
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password
GOOGLE_SHEET_ID=your-sheet-id
GOOGLE_CREDENTIALS_FILE=credentials.json
```

### Step 3: First Run (1 min)

```bash
# First run: visible browser to login to LinkedIn
python scrape_all_india_jobs.py --headless False

# Login to LinkedIn when browser opens
# Session will be saved for future runs
```

---

## 📊 Expected Results

### Typical Run Statistics

| Metric | Value |
|--------|-------|
| **Total Jobs** | 80-150 |
| **LinkedIn** | 40-70 jobs |
| **Indeed** | 25-45 jobs |
| **Naukri** | 20-40 jobs |
| **Time** | 25-35 minutes |
| **Success Rate** | 80-90% |

### Google Sheets Output

Creates 4 worksheets:
1. **LinkedIn_Jobs** - Jobs from LinkedIn
2. **Indeed_Jobs** - Jobs from Indeed
3. **Naukri_Jobs** - Jobs from Naukri
4. **Summary** - Run statistics

---

## 🎯 Common Use Cases

### Daily Quick Scan (10 min)

```bash
python scrape_all_india_jobs.py \
  --platforms indeed naukari \
  --max-days 1 \
  --limit-per-city 5
```

### Regular Scraping (30 min) ⭐ RECOMMENDED

```bash
python scrape_all_india_jobs.py
```

### Comprehensive Search (60 min)

```bash
python scrape_all_india_jobs.py \
  --max-days 7 \
  --limit-per-city 20
```

### LinkedIn Only (20 min)

```bash
python scrape_all_india_jobs.py --platforms linkedin
```

### Indeed + Naukri Only (10 min)

```bash
python scrape_all_india_jobs.py --platforms indeed naukari
```

---

## 🔧 Troubleshooting

### "Session expired"

```bash
python scrape_all_india_jobs.py --headless False
# Login to LinkedIn in browser
```

### "No jobs found"

```bash
# Increase job age filter
python scrape_all_india_jobs.py --max-days 5

# Broaden search
python scrape_all_india_jobs.py --limit-per-city 15
```

### "Google Sheets connection failed"

```bash
# Check credentials file exists
ls -la credentials.json

# Verify sheet ID
echo $GOOGLE_SHEET_ID
```

---

## 📋 Command Reference

| Command | Description |
|---------|-------------|
| `python scrape_all_india_jobs.py` | Default: all platforms, 48hrs, Tier 1 |
| `--platforms linkedin indeed` | Select platforms |
| `--max-days 3` | Jobs from past 3 days |
| `--limit-per-city 15` | More jobs per search |
| `--tier-1-only` | Top 6 cities only |
| `--cities Bangalore Mumbai` | Specific cities |
| `--no-internships` | Exclude internships |
| `--headless False` | Visible browser |

---

## 📈 Optimization Tips

1. **Start Small**: First run with `--limit-per-city 5`
2. **Use Tier 1**: `--tier-1-only` for best jobs
3. **48-Hour Filter**: `--max-days 2` for freshness
4. **Regular Runs**: Every 2-3 days for best results
5. **Monitor Logs**: Watch console for errors

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| `UNIFIED_SCRAPER_GUIDE.md` | Complete user guide |
| `UNIFIED_SCRAPER_ANALYSIS.md` | Technical analysis |
| `JOB_STORAGE_GUIDE.md` | Storage options |
| `INDEED_NAUKRI_INTEGRATION.md` | API details |

---

## 🎯 Next Steps

1. **Test Run**: `python scrape_all_india_jobs.py --headless False`
2. **Verify**: Check Google Sheets for output
3. **Schedule**: Set up regular runs (every 2-3 days)
4. **Optimize**: Adjust limits based on results

---

**Happy Job Scraping! 🚀**

For questions or issues, check the detailed guides or console logs.
