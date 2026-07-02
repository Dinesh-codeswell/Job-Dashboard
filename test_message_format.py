#!/usr/bin/env python3
"""
Test Message Formatting
========================
Tests the new message format with cleaned posted dates, company logos, and employment types.
"""

import re

def clean_posted_date(posted_date: str) -> str:
    """Clean posted date by removing applicant count information."""
    if not posted_date:
        return 'Recently'
    
    # Remove applicant count patterns
    posted_date = re.sub(r'\s*Be among the first \d+ applicants.*', '', posted_date, flags=re.IGNORECASE)
    posted_date = re.sub(r'\s*\d+\s+applicants.*', '', posted_date, flags=re.IGNORECASE)
    posted_date = re.sub(r'\s*Over \d+\s+applicants.*', '', posted_date, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    posted_date = ' '.join(posted_date.split())
    
    return posted_date.strip() or 'Recently'


def format_message(job):
    """Format job as WhatsApp message."""
    job_title = job.get('Job Title', 'Unknown Role')
    company = job.get('Company', 'Unknown Company')
    company_logo = job.get('Company Logo', '')
    location = job.get('Location', 'Unknown Location')
    employment_type = job.get('Employment Type', '')
    job_url = job.get('Job URL', '')
    posted_date_raw = job.get('Posted', 'Recently')
    
    # Clean posted date
    posted_date = clean_posted_date(posted_date_raw)
    
    # Format message (without logo URL in text)
    message = f"""🚀 *New Job Alert!*

📌 *Role:* {job_title}
🏢 *Company:* {company}"""
    
    # Add employment type if available
    if employment_type and employment_type.strip():
        message += f"\n💼 *Type:* {employment_type}"
    
    message += f"""
📍 *Location:* {location}
⏰ *Posted:* {posted_date}

🔗 *Apply Now:* {job_url}"""
    
    # Return message and logo URL separately
    return message, company_logo if company_logo and company_logo.strip() else None


# Test cases
print("="*70)
print("MESSAGE FORMAT TESTING")
print("="*70)
print()

# Test 1: Job with all fields
print("Test 1: Complete job with logo and employment type")
print("-"*70)
job1 = {
    'Job Title': 'Product Manager',
    'Company': 'Reliance Industries Limited',
    'Company Logo': 'https://media.licdn.com/dms/image/v2/C4D0BAQGkZlaLcHqUaQ/company-logo_100_100/company-logo_100_100/0/1630557793413/reliance_industries_limited_logo?e=1748476800&v=beta&t=abc123',
    'Location': 'Mumbai, Maharashtra',
    'Employment Type': 'Full-time',
    'Posted': '8 hours ago   Be among the first 25 applicants',
    'Job URL': 'https://linkedin.com/jobs/12345'
}
message, logo_url = format_message(job1)
print(message)
if logo_url:
    print(f"\n📸 Company Logo Image: {logo_url}")
    print("   (This will display as an image in WhatsApp)")
print()

# Test 2: Job with applicant count
print("Test 2: Job with applicant count")
print("-"*70)
job2 = {
    'Job Title': 'Senior Consultant',
    'Company': 'Deloitte',
    'Company Logo': 'https://media.licdn.com/dms/image/deloitte-logo.jpg',
    'Location': 'Bangalore, Karnataka',
    'Employment Type': 'Contract',
    'Posted': '12 hours ago  86 applicants',
    'Job URL': 'https://linkedin.com/jobs/67890'
}
message, logo_url = format_message(job2)
print(message)
if logo_url:
    print(f"\n📸 Company Logo Image: {logo_url}")
print()

# Test 3: Job without logo
print("Test 3: Job without company logo")
print("-"*70)
job3 = {
    'Job Title': 'Business Analyst',
    'Company': 'Google',
    'Company Logo': '',
    'Location': 'Hyderabad, Telangana',
    'Employment Type': 'Full-time',
    'Posted': '20 hours ago   Be among the first 25 applicants',
    'Job URL': 'https://linkedin.com/jobs/11111'
}
message, logo_url = format_message(job3)
print(message)
if logo_url:
    print(f"\n📸 Company Logo Image: {logo_url}")
else:
    print("\n(No company logo - text-only message)")
print()

# Test 4: Job without employment type
print("Test 4: Job without employment type")
print("-"*70)
job4 = {
    'Job Title': 'Strategy Manager',
    'Company': 'McKinsey & Company',
    'Company Logo': 'https://media.licdn.com/dms/image/mckinsey-logo.jpg',
    'Location': 'Delhi, NCR',
    'Employment Type': '',
    'Posted': '1 day ago  Over 100 applicants',
    'Job URL': 'https://linkedin.com/jobs/22222'
}
message, logo_url = format_message(job4)
print(message)
if logo_url:
    print(f"\n📸 Company Logo Image: {logo_url}")
print()

# Test 5: Minimal job
print("Test 5: Minimal job (no logo, no employment type)")
print("-"*70)
job5 = {
    'Job Title': 'Associate',
    'Company': 'Bain & Company',
    'Company Logo': '',
    'Location': 'Chennai, Tamil Nadu',
    'Employment Type': '',
    'Posted': '2 days ago',
    'Job URL': 'https://linkedin.com/jobs/33333'
}
message, logo_url = format_message(job5)
print(message)
if logo_url:
    print(f"\n📸 Company Logo Image: {logo_url}")
else:
    print("\n(No company logo - text-only message)")
print()

# Test posted date cleaning
print("="*70)
print("POSTED DATE CLEANING TESTS")
print("="*70)
print()

test_dates = [
    "8 hours ago   Be among the first 25 applicants",
    "12 hours ago  86 applicants",
    "20 hours ago   Be among the first 25 applicants",
    "1 day ago  Over 100 applicants",
    "2 days ago",
    "3 weeks ago  200 applicants",
    "1 month ago   Be among the first 50 applicants"
]

for date in test_dates:
    cleaned = clean_posted_date(date)
    print(f"Original: {date}")
    print(f"Cleaned:  {cleaned}")
    print()

print("="*70)
print("✅ All tests complete!")
print("="*70)
