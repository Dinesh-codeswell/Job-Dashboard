"""
Quick test to verify date validation works correctly.
"""

from datetime import datetime, timedelta, timezone
import re


def is_job_fresh(posted_date: str, max_days: int = 2) -> bool:
    """Check if job is within max_days threshold."""
    if not posted_date:
        return False
    
    posted_str = str(posted_date).strip().lower()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_days)
    
    # Parse relative dates (e.g., "1 day ago", "2 weeks ago")
    if "day" in posted_str or "week" in posted_str or "month" in posted_str or "hour" in posted_str:
        # Extract number
        match = re.search(r'(\d+)', posted_str)
        if match:
            num = int(match.group(1))
            
            if "hour" in posted_str:
                job_time = now - timedelta(hours=num)
            elif "day" in posted_str:
                job_time = now - timedelta(days=num)
            elif "week" in posted_str:
                job_time = now - timedelta(weeks=num)
            elif "month" in posted_str:
                job_time = now - timedelta(days=num * 30)
            else:
                return False
            
            return job_time >= cutoff
    
    # Parse ISO format dates
    iso_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', posted_str)
    if iso_match:
        try:
            y, m, d = map(int, iso_match.groups())
            job_time = datetime(y, m, d, tzinfo=timezone.utc)
            return job_time >= cutoff
        except:
            pass
    
    # If can't parse, assume it's fresh (don't filter)
    return True


# Test cases
test_cases = [
    # (posted_date, max_days, expected_result, description)
    ("1 day ago", 2, True, "1 day old - should be fresh"),
    ("2 days ago", 2, True, "2 days old - should be fresh (boundary)"),
    ("3 days ago", 2, False, "3 days old - should be stale"),
    ("1 week ago", 2, False, "1 week old - should be stale"),
    ("1 hour ago", 2, True, "1 hour old - should be fresh"),
    ("24 hours ago", 2, True, "24 hours old - should be fresh"),
    ("48 hours ago", 2, True, "48 hours old - should be fresh (boundary)"),
    ("72 hours ago", 2, False, "72 hours old - should be stale"),
    ("2026-04-07", 2, True, "Today's date - should be fresh"),
    ("2026-04-05", 2, True, "2 days ago - should be fresh"),
    ("2026-04-04", 2, False, "3 days ago - should be stale"),
    ("", 2, False, "Empty string - should be stale"),
    ("just now", 2, True, "Just now - should be fresh"),
    ("2 weeks ago", 2, False, "2 weeks ago - should be stale"),
]

print("=" * 70)
print("DATE VALIDATION TEST SUITE")
print("=" * 70)

passed = 0
failed = 0

for posted_date, max_days, expected, description in test_cases:
    result = is_job_fresh(posted_date, max_days)
    status = "PASS" if result == expected else "FAIL"
    
    if result == expected:
        passed += 1
        symbol = "✓"
    else:
        failed += 1
        symbol = "✗"
    
    print(f"{symbol} {status}: {description}")
    print(f"   Input: '{posted_date}' | Expected: {expected} | Got: {result}")
    print()

print("=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 70)

if failed == 0:
    print("All tests passed!")
    exit(0)
else:
    print(f"Some tests failed!")
    exit(1)
