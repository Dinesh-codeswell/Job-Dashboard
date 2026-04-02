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
os.environ.setdefault('WORKSHEET_NAME', 'Consulting_Jobs_India')

# Lazy load data fetcher
_fetcher = None
_fetcher_error = None

def get_fetcher():
    """Get or create data fetcher instance."""
    global _fetcher, _fetcher_error
    
    if _fetcher is not None:
        return _fetcher
    
    if _fetcher_error is not None:
        return None
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import data_fetcher - try multiple methods for Vercel compatibility
        import importlib.util
        import os
        from pathlib import Path
        
        # Try direct import first
        try:
            from data_fetcher import get_data_fetcher
        except ImportError:
            # Fallback: load from file path (for Vercel)
            spec = importlib.util.spec_from_file_location("data_fetcher", Path(__file__).parent / "data_fetcher.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            get_data_fetcher = module.get_data_fetcher
        
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        # Try multiple env var names for credentials
        creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON') or os.getenv('GOOGLE_CREDENTIALS')
        creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        worksheet = os.getenv('WORKSHEET_NAME', 'Consulting_Jobs_India')
        
        if not sheet_id:
            _fetcher_error = "GOOGLE_SHEET_ID not set"
            print("Error: GOOGLE_SHEET_ID not set")
            return None
        
        # Pass creds_json to data_fetcher via environment
        if creds_json:
            os.environ['GOOGLE_CREDENTIALS_JSON'] = creds_json
            print("Using credentials from env var")
        elif os.path.exists(creds_file):
            print(f"Using credentials from file: {creds_file}")
        else:
            print(f"Warning: No credentials found (tried {creds_file})")
        
        _fetcher = get_data_fetcher(sheet_id, creds_file, worksheet)
        return _fetcher
        
    except Exception as e:
        _fetcher_error = str(e)
        print(f"Fetcher error: {e}")
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
                # Always include company_logo field, even if empty
                'company_logo': job.get('Company Logo', '') or job.get('company_logo', '') or job.get('Company_Logo', '') or ''
            }
            
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
        return jsonify({'success': True, 'job': job})
    except Exception as e:
        print(f"Error in get_job: {e}")
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

