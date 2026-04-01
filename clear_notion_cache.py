#!/usr/bin/env python3
"""Clear the Notion duplicate cache."""
import os

cache_file = "notion_added_jobs_cache.json"

if os.path.exists(cache_file):
    os.remove(cache_file)
    print(f"✓ Cache cleared: {cache_file}")
    print("You can now re-run the scraper and jobs will be added again.")
else:
    print("No cache file found.")
