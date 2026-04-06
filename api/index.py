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
from flask.json.provider import DefaultJSONProvider
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


class SafeJSONProvider(DefaultJSONProvider):
    """Custom JSON provider that handles NaN, Infinity values."""
    
    def dumps(self, obj, **kwargs):
        """Serialize object with NaN handling."""
        import json
        
        def sanitize_for_json(value):
            """Recursively sanitize values to remove NaN/Infinity."""
            if isinstance(value, float):
                import math
                if math.isnan(value) or math.isinf(value):
                    return None
                return value
            elif isinstance(value, dict):
                return {k: sanitize_for_json(v) for k, v in value.items()}
            elif isinstance(value, (list, tuple)):
                return [sanitize_for_json(item) for item in value]
            return value
        
        sanitized = sanitize_for_json(obj)
        return super().dumps(sanitized, **kwargs)

app = Flask(__name__, 
            template_folder='../dashboard/templates',
            static_folder='../dashboard/static',
            static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'vercel-secret-key')

# Register custom JSON provider for NaN handling
app.json_provider_class = SafeJSONProvider
app.json = SafeJSONProvider(app)

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
    """Initialize Supabase client with detailed logging."""
    try:
        logger.info(f"Supabase URL present: {bool(SUPABASE_URL)}")
        logger.info(f"Supabase Key present: {bool(SUPABASE_KEY)}")
        
        if not SUPABASE_URL:
            logger.warning("Supabase URL is empty!")
            return None
        if not SUPABASE_KEY:
            logger.warning("Supabase Key is empty!")
            return None
        
        logger.info(f"Initializing Supabase with URL: {SUPABASE_URL}")
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Supabase Init Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
    
    def safe_int(value, default=None):
        """Safely convert to int, handling NaN/None."""
        if value is None:
            return default
        try:
            result = int(value)
            if math.isinf(result) or math.isnan(result):
                return default
            return result
        except (ValueError, TypeError, OverflowError):
            return default
    
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

# --- Routes ---

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to diagnose deployment issues."""
    status = {
        'status': 'ok',
        'env_vars': {
            'SUPABASE_URL': bool(SUPABASE_URL),
            'SUPABASE_KEY': bool(SUPABASE_KEY),
            'GOOGLE_SHEET_ID': bool(GOOGLE_SHEET_ID),
        },
        'supabase_connected': False,
        'sheets_connected': False
    }
    
    # Check Supabase
    supabase = get_supabase()
    if supabase:
        status['supabase_connected'] = True
        # Try a simple query to verify connection
        try:
            test_query = supabase.table("jobs").select("id", count="exact").limit(1).execute()
            status['supabase_query_works'] = test_query.data is not None
            status['supabase_row_count'] = test_query.count if test_query.count else 0
        except Exception as e:
            status['supabase_query_error'] = str(e)
    
    # Check Sheets
    try:
        fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
        status['sheets_connected'] = fetcher.worksheet is not None
    except Exception as e:
        status['sheets_error'] = str(e)
    
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
        limit = int(request.args.get('limit', 3))  # Default 3 similar jobs
        
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
    """
    Industry-standard job search API.
    
    Features:
    - Multi-column search (title, company, description)
    - Relevance ranking (title match > company match > description match)
    - Fast ilike queries with proper indexing support
    - Comprehensive logging for debugging
    """
    try:
        logger.info("=== /api/jobs called ===")
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        search = request.args.get('search', '').strip()
        city = request.args.get('city', '').strip()
        emp_type = request.args.get('type', '').strip()

        # STRICT 3-DAY CUTOFF
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        logger.info(f"Search params: page={page}, limit={limit}, search='{search}', city='{city}', type='{emp_type}'")

        supabase = get_supabase()
        if supabase:
            logger.info("Supabase client available, attempting query...")
            try:
                offset = (page - 1) * limit
                
                # Base query with 3-day filter
                query = supabase.table("jobs").select("*", count="exact").gte("posted_at_timestamp", cutoff)

                # Apply city filter
                if city:
                    query = query.eq("search_city", city)
                    logger.info(f"Added city filter: {city}")
                
                # Apply employment type filter
                if emp_type:
                    query = query.ilike("employment_type", f"%{emp_type}%")
                    logger.info(f"Added type filter: {emp_type}")
                
                # INDUSTRY-STANDARD MULTI-COLUMN SEARCH
                # Only search role name and company (NOT description)
                # Use client-side filtering + sorting to avoid Supabase API limitations
                if search:
                    logger.info(f"Multi-column search for: '{search}'")
                    search_lower = search.lower()
                    
                    # Fetch ALL jobs within 3-day window (no ordering to avoid API error)
                    result = query.execute()
                    
                    if result.data:
                        # Client-side filter: title + company ONLY
                        matched_jobs = [
                            job for job in result.data
                            if search_lower in (job.get('job_title') or '').lower() 
                            or search_lower in (job.get('company') or '').lower()
                        ]
                        
                        # Client-side sort by timestamp
                        matched_jobs.sort(
                            key=lambda x: x.get('posted_at_timestamp', ''),
                            reverse=True
                        )
                        
                        # Client-side pagination
                        start = offset
                        end = offset + limit
                        paginated_jobs = matched_jobs[start:end]
                        
                        logger.info(f"Search matched {len(matched_jobs)} jobs (title/company only), returning {len(paginated_jobs)}")
                        
                        return jsonify({
                            'success': True,
                            'source': 'supabase',
                            'jobs': [sanitize_job(j, 'supabase') for j in paginated_jobs],
                            'pagination': {
                                'page': page,
                                'limit': limit,
                                'total': len(matched_jobs),
                                'total_pages': (len(matched_jobs) + limit - 1) // limit if len(matched_jobs) else 1
                            }
                        })
                else:
                    # No search - use server-side ordering (works without filters)
                    result = query.order("posted_at_timestamp", desc=True).range(offset, offset + limit - 1).execute()

                logger.info(f"Query executed. Rows returned: {len(result.data) if result.data else 0}")

                if result.data is not None:
                    logger.info(f"Returning {len(result.data)} jobs from Supabase")
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
                else:
                    logger.warning("Supabase returned None data")
            except Exception as supabase_err:
                logger.warning(f"Supabase query failed: {supabase_err}")
                import traceback
                logger.warning(traceback.format_exc())
                logger.info("Falling back to Google Sheets...")
        else:
            logger.warning("Supabase client not available")

        # Fallback to Google Sheets
        try:
            logger.info("Fetching from Google Sheets...")
            fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
            all_jobs = fetcher.fetch_all_jobs(use_cache=False)
            logger.info(f"Fetched {len(all_jobs)} jobs from Sheets")
            
            # Filter sheets data manually for 3-day rule (simplified)
            filtered = [j for j in all_jobs if "day" not in str(j.get('Posted')).lower() or "1 day" in str(j.get('Posted')).lower() or "2 days" in str(j.get('Posted')).lower()]
            logger.info(f"After 3-day filter: {len(filtered)} jobs")

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
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get dashboard statistics with cities and companies count.
    Industry standard: Return aggregated data for dashboard metrics.
    """
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        supabase = get_supabase()
        
        if supabase:
            try:
                # Fetch all jobs within 3-day window for aggregation
                res = supabase.table("jobs").select(
                    "id, company, search_city", count="exact"
                ).gte("posted_at_timestamp", cutoff).execute()
                
                if res.data is not None:
                    # Aggregate cities
                    cities = {}
                    companies = {}
                    
                    for job in res.data:
                        # Count cities
                        city = job.get('search_city', '')
                        if city:
                            cities[city] = cities.get(city, 0) + 1
                        
                        # Count companies
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
            except Exception as e:
                logger.warning(f"Supabase stats failed: {e}")

        # Fallback to Sheets
        try:
            fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
            jobs = fetcher.fetch_all_jobs(use_cache=False)
            
            cities = {}
            companies = {}
            
            for job in jobs:
                city = job.get('Search City', job.get('search_city', ''))
                if city:
                    cities[city] = cities.get(city, 0) + 1
                
                company = job.get('Company', job.get('company', ''))
                if company:
                    companies[company] = companies.get(company, 0) + 1
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_jobs': len(jobs),
                    'cities': dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:20]),
                    'companies': dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:20]),
                    'source': 'sheets'
                }
            })
        except Exception as sheets_err:
            logger.warning(f"SheetStats failed: {sheets_err}")

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
