#!/usr/bin/env python3
"""Find your Notion database ID."""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

api_key = os.getenv("NOTION_API_KEY")
page_id = os.getenv("NOTION_DATABASE_ID")

print("Notion Database ID Finder")
print("=" * 60)
print(f"Page ID: {page_id}")
print()

client = Client(auth=api_key)

# Try to get the page
try:
    page = client.pages.retrieve(page_id)
    print("✓ Page found!")
    print(f"  Title: {page.get('title', [{}])[0].get('plain_text', 'Untitled') if page.get('title') else 'No title'}")
    print()
    
    # Check if it's a database
    if page.get('parent', {}).get('type') == 'database_id':
        print("✓ This page is inside a database!")
        db_id = page.get('parent', {}).get('database_id')
        print(f"  Database ID: {db_id}")
        print()
        print(f"Update your .env file:")
        print(f"  NOTION_DATABASE_ID={db_id}")
    else:
        print("✗ This is a regular page, not a database page.")
        print()
        print("To find your database ID:")
        print("1. Open the database in Notion")
        print("2. Click on any view (Table, Board, etc.)")
        print("3. Click 'Copy view link' or look at the URL")
        print("4. The URL should look like:")
        print("   https://www.notion.so/workspace/DATABASE_ID?v=VIEW_ID")
        print("5. Copy the DATABASE_ID part (before ?v=)")
        print()
        
        # Try to find child databases
        print("Searching for databases on this page...")
        try:
            children = client.blocks.children.list(page_id)
            for block in children.get('results', []):
                if block.get('type') == 'child_database':
                    print()
                    print("✓ Found a database on this page!")
                    print(f"  Database ID: {block.get('id')}")
                    print(f"  Title: {block.get('child_database', {}).get('title', 'Untitled')}")
                    print()
                    print(f"Update your .env file:")
                    print(f"  NOTION_DATABASE_ID={block.get('id')}")
                    break
            else:
                print("  No databases found as child blocks.")
        except Exception as e:
            print(f"  Error searching children: {e}")
            
except Exception as e:
    print(f"✗ Error retrieving page: {e}")
    print()
    print("Possible issues:")
    print("1. Integration is not connected to this page")
    print("2. Invalid page ID")
    print()
    print("To fix:")
    print("1. Open the page in Notion")
    print("2. Click ⋯ (three dots) → Add connections")
    print("3. Select your integration")
