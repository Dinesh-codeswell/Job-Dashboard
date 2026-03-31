# Vercel Serverless API for Consulting Jobs Dashboard

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import data fetcher
from api.data_fetcher import get_data_fetcher

# Create Flask app
app = Flask(__name__, 
            template_folder='../dashboard/templates',
            static_folder='../dashboard/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'vercel-secret-key')
CORS(app)

# Initialize data fetcher
fetcher = None

def get_fetcher():
    """Get or create data fetcher instance."""
    global fetcher
    if fetcher is None:
        fetcher = get_data_fetcher(
            sheet_id=os.getenv('GOOGLE_SHEET_ID'),
            credentials_file=os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
            worksheet_name=os.getenv('WORKSHEET_NAME', 'Consulting_Jobs_India')
        )
    return fetcher

# ============================================================================
# Frontend Routes
# ============================================================================

@app.route('/')
def index():
    """Home page - Dashboard."""
    return render_template('index.html')

@app.route('/job/<job_id>')
def job_detail(job_id):
    """Job detail page."""
    return render_template('job_detail.html', job_id=job_id)

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

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get paginated list of jobs."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        search = request.args.get('search', '')
        city = request.args.get('city', '')
        emp_type = request.args.get('type', '')
        
        jobs = get_fetcher().search_jobs(
            query=search if search else None,
            city=city if city else None,
            employment_type=emp_type if emp_type else None,
            limit=1000
        )
        
        total = len(jobs)
        total_pages = (total + limit - 1) // limit
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1
        
        start = (page - 1) * limit
        end = start + limit
        page_jobs = jobs[start:end]
        
        simplified_jobs = [{
            'id': job.get('id', ''),
            'job_title': job.get('Job Title', ''),
            'company': job.get('Company', ''),
            'employment_type': job.get('Employment Type', ''),
            'location': job.get('Location', ''),
            'posted_date': job.get('Posted', ''),
            'search_city': job.get('Search City', ''),
            'date_added': job.get('Date Added', '')
        } for job in page_jobs]
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get single job details."""
    try:
        job = get_fetcher().get_job_by_id(job_id)
        
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        return jsonify({'success': True, 'job': job})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics."""
    try:
        stats = get_fetcher().get_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Manually refresh data from Google Sheets."""
    try:
        get_fetcher().clear_cache()
        jobs = get_fetcher().fetch_all_jobs(use_cache=False)
        
        return jsonify({
            'success': True,
            'count': len(jobs),
            'message': f'Refreshed {len(jobs)} jobs'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Get list of all cities."""
    try:
        cities = get_fetcher().get_unique_cities()
        return jsonify({'success': True, 'cities': sorted(cities)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/employment-types', methods=['GET'])
def get_employment_types():
    """Get list of employment types."""
    try:
        types = get_fetcher().get_unique_employment_types()
        return jsonify({'success': True, 'types': sorted(types)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        stats = get_fetcher().get_stats()
        return jsonify({
            'status': 'healthy',
            'jobs_count': stats.get('total_jobs', 0),
            'last_updated': stats.get('last_updated'),
            'worksheet': stats.get('worksheet')
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# ============================================================================
# Vercel Serverless Handler
# ============================================================================

def handler(request):
    """Vercel serverless function handler."""
    return app(request.environ, lambda *args: None)
