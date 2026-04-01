"""
Consulting Jobs Dashboard - Flask Application

A real-time dashboard for displaying consulting jobs from Google Sheets.
"""
import os
import sys
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from data.sheets_fetcher import get_data_fetcher

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize data fetcher
fetcher = get_data_fetcher(
    sheet_id=Config.GOOGLE_SHEET_ID,
    credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
    worksheet_name=Config.WORKSHEET_NAME
)


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page - Dashboard."""
    return render_template('index.html')


@app.route('/job/<job_id>')
def job_detail(job_id):
    """Job detail page."""
    try:
        # Fetch job data
        job = fetcher.get_job_by_id(job_id)
        
        if not job:
            # If job not found, redirect to home
            return redirect(url_for('index'))
        
        return render_template('job_detail.html', job=job)
    except Exception as e:
        # If error, redirect to home with error message
        print(f"Error loading job {job_id}: {e}")
        return redirect(url_for('index'))


@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@app.route('/test')
def test():
    """Test page for debugging."""
    return render_template('test_job_detail.html')


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """
    Get paginated list of jobs.
    
    Query Params:
        page: Page number (default: 1)
        limit: Jobs per page (default: 30)
        search: Search query
        city: Filter by city
        type: Filter by employment type
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', Config.JOBS_PER_PAGE))
        search = request.args.get('search', '')
        city = request.args.get('city', '')
        emp_type = request.args.get('type', '')
        
        # Search and filter
        jobs = fetcher.search_jobs(
            query=search if search else None,
            city=city if city else None,
            employment_type=emp_type if emp_type else None,
            limit=1000  # Get more for pagination
        )
        
        # Pagination
        total = len(jobs)
        total_pages = (total + limit - 1) // limit
        
        # Ensure page is within bounds
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1
        
        # Get page slice
        start = (page - 1) * limit
        end = start + limit
        page_jobs = jobs[start:end]
        
        # Simplify job data for list view
        simplified_jobs = []
        for job in page_jobs:
            simplified_jobs.append({
                'id': job.get('id', ''),
                'job_title': job.get('Job Title', ''),
                'company': job.get('Company', ''),
                'employment_type': job.get('Employment Type', ''),
                'location': job.get('Location', ''),
                'posted_date': job.get('Posted', ''),
                'search_city': job.get('Search City', ''),
                'date_added': job.get('Date Added', '')
            })
        
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
            },
            'filters': {
                'search': search,
                'city': city,
                'type': emp_type
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """
    Get single job details.
    
    Args:
        job_id: Job ID
    """
    try:
        job = fetcher.get_job_by_id(job_id)
        
        if not job:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        return jsonify({
            'success': True,
            'job': job
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics."""
    try:
        stats = fetcher.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Manually refresh data from Google Sheets."""
    try:
        fetcher.clear_cache()
        jobs = fetcher.fetch_all_jobs(use_cache=False)
        
        return jsonify({
            'success': True,
            'count': len(jobs),
            'message': f'Refreshed {len(jobs)} jobs'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Get list of all cities."""
    try:
        cities = fetcher.get_unique_cities()
        return jsonify({
            'success': True,
            'cities': sorted(cities)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/employment-types', methods=['GET'])
def get_employment_types():
    """Get list of all employment types."""
    try:
        types = fetcher.get_unique_employment_types()
        return jsonify({
            'success': True,
            'types': sorted(types)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        stats = fetcher.get_stats()
        return jsonify({
            'status': 'healthy',
            'jobs_count': stats.get('total_jobs', 0),
            'last_updated': stats.get('last_updated'),
            'worksheet': stats.get('worksheet')
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found'
        }), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    return render_template('500.html'), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Consulting Jobs Dashboard")
    print("="*60)
    print(f"📊 Worksheet: {Config.WORKSHEET_NAME}")
    print(f"📍 Jobs per page: {Config.JOBS_PER_PAGE}")
    print(f"🔄 Auto-refresh: Every {Config.AUTO_REFRESH_INTERVAL}s")
    print("="*60)
    print(f"\n🌐 Starting server at http://{Config.HOST}:{Config.PORT}\n")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
