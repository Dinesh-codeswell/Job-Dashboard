# 🕐 Dynamic Timeline Fix

## Problem

**Before:** Job timelines were **STATIC** - showed the exact text stored when scraped:
- Scraped at 4:00 PM → Shows `"4 hours ago"`
- User views at 6:00 PM → Still shows `"4 hours ago"` ❌

**After:** Job timelines are **DYNAMIC** - always calculate from the actual timestamp:
- Scraped at 4:00 PM → Shows `"4 hours ago"`
- User views at 6:00 PM → Shows `"6 hours ago"` ✅
- User views next day → Shows `"1d ago"` ✅

---

## How It Works

### **Data Flow:**

```
1. LinkedIn Scraper → "4 hours ago" (relative text)
2. sync_engine.py   → Converts to "2026-04-06T11:00:00+00:00" (ISO timestamp)
3. Supabase         → Stores both:
   - posted_date: "4 hours ago" (original text)
   - posted_at_timestamp: "2026-04-06T11:00:00+00:00" (proper timestamp)
4. API            → Sends both to frontend
5. Frontend       → Uses posted_at_timestamp for DYNAMIC calculation
```

### **Frontend Logic:**

```javascript
// OLD (static):
Utils.formatRelativeTime(job.posted_date)
// "4 hours ago" → returns "4 hours ago" (AS-IS)

// NEW (dynamic):
Utils.formatRelativeTime(job.posted_date, job.posted_at_timestamp)
// Uses posted_at_timestamp → calculates from current time → "4h ago", "6h ago", "1d ago"
```

---

## Files Changed

| File | Change |
|------|--------|
| `dashboard/static/js/utils.js` | Updated `formatRelativeTime()` to accept timestamp parameter |
| `dashboard/static/js/main.js` | Pass `posted_at_timestamp` to format function |
| `dashboard/templates/job_detail.html` | Use dynamic time for job detail + similar jobs |

---

## How The Calculation Works

```javascript
Utils.formatRelativeTime("4 hours ago", "2026-04-06T11:00:00+00:00")
                              ↓
                    posted_at_timestamp exists
                              ↓
                    formatDate("2026-04-06T11:00:00+00:00")
                              ↓
                    const now = new Date(); // Current time
                    const date = new Date("2026-04-06T11:00:00+00:00");
                    const diffInHours = (now - date) / (1000 * 60 * 60);
                              ↓
                    if (diffInHours < 24) return `${diffInHours}h ago`;
                    // Returns "6h ago" if 2 hours passed since scrape
```

---

## Display Formats

| Time Difference | Display |
|-----------------|---------|
| < 1 minute | `Just now` |
| 1-59 minutes | `45m ago` |
| 1-23 hours | `6h ago` |
| 1-6 days | `2d ago` |
| 7+ days | `Apr 6, 2026` |

---

## Benefits

✅ **Always accurate** - Updates in real-time based on current time  
✅ **No re-scraping needed** - Uses stored timestamp  
✅ **Graceful fallback** - If no timestamp, shows original text  
✅ **Consistent across pages** - Works on main page + job detail + similar jobs  

---

## Testing

1. Scrape a job now
2. Check dashboard → Shows `"Just now"` or `"0h ago"`
3. Wait 1 hour
4. Refresh page → Shows `"1h ago"` ✅
5. Wait 24 hours → Shows `"1d ago"` ✅

---

**Your timeline is now fully dynamic!** 🎉
