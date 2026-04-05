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

        # Fallback
        return jsonify({'success': False, 'error': 'Database connection failed'}), 503
    except Exception as e:
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
