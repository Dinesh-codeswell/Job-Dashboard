"""
STRICT Production Dashboard: Supabase Primary
Fixes: 500 Internal Server Errors & 3-Day Sync
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dashboard.data.sheets_fetcher import get_data_fetcher
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent / 'data'))
    from sheets_fetcher import get_data_fetcher

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Config
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

def get_supabase():
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase Init Error: {e}")
    return None

def sanitize_job(job, source_type='supabase'):
    """Sanitize job data with unified keys that work for both sources."""
    import math
    
    def safe_str(value, default=''):
        """Safely convert to string, handling NaN/None."""
        if value is None:
            return default
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return default
        return str(value)
    
    if source_type == 'supabase':
        base = {
            'id': safe_str(job.get('id') or job.get('external_id')),
            'job_title': safe_str(job.get('job_title')),
            'company': safe_str(job.get('company')),
            'employment_type': safe_str(job.get('employment_type')),
            'location': safe_str(job.get('location')),
            'posted_date': safe_str(job.get('posted_date')),
            'posted_at_timestamp': job.get('posted_at_timestamp'),
            'search_city': safe_str(job.get('search_city')),
            'date_added': safe_str(job.get('date_added')),
            'company_logo': safe_str(job.get('company_logo')),
            'job_url': safe_str(job.get('job_url')),
            'job_description': safe_str(job.get('job_description')),
            'source': safe_str(job.get('source'), 'unknown')
        }
        # Add Sheets-compatible aliases for frontend compatibility
        return {
            **base,
            'Job Title': base['job_title'],
            'Company': base['company'],
            'Employment Type': base['employment_type'],
            'Location': base['location'],
            'Posted': base['posted_date'],
            'Job Description': base['job_description'],
            'Job URL': base['job_url'],
            'Company Logo': base['company_logo'],
            'Search City': base['search_city'],
            'Date Added': base['date_added']
        }
    
    # Sheets format
    base = {
        'id': safe_str(job.get('id')),
        'job_title': safe_str(job.get('Job Title', job.get('job_title'))),
        'company': safe_str(job.get('Company', job.get('company'))),
        'employment_type': safe_str(job.get('Employment Type', job.get('employment_type'))),
        'location': safe_str(job.get('Location', job.get('location'))),
        'posted_date': safe_str(job.get('Posted', job.get('posted_date'))),
        'posted_at_timestamp': job.get('posted_at_timestamp'),
        'search_city': safe_str(job.get('Search City', job.get('search_city'))),
        'date_added': safe_str(job.get('Date Added', job.get('date_added'))),
        'company_logo': safe_str(job.get('Company Logo') or job.get('company_logo')),
        'job_url': safe_str(job.get('Job URL', job.get('job_url'))),
        'job_description': safe_str(job.get('Job Description', job.get('job_description'))),
        'source': safe_str(job.get('source'), 'unknown')
    }
    # Add Sheets-style keys
    return {
        **base,
        'Job Title': base['job_title'],
        'Company': base['company'],
        'Employment Type': base['employment_type'],
        'Location': base['location'],
        'Posted': base['posted_date'],
        'Job Description': base['job_description'],
        'Job URL': base['job_url'],
        'Company Logo': base['company_logo'],
        'Search City': base['search_city'],
        'Date Added': base['date_added']
    }

# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/job/<job_id>')
def job_detail(job_id):
    return render_template('job_detail.html')

@app.route('/about')
def about():
    return render_template('about.html')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """
    Industry-standard job search API.
    - Multi-column search (title, company ONLY - not description)
    - Client-side filtering to avoid Supabase API limitations
    - Proper NaN handling for JSON serialization
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        search = request.args.get('search', '').strip()
        city = request.args.get('city', '').strip()
        emp_type = request.args.get('type', '').strip()

        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        supabase = get_supabase()

        if supabase:
            offset = (page - 1) * limit
            query = supabase.table("jobs").select("*", count="exact").gte("posted_at_timestamp", cutoff)

            if city:
                query = query.eq("search_city", city)
            if emp_type:
                query = query.ilike("employment_type", f"%{emp_type}%")

            # Client-side search to avoid Supabase API limitations
            if search:
                search_lower = search.lower()
                result = query.execute()
                
                if result.data:
                    # Filter: title + company ONLY
                    matched_jobs = [
                        job for job in result.data
                        if search_lower in (job.get('job_title') or '').lower()
                        or search_lower in (job.get('company') or '').lower()
                    ]
                    
                    # Client-side sort
                    matched_jobs.sort(
                        key=lambda x: x.get('posted_at_timestamp', ''),
                        reverse=True
                    )
                    
                    # Client-side pagination
                    start = offset
                    end = offset + limit
                    paginated = matched_jobs[start:end]
                    
                    return jsonify({
                        'success': True,
                        'source': 'supabase',
                        'jobs': [sanitize_job(j, 'supabase') for j in paginated],
                        'pagination': {
                            'page': page,
                            'limit': limit,
                            'total': len(matched_jobs),
                            'total_pages': (len(matched_jobs) + limit - 1) // limit if len(matched_jobs) else 1
                        }
                    })
            else:
                # No search - server-side ordering
                result = query.order("posted_at_timestamp", desc=True).range(offset, offset + limit - 1).execute()
                
                if result.data is not None:
                    return jsonify({
                        'success': True,
                        'source': 'supabase',
                        'jobs': [sanitize_job(j, 'supabase') for j in result.data],
                        'pagination': {
                            'page': page,
                            'limit': limit,
                            'total': result.count if result.count else 0,
                            'total_pages': (result.count + limit - 1) // limit if result.count else 1
                        }
                    })

        return jsonify({'success': False, 'error': 'Database connection failed'}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Return dashboard statistics with cities and companies count."""
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        supabase = get_supabase()
        
        if supabase:
            res = supabase.table("jobs").select("id, company, search_city", count="exact").gte("posted_at_timestamp", cutoff).execute()
            
            if res.data is not None:
                cities = {}
                companies = {}
                
                for job in res.data:
                    city = job.get('search_city', '')
                    if city:
                        cities[city] = cities.get(city, 0) + 1
                    
                    company = job.get('company', '')
                    if company:
                        companies[company] = companies.get(company, 0) + 1
                
                return jsonify({
                    'success': True,
                    'stats': {
                        'total_jobs': res.count if res.count else len(res.data),
                        'cities': dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:20]),
                        'companies': dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:20]),
                        'source': 'supabase'
                    }
                })
        
        return jsonify({'success': False, 'error': 'Supabase offline'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employment-types', methods=['GET'])
def get_employment_types():
    return jsonify({
        'success': True,
        'types': ['Full Time', 'Contract', 'Internship', 'Remote']
    })

@app.route('/api/cities', methods=['GET'])
def get_cities():
    return jsonify({
        'success': True,
        'cities': ['Bangalore', 'Mumbai', 'Chennai', 'Pune', 'Gurugram', 'Hyderabad', 'Remote']
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'source': 'supabase'})

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    app.run(host=host, port=port, debug=True)
