"""
🎯 Non-Tech Roles Dashboard - Marketing, Accounts, UI/UX, Entrepreneurial Roles
Reads job listings directly from Notion database and displays them
with the SayBriefly design system.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Cache for jobs (to avoid hitting Notion API on every request)
_jobs_cache = []
_jobs_cache_timestamp = None
CACHE_DURATION = 120  # seconds

# ============================================================================
# ROLES CONFIGURATION
# ============================================================================

# Role domain keywords for filtering
ROLE_DOMAINS = {
    "All": [],
    "Marketing": ["marketing", "brand", "growth", "social media", "content", "campaign",
                   "demand generation", "pr manager", "communications", "seo"],
    "Accounts": ["account manager", "account executive", "key account", "client partner",
                  "client services", "account director", "customer success", "business development"],
    "UI/UX": ["ui designer", "ux designer", "ui/ux", "product designer", "ux researcher",
               "interaction designer", "visual designer", "ux lead", "ux architect", "user experience"],
    "Founders Office": ["founder's office", "founders office", "chief of staff",
                         "entrepreneur in residence", "eir"],
}


def categorize_role(role_title: str) -> str:
    """Determine which domain a role belongs to based on keywords."""
    if not role_title:
        return "Other"
    title_lower = role_title.lower()

    # Check Founder's Office first (high priority)
    founders_keywords = ["founder's office", "founders office", "chief of staff",
                         "entrepreneur in residence", "entrepreneur-in-residence", "eir"]
    for kw in founders_keywords:
        if kw in title_lower:
            return "Founders Office"

    # Check Marketing
    marketing_keywords = ["marketing", "brand", "growth", "social media", "content marketing",
                          "campaign", "demand generation", "pr", "communications", "seo",
                          "digital marketing", "product marketing", "performance marketing"]
    for kw in marketing_keywords:
        if kw in title_lower:
            return "Marketing"

    # Check UI/UX
    ux_keywords = ["ui designer", "ux designer", "ui/ux", "ui ux", "product designer",
                   "ux researcher", "interaction designer", "visual designer", "ux lead",
                   "ux architect", "user experience", "user interface"]
    for kw in ux_keywords:
        if kw in title_lower:
            return "UI/UX"

    # Check Accounts
    accounts_keywords = ["account manager", "account executive", "key account",
                         "client partner", "client services", "account director",
                         "customer success", "client relationship", "account lead",
                         "business development manager", "strategic account"]
    for kw in accounts_keywords:
        if kw in title_lower:
            return "Accounts"

    return "Other"


# ============================================================================
# NOTION API READER
# ============================================================================

def fetch_jobs_from_notion() -> list:
    """Fetch all jobs from the Notion database."""
    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("⚠️  Notion API key or database ID not configured")
        return []

    try:
        from notion_client import Client
        from notion_client.errors import APIResponseError

        client = Client(auth=NOTION_API_KEY)

        all_jobs = []
        has_more = True
        start_cursor = None

        while has_more:
            query_params = {"database_id": NOTION_DATABASE_ID}
            if start_cursor:
                query_params["start_cursor"] = start_cursor
            query_params["page_size"] = 100

            response = client.databases.query(**query_params)
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

            for page in response.get("results", []):
                props = page.get("properties", {})

                # Extract Company (Title)
                company = ""
                company_prop = props.get("Company", {})
                if company_prop.get("type") == "title":
                    title_list = company_prop.get("title", [])
                    if title_list:
                        company = title_list[0].get("plain_text", "")

                # Extract Position (Rich text)
                role = ""
                position_prop = props.get("Position", {})
                if position_prop.get("type") == "rich_text":
                    rt_list = position_prop.get("rich_text", [])
                    if rt_list:
                        role = rt_list[0].get("plain_text", "")

                # Extract Location (Rich text)
                location = ""
                location_prop = props.get("Location", {})
                if location_prop.get("type") == "rich_text":
                    loc_list = location_prop.get("rich_text", [])
                    if loc_list:
                        location = loc_list[0].get("plain_text", "")

                # Extract Application Link (URL)
                job_url = ""
                url_prop = props.get("Application Link", {})
                if url_prop.get("type") == "url":
                    job_url = url_prop.get("url", "")

                # Extract Date Posted
                date_str = ""
                date_prop = props.get("Date Posted", {})
                if date_prop.get("type") == "date":
                    date_data = date_prop.get("date", {})
                    if date_data:
                        date_str = date_data.get("start", "")

                # Extract role domain
                domain = categorize_role(role)

                all_jobs.append({
                    "id": page.get("id", ""),
                    "company": company or "Unknown",
                    "role": role or "Unknown",
                    "location": location or "India",
                    "url": job_url or "",
                    "date_added": date_str or datetime.now().strftime("%Y-%m-%d"),
                    "domain": domain,
                    "created_time": page.get("created_time", ""),
                    "last_edited_time": page.get("last_edited_time", ""),
                })

        return all_jobs

    except ImportError:
        print("❌ notion_client not installed. Run: pip install notion-client")
        return []
    except APIResponseError as e:
        print(f"❌ Notion API error: {e}")
        return []
    except Exception as e:
        print(f"❌ Error fetching from Notion: {e}")
        return []


def get_jobs(force_refresh: bool = False) -> list:
    """Get jobs with caching."""
    global _jobs_cache, _jobs_cache_timestamp

    now = datetime.now()

    if (not force_refresh
        and _jobs_cache_timestamp
        and (now - _jobs_cache_timestamp).seconds < CACHE_DURATION
        and _jobs_cache):
        return _jobs_cache

    jobs = fetch_jobs_from_notion()

    # Sort by date_added (most recent first)
    jobs.sort(key=lambda j: j.get("date_added", ""), reverse=True)

    _jobs_cache = jobs
    _jobs_cache_timestamp = now

    return jobs


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/jobs', methods=['GET'])
def api_jobs():
    """Get jobs with optional filtering and pagination."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        domain = request.args.get('domain', '').strip()
        search = request.args.get('search', '').strip()
        force_refresh = request.args.get('refresh', '').lower() == 'true'

        jobs = get_jobs(force_refresh=force_refresh)

        # Apply domain filter
        if domain and domain != "All":
            domain_lower = domain.lower()
            jobs = [j for j in jobs if j.get("domain", "").lower() == domain_lower]

        # Apply search filter
        if search:
            search_lower = search.lower()
            jobs = [
                j for j in jobs
                if search_lower in j.get("role", "").lower()
                or search_lower in j.get("company", "").lower()
                or search_lower in j.get("location", "").lower()
            ]

        # Calculate pagination
        total = len(jobs)
        total_pages = max(1, (total + limit - 1) // limit) if total else 1
        start = (page - 1) * limit
        end = start + limit
        paginated_jobs = jobs[start:end] if start < total else []

        return jsonify({
            "success": True,
            "jobs": paginated_jobs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get dashboard statistics."""
    try:
        jobs = get_jobs()

        total = len(jobs)
        domains = {}
        for job in jobs:
            d = job.get("domain", "Other")
            domains[d] = domains.get(d, 0) + 1

        companies = {}
        for job in jobs:
            c = job.get("company", "Unknown")
            companies[c] = companies.get(c, 0) + 1

        return jsonify({
            "success": True,
            "stats": {
                "total_jobs": total,
                "domains": dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)),
                "companies": dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:20]),
                "total_companies": len(companies),
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/domains', methods=['GET'])
def api_domains():
    """Get list of available role domains."""
    return jsonify({
        "success": True,
        "domains": ["All", "Marketing", "Accounts", "UI/UX", "Founders Office"]
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "source": "notion"})


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Force refresh the jobs cache from Notion."""
    try:
        jobs = get_jobs(force_refresh=True)
        return jsonify({
            "success": True,
            "message": f"Refreshed {len(jobs)} jobs from Notion",
            "count": len(jobs)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
