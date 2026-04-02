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
            simplified_job = {
                'id': job.get('id', ''),
                'job_title': job.get('Job Title', ''),
                'company': job.get('Company', ''),
                'employment_type': job.get('Employment Type', ''),
                'location': job.get('Location', ''),
                'posted_date': job.get('Posted', ''),
                'search_city': job.get('Search City', ''),
                'date_added': job.get('Date Added', ''),
                # Include company logo
                'company_logo': job.get('Company Logo', '') or job.get('company_logo', '') or ''
            }
            simplified_jobs.append(simplified_job)

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
# SIMILAR JOBS ENDPOINT
# ============================================================================

@app.route('/api/jobs/<job_id>/similar', methods=['GET'])
def get_similar_jobs(job_id):
    """
    Get similar jobs based on multiple similarity factors.
    
    Similarity Algorithm (100 points total):
    1. Same city (40 points) - Location matters most
    2. Same employment type (30 points) - Job arrangement
    3. Similar job title keywords (30 points) - Role similarity
    4. Same company (20 points) - Other positions at same company
    
    Returns top 3 most similar jobs.
    """
    try:
        # Use the global fetcher object
        current_job = fetcher.get_job_by_id(job_id)
        if not current_job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        # Get all other jobs
        all_jobs = fetcher.fetch_all_jobs()
        other_jobs = [j for j in all_jobs if j.get('id') != job_id]
        
        if not other_jobs:
            return jsonify({'success': True, 'similar_jobs': [], 'count': 0})
        
        # Calculate similarity scores
        similar_jobs = []
        
        for job in other_jobs:
            score = 0
            reasons = []
            
            # Factor 1: Same city (40 points)
            current_city = current_job.get('Search City', '')
            job_city = job.get('Search City', '')
            if current_city and job_city:
                if current_city.lower() == job_city.lower():
                    score += 40
                    reasons.append(f"Same location: {current_city}")
                elif current_city.lower() in job_city.lower() or job_city.lower() in current_city.lower():
                    score += 20
                    reasons.append(f"Nearby location")
            
            # Factor 2: Same employment type (30 points)
            current_type = current_job.get('Employment Type', '')
            job_type = job.get('Employment Type', '')
            if current_type and job_type:
                if current_type.lower() == job_type.lower():
                    score += 30
                    reasons.append(f"Same type: {current_type}")
                elif any(word in job_type.lower() for word in current_type.lower().split()):
                    score += 15
            
            # Factor 3: Similar job title (30 points)
            current_title = current_job.get('Job Title', '').lower()
            job_title = job.get('Job Title', '').lower()
            
            # Extract keywords from titles
            current_keywords = set(extract_title_keywords(current_title))
            job_keywords = set(extract_title_keywords(job_title))
            
            if current_keywords and job_keywords:
                common = current_keywords & job_keywords
                if common:
                    keyword_score = min(30, len(common) * 10)
                    score += keyword_score
                    reasons.append(f"Similar role: {', '.join(list(common)[:2])}")
            
            # Factor 4: Same company (20 points)
            current_company = current_job.get('Company', '')
            job_company = job.get('Company', '')
            if current_company and job_company:
                if current_company.lower() == job_company.lower():
                    score += 20
                    reasons.append(f"Same company")
            
            # Add job with score (even if score is 0)
            similar_jobs.append({
                'job': job,
                'score': score,
                'match_reasons': reasons if reasons else ['Other opportunities']
            })
        
        # Sort by score (highest first) and take top 3
        similar_jobs.sort(key=lambda x: x['score'], reverse=True)
        top_similar = similar_jobs[:3]
        
        # Format response
        result = []
        for item in top_similar:
            job_data = item['job']
            result.append({
                'id': job_data.get('id', ''),
                'job_title': job_data.get('Job Title', ''),
                'company': job_data.get('Company', ''),
                'company_logo': job_data.get('Company Logo', '') or job_data.get('company_logo', ''),
                'location': job_data.get('Location', ''),
                'employment_type': job_data.get('Employment Type', ''),
                'posted_date': job_data.get('Posted', ''),
                'match_score': item['score'],
                'match_reasons': item['match_reasons']
            })
        
        return jsonify({
            'success': True,
            'similar_jobs': result,
            'count': len(result)
        })
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR in get_similar_jobs: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500


def extract_title_keywords(title):
    """
    Extract important keywords from job title.
    Removes common words and keeps technical/specific terms.
    """
    # Words to ignore
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'for', 'in', 'at', 'on', 'with',
        'senior', 'junior', 'lead', 'principal', 'manager', 'director',
        'executive', 'head', 'chief', 'vice', 'president', 'assistant',
        'associate', 'intern', 'internship', 'trainee', 'entry', 'level'
    }
    
    # Split and clean
    words = title.replace('-', ' ').replace('/', ' ').split()
    keywords = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 2]
    
    return keywords


def get_match_reasons(score, current_city, job_city, current_type, job_type, current_keywords, job_keywords, current_company, job_company):
    """Generate human-readable match reasons."""
    reasons = []
    
    if current_city and job_city and current_city == job_city:
        reasons.append(f"Same location: {current_city}")
    
    if current_type and job_type and current_type.lower() == job_type.lower():
        reasons.append(f"Same type: {current_type}")
    
    if current_keywords and job_keywords:
        common = current_keywords & job_keywords
        if common:
            reasons.append(f"Similar role: {', '.join(list(common)[:2])}")
    
    if current_company and job_company and current_company.lower() == job_company.lower():
        reasons.append(f"Same company: {current_company}")
    
    return reasons


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
