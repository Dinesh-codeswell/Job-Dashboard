#!/usr/bin/env python3
"""
SAFELY clears ALL jobs from the NON-TECH roles database ONLY.
Uses direct HTTP requests (bypasses library version issues).
"""
import sys, os, json, time
from pathlib import Path

from dotenv import load_dotenv

# --- FORCE LOAD ONLY from marketing-dashboard/.env ---
for key in ['NOTION_API_KEY', 'NOTION_DATABASE_ID']:
    os.environ.pop(key, None)

marketing_env = Path(__file__).parent / 'marketing-dashboard' / '.env'
if not marketing_env.exists():
    print(f"ERROR: {marketing_env} not found!")
    sys.exit(1)

load_dotenv(dotenv_path=marketing_env, override=True)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    print("ERROR: Missing NOTION_API_KEY or NOTION_DATABASE_ID in marketing-dashboard/.env")
    sys.exit(1)

# Format database ID with hyphens
DB_ID = NOTION_DATABASE_ID
if len(DB_ID) == 32:
    DB_ID = f"{DB_ID[:8]}-{DB_ID[8:12]}-{DB_ID[12:16]}-{DB_ID[16:20]}-{DB_ID[20:32]}"

print("=" * 60)
print("NON-TECH ROLES DATABASE CLEAR")
print("=" * 60)
print(f"Database ID: {DB_ID}")
print()

# Use direct HTTP requests to Notion API
import urllib.request
import urllib.error

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def notion_post(endpoint, body):
    """Make a POST request to Notion API."""
    url = f"https://api.notion.com/v1/{endpoint}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP {e.code}: {error_body}")

def notion_get(endpoint):
    """Make a GET request to Notion API."""
    url = f"https://api.notion.com/v1/{endpoint}"
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP {e.code}: {error_body}")

def notion_patch(endpoint, body):
    """Make a PATCH request to Notion API."""
    url = f"https://api.notion.com/v1/{endpoint}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="PATCH")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP {e.code}: {error_body}")

# 1. Get database info
print("--- Database Info ---")
try:
    db_info = notion_get(f"databases/{DB_ID}")
    title = db_info.get("title", [{}])
    db_title = title[0].get("plain_text", "Untitled") if title else "Untitled"
    props = db_info.get("properties", {})
    print(f"  Title: {db_title}")
    print(f"  Properties: {list(props.keys())}")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

# 2. Count pages and delete
print()
print("--- Counting & Deleting Jobs ---")

total = 0
deleted = 0
has_more = True
cursor = None
batch_num = 0
errors = []

while has_more:
    batch_num += 1
    try:
        query_body = {
            "page_size": 100
        }
        if cursor:
            query_body["start_cursor"] = cursor

        result = notion_post(f"databases/{DB_ID}/query", query_body)
        pages = result.get("results", [])
        has_more = result.get("has_more", False)
        cursor = result.get("next_cursor")
        
        total += len(pages)
        
        # Delete each page by archiving it
        for page in pages:
            page_id = page["id"]
            try:
                notion_patch(f"pages/{page_id}", {"archived": True})
                deleted += 1
                time.sleep(0.35)  # Respect Notion rate limits (~3 req/s)
                if deleted % 50 == 0:
                    print(f"  Deleted {deleted} jobs...")
            except Exception as e:
                errors.append(f"Page {page_id}: {e}")
        
        # Rate limiting
        time.sleep(0.25)
        
        # Progress update
        if total > 0 and total % 500 == 0:
            print(f"  Processed {total} jobs, deleted {deleted}...")
            
    except Exception as e:
        print(f"  Batch error: {e}")
        break

print()
print("=" * 60)
print("DONE")
print("=" * 60)
print(f"Total jobs found: {total}")
print(f"Successfully deleted: {deleted}")
if errors:
    print(f"Errors: {len(errors)}")
    for err in errors[:3]:
        print(f"  - {err}")
print()
if total == 0:
    print("Database was already empty.")
elif deleted == total:
    print("All jobs have been cleared successfully!")
else:
    print(f"Cleared {deleted} of {total} jobs.")
print()
print("Ready for fresh scraping with:")
print("  python scrape_non_tech_roles_notion.py")
