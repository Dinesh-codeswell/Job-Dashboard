# Consulting Jobs Dashboard - India

A real-time web dashboard for displaying consulting job opportunities across India, sourced from LinkedIn and stored in Google Sheets.

![Dashboard Preview](preview.png)

## Features

✅ **Real-time Job Listings** - Automatically fetches jobs from Google Sheets  
✅ **Search & Filter** - Search by keywords, filter by city and employment type  
✅ **Pagination** - 30 jobs per page with smooth navigation  
✅ **Job Details** - Complete job descriptions with direct application links  
✅ **Auto-refresh** - Updates every 60 seconds automatically  
✅ **Responsive Design** - Works on desktop, tablet, and mobile  
✅ **Share Functionality** - Easy job sharing  
✅ **Statistics Dashboard** - View total jobs, cities, and companies  

## Quick Start

### 1. Install Dependencies

```bash
cd dashboard
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env and add your Google Sheet ID
# (The Sheet ID is already configured from your setup)
```

### 3. Run the Dashboard

```bash
python app.py
```

### 4. Open in Browser

```
http://localhost:5000
```

## Project Structure

```
dashboard/
├── app.py                      # Flask application server
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── .env.example               # Example environment file
├── ARCHITECTURE.md            # Technical architecture docs
├── README.md                  # This file
│
├── data/
│   ├── __init__.py
│   └── sheets_fetcher.py      # Google Sheets integration
│
├── static/
│   ├── css/
│   │   └── style.css          # Dashboard styles
│   └── js/
│       ├── api.js             # API client
│       ├── utils.js           # Utility functions
│       └── main.js            # Dashboard logic
│
└── templates/
    ├── index.html             # Home/dashboard page
    ├── job_detail.html        # Job detail page
    ├── about.html             # About page
    ├── 404.html               # 404 error page
    └── 500.html               # 500 error page
```

## API Endpoints

### GET /api/jobs
Get paginated list of jobs

**Query Parameters:**
- `page` - Page number (default: 1)
- `limit` - Jobs per page (default: 30)
- `search` - Search query
- `city` - Filter by city
- `type` - Filter by employment type

**Response:**
```json
{
  "success": true,
  "jobs": [...],
  "pagination": {
    "page": 1,
    "limit": 30,
    "total": 150,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "filters": {...}
}
```

### GET /api/jobs/<job_id>
Get single job details

### GET /api/stats
Get dashboard statistics

### GET /api/cities
Get list of all cities

### GET /api/employment-types
Get list of employment types

### POST /api/refresh
Manually refresh data from Google Sheets

### GET /api/health
Health check endpoint

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-key` |
| `DEBUG` | Debug mode | `True` |
| `PORT` | Server port | `5000` |
| `HOST` | Server host | `0.0.0.0` |
| `GOOGLE_SHEET_ID` | Google Sheet ID | Required |
| `GOOGLE_CREDENTIALS_FILE` | Credentials file path | `credentials.json` |
| `WORKSHEET_NAME` | Worksheet name | `Consulting_Jobs_India` |
| `JOBS_PER_PAGE` | Pagination limit | `30` |
| `AUTO_REFRESH_INTERVAL` | Auto-refresh seconds | `60` |

## Usage

### Browsing Jobs

1. Open the dashboard at `http://localhost:5000`
2. View jobs in the grid (30 per page)
3. Use pagination to navigate

### Searching & Filtering

1. **Search**: Type keywords in the search bar (searches title, company, description)
2. **Filter by City**: Select a city from the dropdown
3. **Filter by Type**: Select employment type (Full-time, Part-time, etc.)
4. Click "Apply" to apply filters
5. Click "Clear" to reset all filters

### Viewing Job Details

1. Click on any job card
2. View complete job description
3. Click "Apply Now" to open LinkedIn application page

### Auto-Refresh

- Dashboard automatically refreshes data every 60 seconds
- Countdown timer shows time until next refresh
- Click "Refresh" button for manual refresh
- New jobs notification appears when data updates

## Deployment

### Local Development

```bash
python app.py
# Open http://localhost:5000
```

### Production (Heroku)

1. Create `Procfile`:
```
web: python app.py
```

2. Deploy:
```bash
heroku create your-app-name
heroku config:set GOOGLE_SHEET_ID=your_sheet_id
git push heroku main
```

### Production (Docker)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t jobs-dashboard .
docker run -p 5000:5000 jobs-dashboard
```

## Troubleshooting

### Dashboard not loading jobs

1. Check if Google Sheet ID is correct in `.env`
2. Verify `credentials.json` exists
3. Check Flask console for errors
4. Run health check: `http://localhost:5000/api/health`

### Auto-refresh not working

1. Check browser console for errors
2. Verify API is responding
3. Check network tab for failed requests

### Jobs not appearing

1. Verify Google Sheet has data
2. Check worksheet name matches `.env`
3. Clear browser cache
4. Click manual refresh button

## Performance Tips

1. **Reduce JOBS_PER_PAGE** if loading is slow
2. **Increase AUTO_REFRESH_INTERVAL** to reduce API calls
3. **Enable caching** in production
4. **Use CDN** for static assets in production

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Opera

## Security Notes

⚠️ **For Production:**
- Change `SECRET_KEY` to a random secure value
- Set `DEBUG=False`
- Use HTTPS
- Add rate limiting
- Validate all inputs
- Keep credentials secure

## License

Apache License 2.0

## Support

For issues or questions:
1. Check `ARCHITECTURE.md` for technical details
2. Review Flask console logs
3. Check browser console for frontend errors

---

**Built with ❤️ for Consulting Jobs in India**
