# Consulting Jobs Dashboard - Technical Architecture

## Overview
A real-time web dashboard that displays consulting jobs scraped from LinkedIn and stored in Google Sheets.

## Tech Stack

### Backend
- **Flask** - Lightweight Python web framework
- **Flask-CORS** - Enable cross-origin requests
- **GSpread** - Google Sheets API integration
- **Threading** - Background data refresh

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **Vanilla JavaScript** - No framework dependencies
- **Fetch API** - Async API calls
- **LocalStorage** - Cache for offline support

### Real-time Updates
- **Auto-polling** - Refresh data every 60 seconds
- **Manual refresh** - User-triggered update
- **Last updated timestamp** - Show freshness

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Google Sheets │────▶│   Flask Backend  │────▶│  Frontend Dashboard │
│   (Data Source) │     │   (API Server)   │     │  (HTML/CSS/JS)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Background      │
                        │  Data Refresh    │
                        └──────────────────┘
```

## API Endpoints

### 1. GET /api/jobs
Fetch all jobs with pagination
- Query Params: `page`, `limit`, `search`, `city`, `type`
- Response: `{ jobs: [], total: 0, page: 1, pages: 1 }`

### 2. GET /api/jobs/<job_id>
Fetch single job details
- Response: `{ job: {...} }`

### 3. GET /api/stats
Dashboard statistics
- Response: `{ total_jobs: 0, cities: {}, types: {}, last_updated: "" }`

### 4. GET /api/refresh
Trigger manual data refresh
- Response: `{ success: true, count: 0 }`

### 5. GET /api/cities
List of all cities
- Response: `{ cities: [] }`

### 6. GET /api/employment-types
List of employment types
- Response: `{ types: [] }`

## Data Flow

1. **Initial Load**
   - Frontend requests `/api/jobs?page=1&limit=30`
   - Backend fetches from Google Sheets
   - Returns paginated results
   - Frontend renders job cards

2. **Real-time Update**
   - Frontend polls `/api/stats` every 60 seconds
   - If `last_updated` changed, fetch new jobs
   - Show "New jobs available" notification
   - User can refresh or auto-refresh triggers

3. **Job Detail View**
   - User clicks job card
   - Navigate to `/job/<job_id>`
   - Backend fetches full job details
   - Render complete job description with Apply button

## Database Schema (Google Sheets)

| Column | Type | Description |
|--------|------|-------------|
| Job Title | String | Position title |
| Employment Type | String | Full-time/Part-time/etc |
| Posted | String | Time ago |
| Location | String | Job location |
| Job Description | String | Complete JD |
| Job URL | String | LinkedIn URL |
| Search City | String | City searched |
| Date Added | DateTime | When scraped |

## Frontend Pages

### 1. Home/Dashboard (`/`)
- Search bar
- Filter dropdowns (City, Type)
- Job cards grid (30 per page)
- Pagination controls
- Stats summary
- Last updated timestamp
- Auto-refresh indicator

### 2. Job Detail (`/job/<id>`)
- Job title
- Company name
- Employment type badge
- Location
- Posted date
- Complete job description
- Apply button (opens LinkedIn URL)
- Back to dashboard button
- Share button

### 3. About/Help (`/about`)
- Dashboard info
- How to use
- Data source info

## UI/UX Design

### Color Scheme
- Primary: #2563eb (Blue)
- Secondary: #7c3aed (Purple)
- Success: #10b981 (Green)
- Background: #f8fafc (Light Gray)
- Card Background: #ffffff (White)
- Text: #1e293b (Dark Gray)

### Components
- **Job Card**: Title, Company, Location, Type badge, Posted time
- **Search Bar**: Full-width with icon
- **Filter Dropdown**: City, Employment Type
- **Pagination**: Previous, Page numbers, Next
- **Stats Cards**: Total Jobs, Cities, Companies
- **Loading Spinner**: During data fetch
- **Toast Notification**: For updates/errors

### Responsive Design
- Desktop: 3 columns grid
- Tablet: 2 columns grid
- Mobile: 1 column grid

## Performance Optimization

1. **Caching**
   - Cache Google Sheets data for 60 seconds
   - LocalStorage for offline viewing
   - Debounce search input

2. **Lazy Loading**
   - Load job details on demand
   - Infinite scroll option (future)

3. **Optimization**
   - Minify CSS/JS for production
   - Compress images
   - Use CDN for dependencies

## Security

1. **API Security**
   - Rate limiting (100 requests/minute)
   - CORS configuration
   - Input validation

2. **Data Security**
   - Google Sheets credentials in .env
   - No sensitive data in frontend
   - HTTPS in production

## Deployment Options

### Local Development
```bash
python app.py
# Open http://localhost:5000
```

### Production (Options)
1. **Heroku** - Easy Flask deployment
2. **Vercel** - Serverless functions
3. **AWS EC2** - Full control
4. **DigitalOcean** - Simple VPS

## File Structure

```
dashboard/
├── app.py                  # Flask server
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── config.py              # Configuration
├── data/
│   └── sheets_fetcher.py  # Google Sheets integration
├── api/
│   └── routes.py          # API endpoints
├── static/
│   ├── css/
│   │   └── style.css      # Styles
│   └── js/
│       ├── main.js        # Dashboard logic
│       ├── api.js         # API calls
│       └── utils.js       # Utilities
└── templates/
    ├── index.html         # Home page
    ├── job_detail.html    # Job detail page
    └── about.html         # About page
```

## Features Checklist

### Phase 1 (Core)
- [x] Planning
- [ ] Backend API
- [ ] Frontend Dashboard
- [ ] Job Cards
- [ ] Pagination
- [ ] Job Detail Page

### Phase 2 (Enhanced)
- [ ] Real-time Updates
- [ ] Search Functionality
- [ ] Filter by City/Type
- [ ] Stats Dashboard

### Phase 3 (Polish)
- [ ] Responsive Design
- [ ] Loading States
- [ ] Error Handling
- [ ] Share Functionality

## Future Enhancements

1. **Advanced Filters**
   - Experience level
   - Salary range
   - Date posted
   - Company size

2. **User Features**
   - Save jobs
   - Job alerts
   - Application tracking

3. **Analytics**
   - Job trends
   - Salary insights
   - Company ratings

4. **Integrations**
   - Email notifications
   - Slack alerts
   - RSS feed
