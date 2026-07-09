#!/usr/bin/env python3
"""Check the database properties and sample data."""
import sys, os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / 'marketing-dashboard' / '.env', override=True)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    print("ERROR: Missing env vars")
    sys.exit(1)

from notion_client import Client
notion = Client(auth=NOTION_API_KEY)

DB_ID = NOTION_DATABASE_ID
# Add hyphens for API calls
if len(DB_ID) == 32:
    DB_ID = f"{DB_ID[:8]}-{DB_ID[8:12]}-{DB_ID[12:16]}-{DB_ID[16:20]}-{DB_ID[20:32]}"

print(f"Database ID: {DB_ID}")
print()

# 1. Get database info
print("--- Database Properties ---")
try:
    db_info = notion.databases.retrieve(DB_ID)
    props = db_info.get("properties", {})
    title = db_info.get("title", [{}])
    db_title = title[0].get("plain_text", "Untitled") if title else "Untitled"
    print(f"  Title: {db_title}")
    print(f"  Properties ({len(props)}):")
    for name, config in props.items():
        ptype = config.get("type", "?")
        print(f"    - {name} ({ptype})")
except Exception as e:
    print(f"  Error: {e}")

print()

# 2. Count total jobs
print("--- Counting Jobs ---")
try:
    total = 0
    has_more = True
    cursor = None
    
    while has_more:
        if cursor:
            result = notion.databases.query(DB_ID, start_cursor=cursor, page_size=100)
        else:
            result = notion.databases.query(DB_ID, page_size=100)
        
        total += len(result.get("results", []))
        has_more = result.get("has_more", False)
        cursor = result.get("next_cursor")
        
        if total % 1000 == 0 and total > 0:
            print(f"  Counted {total} jobs so far...")
    
    print(f"  Total jobs in database: {total}")
    
    # 3. Show a sample
    result = notion.databases.query(DB_ID, page_size=1)
    if result.get("results"):
        sample = result["results"][0]
        props = sample.get("properties", {})
        print()
        print("--- Sample Job ---")
        for key, val in props.items():
            ptype = val.get("type", "?")
            content = ""
            if ptype == "title":
                content = val.get("title", [{}])[0].get("plain_text", "") if val.get("title") else ""
            elif ptype == "rich_text":
                content = val.get("rich_text", [{}])[0].get("plain_text", "") if val.get("rich_text") else ""
            elif ptype == "url":
                content = val.get("url", "") or ""
            elif ptype == "date":
                content = str(val.get("date", {})) if val.get("date") else ""
            else:
                content = str(val)
            print(f"    {key}: {content[:80]}")
except Exception as e:
    print(f"  Error: {e}")
