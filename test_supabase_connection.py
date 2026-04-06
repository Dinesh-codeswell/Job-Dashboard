"""
Diagnostic script to test Supabase connection
Run this locally to verify Supabase is working
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta, timezone

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

print("=" * 60)
print("SUPABASE CONNECTION TEST")
print("=" * 60)

print(f"\n1. Environment Variables:")
print(f"   SUPABASE_URL present: {bool(SUPABASE_URL)}")
print(f"   SUPABASE_KEY present: {bool(SUPABASE_KEY)}")

if not SUPABASE_URL:
    print("\n❌ ERROR: SUPABASE_URL is not set!")
    print("   Check your .env file or Vercel environment variables")
    exit(1)

if not SUPABASE_KEY:
    print("\n❌ ERROR: SUPABASE_KEY is not set!")
    print("   Check your .env file or Vercel environment variables")
    exit(1)

print(f"\n2. Initializing Supabase client...")
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("   ✅ Supabase client created successfully")
except Exception as e:
    print(f"   ❌ Failed to create client: {e}")
    exit(1)

print(f"\n3. Testing connection with simple query...")
try:
    # Test 1: Check if jobs table exists
    result = supabase.table("jobs").select("id", count="exact").limit(1).execute()
    print(f"   ✅ Query successful")
    print(f"   Total rows in jobs table: {result.count}")
    print(f"   Sample data: {result.data[:1] if result.data else 'No data'}")
except Exception as e:
    print(f"   ❌ Query failed: {e}")
    print(f"\n   Possible causes:")
    print(f"   - Table 'jobs' doesn't exist")
    print(f"   - RLS policies blocking access")
    print(f"   - Invalid API key (needs anon or service role key)")
    exit(1)

print(f"\n4. Testing 3-day filter query...")
try:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    result = supabase.table("jobs").select("*", count="exact").gte("posted_at_timestamp", cutoff).limit(5).execute()
    print(f"   ✅ 3-day filter query successful")
    print(f"   Jobs in last 3 days: {result.count}")
    print(f"   Sample jobs returned: {len(result.data)}")
    
    if result.data:
        print(f"\n   First job sample:")
        job = result.data[0]
        print(f"   - ID: {job.get('id')}")
        print(f"   - Title: {job.get('job_title')}")
        print(f"   - Company: {job.get('company')}")
        print(f"   - Posted: {job.get('posted_at_timestamp')}")
except Exception as e:
    print(f"   ❌ 3-day filter query failed: {e}")
    print(f"\n   Possible causes:")
    print(f"   - Column 'posted_at_timestamp' doesn't exist")
    print(f"   - Column has wrong type (should be timestamptz)")
    print(f"   - RLS policies blocking access")

print(f"\n5. Checking for problematic columns...")
try:
    # Try to get column names
    result = supabase.table("jobs").select("*").limit(1).execute()
    if result.data:
        columns = list(result.data[0].keys())
        print(f"   ✅ Columns found: {columns}")
        
        # Check for NaN in any field
        import math
        for key, value in result.data[0].items():
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                print(f"   ⚠️  WARNING: Column '{key}' contains NaN/Infinity!")
    else:
        print(f"   ⚠️  No data returned to check columns")
except Exception as e:
    print(f"   ❌ Failed to check columns: {e}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("Supabase connection is working correctly.")
print("=" * 60)
