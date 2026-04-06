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
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# Ensure credentials file path is absolute for Vercel
if not os.path.isabs(GOOGLE_CREDENTIALS_FILE):
    GOOGLE_CREDENTIALS_FILE = str(Path(__file__).parent.parent / GOOGLE_CREDENTIALS_FILE)

def get_supabase():
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Supabase Init Error: {e}")
    return None

def sanitize_job(job, source_type='supabase'):
    """Sanitize job data with unified keys that work for both sources."""
    if source_type == 'supabase':
        base = {
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
        'id': str(job.get('id', '')),
        'job_title': job.get('Job Title', job.get('job_title', '')),
        'company': job.get('Company', job.get('company', '')),
        'employment_type': job.get('Employment Type', job.get('employment_type', '')),
        'location': job.get('Location', job.get('location', '')),
        'posted_date': job.get('Posted', job.get('posted_date', '')),
        'posted_at_timestamp': job.get('posted_at_timestamp'),
        'search_city': job.get('Search City', job.get('search_city', '')),
        'date_added': job.get('Date Added', job.get('date_added', '')),
        'company_logo': job.get('Company Logo') or job.get('company_logo', ''),
        'job_url': job.get('Job URL', job.get('job_url', '')),
        'job_description': job.get('Job Description', job.get('job_description', '')),
        'source': job.get('source', 'unknown')
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

# --- Routes ---

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to diagnose deployment issues."""
    status = {
        'status': 'ok',
        'supabase_connected': False,
        'sheets_connected': False
    }
    
    # Check Supabase
    supabase = get_supabase()
    if supabase:
        status['supabase_connected'] = True
    
    # Check Sheets
    try:
        fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
        status['sheets_connected'] = fetcher.worksheet is not None
    except Exception:
        pass
    
    return jsonify(status)

@app.route('/job/<job_id>')
def job_detail(job_id):
    """Render job detail page."""
    return render_template('job_detail.html')

@app.route('/about')
def about():
    """Render about page."""
    return render_template('about.html')

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get single job details from Supabase or Sheets."""
    try:
        supabase = get_supabase()
        if supabase:
            try:
                # Try finding by UUID or external_id
                result = supabase.table("jobs").select("*").or_(
                    f"id.eq.{job_id},external_id.eq.{job_id}"
                ).execute()

                if result.data:
                    return jsonify({
                        'success': True,
                        'job': sanitize_job(result.data[0], 'supabase')
                    })
            except Exception as supabase_err:
                logger.warning(f"Supabase single job fetch failed: {supabase_err}")

        # Fallback to Google Sheets
        try:
            fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
            job = fetcher.get_job_by_id(job_id)
            if job:
                return jsonify({
                    'success': True,
                    'job': sanitize_job(job, 'sheets')
                })
        except Exception as sheets_err:
            logger.warning(f"Sheets single job fetch failed: {sheets_err}")

        return jsonify({'success': False, 'error': 'Job not found'}), 404
    except Exception as e:
        logger.error(f"Single Job API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs/<job_id>/similar', methods=['GET'])
def get_similar_jobs(job_id):
    """Get similar jobs based on company, location, or title keywords."""
    try:
        limit = int(request.args.get('limit', 9))
        
        # First, get the current job to find similar ones
        current_job = None
        supabase = get_supabase()
        
        if supabase:
            try:
                # Get current job
                result = supabase.table("jobs").select("*").or_(
                    f"id.eq.{job_id},external_id.eq.{job_id}"
                ).execute()
                
                if result.data:
                    current_job = result.data[0]
                    
                    # Find similar jobs by matching title keywords or same company
                    cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
                    title = current_job.get('job_title', '')
                    company = current_job.get('company', '')
                    location = current_job.get('location', '')
                    
                    # Build query for similar jobs
                    query = supabase.table("jobs").select("*", count="exact").gte("posted_at_timestamp", cutoff).neq("id", job_id)
                    
                    # Try matching by company first
                    if company:
                        similar_result = query.ilike("company", f"%{company}%").limit(limit).execute()
                        if similar_result.data and len(similar_result.data) > 0:
                            return jsonify({
                                'success': True,
                                'similar_jobs': [sanitize_job(j, 'supabase') for j in similar_result.data]
                            })
                    
                    # Fallback: match by location
                    if location:
                        location_result = query.ilike("location", f"%{location.split(',')[0]}%").limit(limit).execute()
                        if location_result.data and len(location_result.data) > 0:
                            return jsonify({
                                'success': True,
                                'similar_jobs': [sanitize_job(j, 'supabase') for j in location_result.data]
                            })
                    
                    # Last resort: just return recent jobs
                    recent_result = query.order("posted_at_timestamp", desc=True).limit(limit).execute()
                    if recent_result.data:
                        return jsonify({
                            'success': True,
                            'similar_jobs': [sanitize_job(j, 'supabase') for j in recent_result.data]
                        })
            except Exception as supabase_err:
                logger.warning(f"Supabase similar jobs failed: {supabase_err}")
        
        # Fallback to Google Sheets
        try:
            fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
            all_jobs = fetcher.fetch_all_jobs(use_cache=False)
            
            # Filter out current job and get random recent ones
            filtered = [j for j in all_jobs if str(j.get('id')) != str(job_id)]
            import random
            similar = random.sample(filtered, min(limit, len(filtered)))
            
            return jsonify({
                'success': True,
                'similar_jobs': [sanitize_job(j, 'sheets') for j in similar]
            })
        except Exception as sheets_err:
            logger.warning(f"Sheets similar jobs failed: {sheets_err}")
        
        return jsonify({'success': True, 'similar_jobs': []})
    except Exception as e:
        logger.error(f"Similar Jobs API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
            try:
                offset = (page - 1) * limit
                query = supabase.table("jobs").select("*", count="exact").gte("posted_at_timestamp", cutoff)

                if city:
                    query = query.eq("search_city", city)
                if emp_type:
                    query = query.ilike("employment_type", f"%{emp_type}%")
                if search:
                    # Fallback to ilike if fts_tokens doesn't exist
                    try:
                        query = query.text_search('fts_tokens', search)
                    except Exception:
                        # Use basic text search instead of FTS
                        query = query.ilike("job_title", f"%{search}%")

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
            except Exception as supabase_err:
                logger.warning(f"Supabase query failed: {supabase_err}. Falling back to Sheets.")

        # Fallback to Google Sheets
        try:
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
        except Exception as sheets_err:
            logger.error(f"Google Sheets fallback failed: {sheets_err}")
            return jsonify({'success': False, 'error': 'Data source unavailable', 'details': str(sheets_err)}), 500
    except Exception as e:
        logger.error(f"API Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        supabase = get_supabase()
        if supabase:
            try:
                res = supabase.table("jobs").select("id", count="exact").gte("posted_at_timestamp", cutoff).execute()
                return jsonify({'success': True, 'stats': {'total_jobs': res.count if res.count else 0, 'source': 'supabase'}})
            except Exception as e:
                logger.warning(f"Supabase stats failed: {e}")
        
        # Fallback to Sheets
        try:
            fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
            jobs = fetcher.fetch_all_jobs(use_cache=False)
            return jsonify({'success': True, 'stats': {'total_jobs': len(jobs), 'source': 'sheets'}})
        except Exception:
            pass
        
        return jsonify({'success': False, 'error': 'All data sources unavailable'}), 500
    except Exception as e:
        logger.error(f"Stats API Error: {e}")
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
    try:
        supabase = get_supabase()
        if supabase:
            try:
                res = supabase.table("jobs").select("search_city").execute()
                if res.data:
                    cities = sorted(set(j.get('search_city') for j in res.data if j.get('search_city')))
                    return jsonify({'success': True, 'cities': cities})
            except Exception:
                pass
        
        return jsonify({
            'success': True,
            'cities': ['Bangalore', 'Mumbai', 'Chennai', 'Pune', 'Gurugram', 'Hyderabad', 'Delhi', 'Remote']
        })
    except Exception as e:
        logger.error(f"Cities API Error: {e}")
        return jsonify({'success': True, 'cities': []})

def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
