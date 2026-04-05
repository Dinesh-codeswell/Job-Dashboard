"""
Unified API with Robust Fallback Mechanism
Primary: Supabase (High Performance, Reliable)
Secondary: Google Sheets (Fallback during transition or DB maintenance)
"""
import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Existing fetcher for fallback
from dashboard.data.sheets_fetcher import get_data_fetcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
load_dotenv()

# Config
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

def get_supabase():
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None
    return None

def sanitize_supabase_job(job):
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

def sanitize_sheets_job(job):
    return {
        'id': job.get('id', ''),
        'job_title': job.get('Job Title', ''),
        'company': job.get('Company', ''),
        'employment_type': job.get('Employment Type', ''),
        'location': job.get('Location', ''),
        'posted_date': job.get('Posted', ''),
        'search_city': job.get('Search City', ''),
        'date_added': job.get('Date Added', ''),
        'company_logo': job.get('Company Logo', '') or job.get('company_logo', '') or '',
        'job_url': job.get('Job URL', ''),
        'job_description': job.get('Job Description', ''),
        'source': job.get('source', 'unknown')
    }

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    search = request.args.get('search', '')
    city = request.args.get('city', '')
    emp_type = request.args.get('type', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 30))

    # 1. Try Supabase first
    supabase = get_supabase()
    if supabase:
        try:
            offset = (page - 1) * limit
            query = supabase.table("jobs").select("*", count="exact")
            if city: query = query.eq("search_city", city)
            if emp_type: query = query.ilike("employment_type", f"%{emp_type}%")
            if search: query = query.text_search('fts_tokens', search)
            
            result = query.order("date_added", desc=True).range(offset, offset + limit - 1).execute()
            
            if result.data:
                logger.info("Fetched jobs from Supabase")
                return jsonify({
                    'success': True,
                    'source': 'supabase',
                    'jobs': [sanitize_supabase_job(j) for j in result.data],
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': result.count,
                        'total_pages': (result.count + limit - 1) // limit
                    }
                })
        except Exception as e:
            logger.error(f"Supabase fetch failed, falling back to Sheets: {e}")

    # 2. Fallback to Google Sheets
    try:
        fetcher = get_data_fetcher(GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE)
        jobs = fetcher.search_jobs(
            query=search if search else None,
            city=city if city else None,
            employment_type=emp_type if emp_type else None,
            limit=1000
        )
        
        total = len(jobs)
        start = (page - 1) * limit
        end = start + limit
        page_jobs = jobs[start:end]
        
        logger.info("Fetched jobs from Google Sheets (Fallback)")
        return jsonify({
            'success': True,
            'source': 'sheets',
            'jobs': [sanitize_sheets_job(j) for j in page_jobs],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': (total + limit - 1) // limit
            }
        })
    except Exception as e:
        logger.error(f"Fallback fetch failed: {e}")
        return jsonify({'success': False, 'error': 'All data sources failed'}), 500

# Other endpoints similar to Supabase with fallback...
# [Simplified for space, would include health, job_id, etc.]

def handler(request):
    return app(request.environ, lambda *args: None)
