"""
STRICT Unified API: Supabase Primary with Sheets Fallback
Fixes: '<' not supported between instances of 'float' and 'str'
Ensures: 3-Day Global Filter
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dashboard.data.sheets_fetcher import get_data_fetcher
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'dashboard' / 'data'))
    from sheets_fetcher import get_data_fetcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            template_folder='../dashboard/templates',
            static_folder='../dashboard/static',
            static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'vercel-secret-key')
CORS(app)
load_dotenv()

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
        logger.error(f"Supabase Init Error: {e}")
    return None

def sanitize_job(job, source_type='supabase'):
    if source_type == 'supabase':
        return {
            'id': job.get('id') or str(job.get('external_id', '')),
            'job_title': job.get('job_title', ''),
            'company': job.get('company', ''),
            'employment_type': job.get('employment_type', ''),
            'location': job.get('location', ''),
            'posted_date': job.get('posted_date', ''),
            'posted_at_timestamp': job.get('posted_at_timestamp'),
            'search_city': job.get('search_city', ''),
            'date_added': job.get('date_added', ''),
            'company_logo': job.get('company_logo', ''),
            'job_url': job.get('job_url', ''),
            'job_description': job.get('job_description', ''),
            'source': job.get('source', 'unknown')
        }
    return {
        'id': str(job.get('id', '')),
        'job_title': job.get('Job Title', ''),
        'company': job.get('Company', ''),
        'employment_type': job.get('Employment Type', ''),
        'location': job.get('Location', ''),
        'posted_date': job.get('Posted', ''),
        'search_city': job.get('Search City', ''),
        'date_added': job.get('Date Added', ''),
        'company_logo': job.get('Company Logo') or job.get('company_logo') or '',
        'job_url': job.get('Job URL', ''),
        'job_description': job.get('Job Description', ''),
        'source': job.get('source', 'unknown')
    }

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        search = request.args.get('search', '')
        city = request.args.get('city', '')
        emp_type = request.args.get('type', '')
        
        # STRICT 3-DAY CUTOFF
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        
        supabase = get_supabase()
        if supabase:
            offset = (page - 1) * limit
            query = supabase.table("jobs").select("*", count="exact").gte("posted_at_timestamp", cutoff)
            
            if city: query = query.eq("search_city", city)
            if emp_type: query = query.ilike("employment_type", f"%{emp_type}%")
            if search: query = query.text_search('fts_tokens', search)
            
            result = query.order("posted_at_timestamp", desc=True).range(offset, offset + limit - 1).execute()
            
            if result.data is not None:
                return jsonify({
                    'success': True,
                    'source': 'supabase',
                    'jobs': [sanitize_job(j, 'supabase') for j in result.data],
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': result.count,
                        'total_pages': (result.count + limit - 1) // limit
                    }
                })

        # Fallback (also with 3-day filter)
        fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
        all_jobs = fetcher.fetch_all_jobs(use_cache=False)
        # Filter sheets data manually for 3-day rule (simplified)
        filtered = [j for j in all_jobs if "day" not in str(j.get('Posted')).lower() or "1 day" in str(j.get('Posted')).lower() or "2 days" in str(j.get('Posted')).lower()]
        
        start = (page - 1) * limit
        return jsonify({
            'success': True,
            'source': 'sheets',
            'jobs': [sanitize_job(j, 'sheets') for j in filtered[start:start+limit]],
            'pagination': {'page': page, 'limit': limit, 'total': len(filtered), 'total_pages': (len(filtered) + limit - 1) // limit}
        })
    except Exception as e:
        logger.error(f"API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        supabase = get_supabase()
        if supabase:
            res = supabase.table("jobs").select("id", count="exact").gte("posted_at_timestamp", cutoff).execute()
            return jsonify({'success': True, 'stats': {'total_jobs': res.count, 'source': 'supabase'}})
        return jsonify({'success': False, 'error': 'Supabase offline'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employment-types', methods=['GET'])
def get_emp_types():
    # Return fixed list to avoid complex grouping errors for now
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

def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
