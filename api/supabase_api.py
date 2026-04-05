"""
High Performance Supabase-backed API for Job Dashboard
Replaces Google Sheets direct fetching for 100% reliability.
"""
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Initialize app
app = Flask(__name__)
CORS(app)

# Load env vars
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") # Use anon key for frontend read-only API

# Singleton client
_supabase = None

def get_supabase() -> Client:
    """Get Supabase client."""
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase

def sanitize_job(job: dict) -> dict:
    """Ensure job data matches expected frontend schema."""
    return {
        'id': job.get('id') or job.get('external_id', ''),
        'job_title': job.get('job_title', ''),
        'company': job.get('company', ''),
        'employment_type': job.get('employment_type', ''),
        'location': job.get('location', ''),
        'posted_date': job.get('posted_date', ''),
        'search_city': job.get('search_city', ''),
        'date_added': job.get('date_added', ''),
        'company_logo': job.get('company_logo', ''),
        'job_url': job.get('job_url', ''),
        'job_description': job.get('job_description', ''),
        'source': job.get('source', 'unknown')
    }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        supabase = get_supabase()
        # Test connection
        supabase.table("jobs").select("id", count="exact").limit(1).execute()
        return jsonify({'status': 'healthy', 'source': 'supabase'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get paginated and filtered jobs from Supabase."""
    try:
        supabase = get_supabase()
        
        # Params
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        search = request.args.get('search', '')
        city = request.args.get('city', '')
        emp_type = request.args.get('type', '')
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Build query
        query = supabase.table("jobs").select("*", count="exact")
        
        # Filters
        if city:
            query = query.eq("search_city", city)
        if emp_type:
            # Simple substring match for employment type
            query = query.ilike("employment_type", f"%{emp_type}%")
        
        # Search (using Supabase full-text search if query provided)
        if search:
            query = query.text_search('fts_tokens', search)
        
        # Order and Pagination
        query = query.order("date_added", desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        jobs = [sanitize_job(j) for j in result.data]
        total = result.count
        total_pages = (total + limit - 1) // limit if total else 0

        return jsonify({
            'success': True,
            'jobs': jobs,
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
    """Get single job from Supabase."""
    try:
        supabase = get_supabase()
        # Try finding by UUID or external_id
        result = supabase.table("jobs").select("*").or_(f"id.eq.{job_id},external_id.eq.{job_id}").execute()
        
        if not result.data:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
            
        return jsonify({'success': True, 'job': sanitize_job(result.data[0])})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics from Supabase."""
    try:
        supabase = get_supabase()
        
        # Total count
        total_res = supabase.table("jobs").select("id", count="exact").limit(1).execute()
        total = total_res.count
        
        # Top Cities (using a simple RPC or multiple queries for now)
        # For production, you might want to create a Postgres View or RPC
        # Here we just return basics
        
        return jsonify({
            'success': True,
            'stats': {
                'total_jobs': total,
                'source': 'supabase'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Vercel handler
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
