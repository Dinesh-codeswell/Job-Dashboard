#!/usr/bin/env python3
"""Test Notion connection."""
import os
from dotenv import load_dotenv
from linkedin_scraper.integrations.notion import NotionIntegration

load_dotenv()

api_key = os.getenv("NOTION_API_KEY")
database_id = os.getenv("NOTION_DATABASE_ID")

print("Testing Notion Connection...")
print(f"API Key: {'Set ✓' if api_key and (api_key.startswith('secret_') or api_key.startswith('ntn_')) else 'NOT SET or invalid ✗'}")
print(f"Database ID: {database_id}")
print()

if not api_key or not (api_key.startswith('secret_') or api_key.startswith('ntn_')):
    print("❌ ERROR: NOTION_API_KEY is not set or invalid!")
    print()
    print("To fix:")
    print("1. Go to https://www.notion.so/my-integrations")
    print("2. Create or copy your integration token")
    print("3. Edit .env file and set:")
    print("   NOTION_API_KEY=your_token_here")
    exit(1)

if not database_id:
    print("❌ ERROR: NOTION_DATABASE_ID is not set!")
    exit(1)

notion = NotionIntegration(api_key, database_id)

if notion.connect():
    print("✅ Connected to Notion successfully!")
    print()
    print("Database info:")
    props = notion.get_database_properties()
    for prop_name, prop_config in props.items():
        print(f"  - {prop_name}: {prop_config.get('type', 'unknown')}")
else:
    print("❌ Failed to connect to Notion!")
    print()
    print("Check:")
    print("1. Integration token is correct")
    print("2. Integration is connected to your database")
    print("   (Open database → ⋯ → Add connections → Select your integration)")
    exit(1)
