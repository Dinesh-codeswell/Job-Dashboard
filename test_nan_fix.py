"""Quick test to verify JSON NaN handling"""
import math
import json
from datetime import datetime, timezone

# Test data with NaN values
test_data = {
    'success': True,
    'similar_jobs': [
        {
            'Job Title': 'Test Position',
            'Company': 'Test Corp',
            'Company Logo': float('nan'),  # This was causing the error
            'posted_at_timestamp': datetime.now(timezone.utc).isoformat(),
            'salary': float('inf'),
            'valid_field': 'This is fine'
        }
    ]
}

# Standard json.dumps would fail or output NaN
print("=== Standard json.dumps ===")
try:
    result = json.dumps(test_data)
    print(result)
except Exception as e:
    print(f"Error: {e}")

# Custom sanitizer
def sanitize_for_json(value):
    """Recursively sanitize values to remove NaN/Infinity."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    elif isinstance(value, dict):
        return {k: sanitize_for_json(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [sanitize_for_json(item) for item in value]
    return value

print("\n=== With NaN sanitizer ===")
sanitized = sanitize_for_json(test_data)
result = json.dumps(sanitized)
print(result)

# Verify it's valid JSON
parsed = json.loads(result)
assert parsed['similar_jobs'][0]['Company Logo'] is None
assert parsed['similar_jobs'][0]['valid_field'] == 'This is fine'
print("\n✅ Test passed! NaN values properly converted to null")
