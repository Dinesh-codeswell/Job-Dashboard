"""
Vercel Serverless API for Consulting Jobs Dashboard
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Create Flask app FIRST before any imports
app = Flask(__name__, 
            template_folder='../dashboard/templates',
            static_folder='../dashboard/static',
            static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'vercel-secret-key')
CORS(app)

# Load environment variables
os.environ.setdefault('GOOGLE_SHEET_ID', '')
os.environ.setdefault('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
os.environ.setdefault('WORKSHEET_NAME', 'LinkedIn_Jobs')  # Deprecated - now fetches from all sheets

# Lazy load data fetcher
_fetcher = None
_fetcher_error = None

def get_fetcher():
    """Get or create data fetcher instance (unified - fetches from all 3 sheets)."""
    global _fetcher, _fetcher_error

    if _fetcher is not None:
        return _fetcher

    if _fetcher_error is not None:
        return None

    try:
        from dotenv import load_dotenv
        load_dotenv()

        # Import the UNIFIED data fetcher that fetches from all 3 sheets (LinkedIn, Indeed, Naukri)
        import importlib.util
        import os
        from pathlib import Path

        # Try to import from dashboard/data/sheets_fetcher.py (unified version)
        try:
            # Add dashboard directory to path
            dashboard_data_path = Path(__file__).parent.parent / 'dashboard' / 'data'
            if dashboard_data_path.exists():
                sys.path.insert(0, str(dashboard_data_path))
            
            from sheets_fetcher import get_data_fetcher
            print("✅ Using unified data fetcher (fetches from LinkedIn_Jobs, Indeed_Jobs, Naukri_Jobs)")
        except ImportError as e:
            print(f"⚠️ Could not import unified fetcher: {e}")
            # Fallback: try direct import from current directory
            try:
                from sheets_fetcher import get_data_fetcher
                print("✅ Using unified data fetcher from current directory")
            except ImportError:
                # Last resort: load from file path
                print("⚠️ Trying to load sheets_fetcher.py from dashboard/data/")
                sheets_fetcher_path = Path(__file__).parent.parent / 'dashboard' / 'data' / 'sheets_fetcher.py'
                if sheets_fetcher_path.exists():
                    spec = importlib.util.spec_from_file_location("sheets_fetcher", sheets_fetcher_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    get_data_fetcher = module.get_data_fetcher
                    print("✅ Loaded unified data fetcher from file path")
                else:
                    raise ImportError(f"sheets_fetcher.py not found at {sheets_fetcher_path}")

        sheet_id = os.getenv('GOOGLE_SHEET_ID')

        # Try multiple env var names for credentials
        creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON') or os.getenv('GOOGLE_CREDENTIALS')
        creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        worksheet = os.getenv('WORKSHEET_NAME', 'LinkedIn_Jobs')  # Deprecated parameter

        if not sheet_id:
            _fetcher_error = "GOOGLE_SHEET_ID not set"
            print("❌ Error: GOOGLE_SHEET_ID not set")
            return None

        # Pass creds_json to data_fetcher via environment
        if creds_json:
            os.environ['GOOGLE_CREDENTIALS_JSON'] = creds_json
            print("✅ Using credentials from env var")
        elif os.path.exists(creds_file):
            print(f"✅ Using credentials from file: {creds_file}")
        else:
            print(f"⚠️ Warning: No credentials found (tried {creds_file})")

        # Initialize the unified fetcher (worksheet_name parameter is deprecated - it fetches from all sheets)
        _fetcher = get_data_fetcher(sheet_id, creds_file, worksheet)
        print("✅ Unified fetcher initialized - will fetch from LinkedIn_Jobs, Indeed_Jobs, Naukri_Jobs")
        return _fetcher

    except Exception as e:
        _fetcher_error = str(e)
        print(f"❌ Fetcher error: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# Frontend Routes
# ============================================================================

@app.route('/')
def index():
    """Home page - Dashboard."""
    return render_template('index.html')

@app.route('/job/<job_id>')
def job_detail(job_id):
    """Job detail page - client-side renders."""
    # Just render the template - JavaScript will fetch job data via API
    return render_template('job_detail.html')

@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@app.route('/test')
def test():
    """Test page."""
    return render_template('test_job_detail.html')

# ============================================================================
# API Endpoints
# ============================================================================

def sanitize_job_data(job_data: dict) -> dict:
    """
    Sanitize job data to ensure it's JSON-serializable.
    Removes NaN, Infinity, and other problematic values.
    """
    import math
    
    sanitized = {}
    for key, value in job_data.items():
        if isinstance(value, float):
            # Replace NaN and Infinity with empty string or 0
            if math.isnan(value) or math.isinf(value):
                sanitized[key] = '' if key == 'company_logo' else 0
            else:
                sanitized[key] = value
        elif isinstance(value, str):
            # Clean up string values
            sanitized[key] = value.strip() if value else ''
        elif value is None:
            sanitized[key] = ''
        else:
            sanitized[key] = value
    
    return sanitized

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    fetcher = get_fetcher()
    if not fetcher:
        return jsonify({
            'status': 'unhealthy',
            'error': _fetcher_error or 'Failed to initialize data fetcher',
            'env_check': {
                'GOOGLE_SHEET_ID': 'set' if os.getenv('GOOGLE_SHEET_ID') else 'missing',
                'credentials': 'exists' if os.path.exists('credentials.json') else 'missing'
            }
        }), 500
    
    try:
        stats = fetcher.get_stats()
        return jsonify({
            'status': 'healthy',
            'jobs_count': stats.get('total_jobs', 0),
            'last_updated': stats.get('last_updated'),
            'worksheet': stats.get('worksheet')
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get paginated list of jobs."""
    fetcher = get_fetcher()
    if not fetcher:
        return jsonify({
            'success': False, 
            'error': f'Failed to initialize: {_fetcher_error}'
        }), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        search = request.args.get('search', '')
        city = request.args.get('city', '')
        emp_type = request.args.get('type', '')
        
        jobs = fetcher.search_jobs(
            query=search if search else None,
            city=city if city else None,
            employment_type=emp_type if emp_type else None,
            limit=1000
        )
        
        # DEBUG: Print first job from search_jobs
        if jobs and len(jobs) > 0:
            print(f"\n=== DEBUG: First job from search_jobs ===")
            print(f"Keys: {list(jobs[0].keys())}")
            print(f"Company Logo value: {jobs[0].get('Company Logo', 'MISSING')}")
            print(f"company_logo value: {jobs[0].get('company_logo', 'MISSING')}\n")

        total = len(jobs)
        total_pages = (total + limit - 1) // limit
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1
        
        start = (page - 1) * limit
        end = start + limit
        page_jobs = jobs[start:end]
        
        simplified_jobs = []
        for job in page_jobs:
            simplified_job = {
                'id': job.get('id', ''),
                'job_title': job.get('Job Title', ''),
                'company': job.get('Company', ''),
                'employment_type': job.get('Employment Type', ''),
                'location': job.get('Location', ''),
                'posted_date': job.get('Posted', ''),
                'search_city': job.get('Search City', ''),
                'date_added': job.get('Date Added', ''),
                'company_logo': job.get('Company Logo', '') or job.get('company_logo', '') or job.get('Company_Logo', '') or ''
            }
            # Sanitize to remove NaN and ensure JSON-serializable data
            simplified_job = sanitize_job_data(simplified_job)
            simplified_jobs.append(simplified_job)
        
        # DEBUG: Log first simplified job
        if simplified_jobs:
            print(f"\n=== API DEBUG ===")
            print(f"Simplified job keys: {list(simplified_jobs[0].keys())}")
            print(f"Logo field present: {'company_logo' in simplified_jobs[0]}")
            print(f"Logo value: '{simplified_jobs[0].get('company_logo', 'NOT SET')}'")
            print(f"Original job keys: {list(page_jobs[0].keys())}")
            print(f"Original Company Logo: '{page_jobs[0].get('Company Logo', 'MISSING')}'\n")

        return jsonify({
            'success': True,
            'jobs': simplified_jobs,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
    except Exception as e:
        print(f"Error in get_jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get single job details."""
    fetcher = get_fetcher()
    if not fetcher:
        return jsonify({'success': False, 'error': f'Failed to initialize: {_fetcher_error}'}), 500

    try:
        job = fetcher.get_job_by_id(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        # Sanitize job data to remove NaN and ensure JSON-serializable data
        sanitized_job = sanitize_job_data(job)
        return jsonify({'success': True, 'job': sanitized_job})
    except Exception as e:
        print(f"Error in get_job: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def extract_title_keywords(title):
    """Extract important keywords from job title."""
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'for', 'in', 'at', 'on', 'with',
        'senior', 'junior', 'lead', 'principal', 'manager', 'director',
        'executive', 'head', 'chief', 'vice', 'president', 'assistant',
        'associate', 'intern', 'internship', 'trainee', 'entry', 'level'
    }
    words = title.replace('-', ' ').replace('/', ' ').split()
    keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
    return keywords

@app.route('/api/jobs/<job_id>/similar', methods=['GET'])
def get_similar_jobs(job_id):
    """Get similar jobs based on multiple similarity factors."""
    fetcher = get_fetcher()
    if not fetcher:
        return jsonify({'success': False, 'error': f'Failed to initialize: {_fetcher_error}'}), 500

    try:
        current_job = fetcher.get_job_by_id(job_id)
        if not current_job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        all_jobs = fetcher.fetch_all_jobs()
        other_jobs = [j for j in all_jobs if j.get('id') != job_id]

        if not other_jobs:
            return jsonify({'success': True, 'similar_jobs': [], 'count': 0})

        similar_jobs = []

        for job in other_jobs:
            score = 0
            reasons = []

            # Factor 1: Same city (40 points)
            current_city = str(current_job.get('Search City', '') or '')
            job_city = str(job.get('Search City', '') or '')
            if current_city and job_city:
                if current_city.lower() == job_city.lower():
                    score += 40
                    reasons.append(current_city)
                elif current_city.lower() in job_city.lower() or job_city.lower() in current_city.lower():
                    score += 20
                    reasons.append("Nearby")

            # Factor 2: Same employment type (30 points)
            current_type = str(current_job.get('Employment Type', '') or '')
            job_type = str(job.get('Employment Type', '') or '')
            if current_type and job_type:
                if current_type.lower() == job_type.lower():
                    score += 30
                    reasons.append(current_type)
                elif any(word in job_type.lower() for word in current_type.lower().split()):
                    score += 15

            # Factor 3: Similar job title (30 points)
            current_title = str(current_job.get('Job Title', '') or '').lower()
            job_title = str(job.get('Job Title', '') or '').lower()
            current_keywords = set(extract_title_keywords(current_title))
            job_keywords = set(extract_title_keywords(job_title))

            if current_keywords and job_keywords:
                common = current_keywords & job_keywords
                if common:
                    keyword_score = min(30, len(common) * 10)
                    score += keyword_score
                    reasons.append(', '.join(list(common)[:2]))

            # Factor 4: Same company (20 points)
            current_company = str(current_job.get('Company', '') or '')
            job_company = str(job.get('Company', '') or '')
            if current_company and job_company:
                if current_company.lower() == job_company.lower():
                    score += 20
                    reasons.append("Same company")

            similar_jobs.append({
                'job': job,
                'score': score,
                'match_reasons': reasons if reasons else ['Other opportunities']
            })

        # Sort by score and take top 3
        similar_jobs.sort(key=lambda x: x['score'], reverse=True)
        top_similar = similar_jobs[:3]

        # Format response
        result = []
        for item in top_similar:
            job_data = item['job']
            similar_job = {
                'id': job_data.get('id', ''),
                'job_title': job_data.get('Job Title', ''),
                'company': job_data.get('Company', ''),
                'company_logo': job_data.get('Company Logo', '') or job_data.get('company_logo', ''),
                'location': job_data.get('Location', ''),
                'employment_type': job_data.get('Employment Type', ''),
                'posted_date': job_data.get('Posted', ''),
                'match_score': item['score'],
                'match_reasons': item['match_reasons']
            }
            # Sanitize to remove NaN
            result.append(sanitize_job_data(similar_job))

        return jsonify({
            'success': True,
            'similar_jobs': result,
            'count': len(result)
        })

    except Exception as e:
        print(f"Error in get_similar_jobs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics."""
    fetcher = get_fetcher()
    if not fetcher:
        return jsonify({'success': False, 'error': f'Failed to initialize: {_fetcher_error}'}), 500
    
    try:
        stats = fetcher.get_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        print(f"Error in get_stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Get list of all cities."""
    fetcher = get_fetcher()
    if not fetcher:
        return jsonify({'success': False, 'error': f'Failed to initialize: {_fetcher_error}'}), 500
    
    try:
        cities = fetcher.get_unique_cities()
        return jsonify({'success': True, 'cities': sorted(cities)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employment-types', methods=['GET'])
def get_employment_types():
    """Get list of employment types."""
    fetcher = get_fetcher()
    if not fetcher:
        return jsonify({'success': False, 'error': f'Failed to initialize: {_fetcher_error}'}), 500
    
    try:
        types = fetcher.get_unique_employment_types()
        return jsonify({'success': True, 'types': sorted(types)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Manually refresh data from Google Sheets."""
    fetcher = get_fetcher()
    if not fetcher:
        return jsonify({'success': False, 'error': f'Failed to initialize: {_fetcher_error}'}), 500
    
    try:
        fetcher.clear_cache()
        jobs = fetcher.fetch_all_jobs(use_cache=False)
        return jsonify({'success': True, 'count': len(jobs), 'message': f'Refreshed {len(jobs)} jobs'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-import', methods=['GET'])
def test_import():
    """Test if data_fetcher can be imported."""
    try:
        from data_fetcher import get_data_fetcher
        return jsonify({
            'success': True,
            'message': 'data_fetcher imported successfully!',
            'module_path': get_data_fetcher.__module__
        })
    except ImportError as e:
        return jsonify({
            'success': False,
            'error': f'ImportError: {str(e)}',
            'python_path': sys.path
        }), 500

# Vercel handler
def handler(request):
    """Vercel serverless function handler."""
    return app(request.environ, lambda *args: None)

