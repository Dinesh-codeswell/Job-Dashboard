#!/usr/bin/env python3
"""Find the Notion database ID from a duplicated page URL."""
import sys, os
from pathlib import Path

# Load env credentials
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / 'marketing-dashboard' / '.env', override=True)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
if not NOTION_API_KEY:
    print("ERROR: NOTION_API_KEY not found in marketing-dashboard/.env")
    sys.exit(1)

from notion_client import Client
notion = Client(auth=NOTION_API_KEY)

# New duplicated page URL:
# https://app.notion.com/p/Non-Tech-Roles-398e82acc24f80c89bd8c1f96eecb3b1
PAGE_ID = "398e82ac-c24f-80c8-9bd8-c1f96eecb3b1"

print(f"Page ID: {PAGE_ID}")
print()

# 1. Check if this is itself a database
print("--- Trying as database ---")
try:
    db_info = notion.databases.retrieve(PAGE_ID)
    title = db_info.get("title", [{}])
    db_title = title[0].get("plain_text", "Untitled") if title else "Untitled"
    props = db_info.get("properties", {})
    print(f"  Title: {db_title}")
    print(f"  Properties ({len(props)}): {list(props.keys())}")
    print(f"\n  Database ID: {PAGE_ID.replace('-', '')}")
    print(f"  Copy to .env: NOTION_DATABASE_ID={PAGE_ID.replace('-', '')}")
    sys.exit(0)
except Exception as e:
    print(f"  Not a database: {e}")
    print()

# 2. Check child blocks for databases
print("--- Looking for child databases ---")
try:
    children = notion.blocks.children.list(PAGE_ID)
    results = children.get("results", [])

    found = False
    for block in results:
        block_type = block.get("type", "")
        block_id = block.get("id", "")

        if block_type == "child_database":
            found = True
            db_title = block.get("child_database", {}).get("title", "Untitled")
            db_uuid = block_id  # full UUID is the database ID

            print(f"\n  [CHILD DATABASE] Title: {db_title}")
            print(f"  Database ID (with hyphens): {db_uuid}")
            print(f"  Database ID (plain): {db_uuid.replace('-', '')}")

            # Get properties
            try:
                info = notion.databases.retrieve(db_uuid)
                props = info.get("properties", {})
                print(f"  Properties ({len(props)}):")
                for name, config in props.items():
                    ptype = config.get("type", "?")
                    print(f"    - {name} ({ptype})")
            except Exception as e:
                print(f"  Error getting properties: {e}")

            print(f"\n  >>> Copy this to .env:")
            print(f"  NOTION_DATABASE_ID={db_uuid.replace('-', '')}")

        elif block_type == "link_preview":
            url = block.get("link_preview", {}).get("url", "")
            if "notion.com" in url:
                print(f"\n  [LINK PREVIEW] URL: {url}")
                # Extract possible database ID from URL
                import re
                ids = re.findall(r'([a-f0-9]{32})', url)
                for id_ in ids:
                    formatted = f"{id_[:8]}-{id_[8:12]}-{id_[12:16]}-{id_[16:20]}-{id_[20:32]}"
                    print(f"  Possible DB ID: {formatted}")
                    try:
                        info = notion.databases.retrieve(formatted)
                        props = info.get("properties", {})
                        print(f"  -> IS a database! Properties: {list(props.keys())}")
                        print(f"\n  >>> Copy to .env: NOTION_DATABASE_ID={id_}")
                    except:
                        print(f"  -> Not directly accessible")

    if not found:
        print("  No child databases found. The page might need to be shared with your integration.")
        print("\n  Suggestion: Go to the page -> Share -> Add 'Non-Tech Roles Access' integration")

except Exception as e:
    print(f"  Error: {e}")

print()
