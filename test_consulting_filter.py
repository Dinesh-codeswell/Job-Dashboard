#!/usr/bin/env python3
"""
Test the consulting job filter logic
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import the validation function
from scrape_all_india_jobs import UnifiedIndiaJobsScraper

# Test cases from your affected jobs
test_jobs = [
    # Should be REJECTED
    ("Founder's Office Intern – L&D (Entrepreneurial)", False, "Intern + Founder's Office"),
    ("Founder's Office Intern", False, "Intern + Founder's Office"),
    ("Intern", False, "Intern"),
    ("Data Analyst", False, "Analyst without consulting"),
    ("Product Development Internship in Mumbai", False, "Internship"),
    ("Business Development Intern", False, "Intern"),
    ("Finance Internship in Mumbai", False, "Internship"),
    ("Post a job", False, "Invalid title"),
    ("Oracle Tech Architecture and Middleware-MuleSoft-Senior", False, "Architect without consulting"),
    ("Oracle Fusion Technical with AI expertise", False, "Technical without consulting"),
    ("Network Engineer - IT Service", False, "Engineer without consulting"),
    ("Security Technical Engineer - IT", False, "Engineer without consulting"),
    ("Oracle Cloud Infrastructure Admin- Quick Joiners", False, "Admin without consulting"),
    ("Cyber Security Architect  - Team Leader (Professional)", False, "Architect without consulting"),
    ("Solution Architect - Cyber Security", False, "Architect without consulting"),
    
    # Should be ACCEPTED
    ("Consultant - Performance Transformation", True, "Has Consultant"),
    ("Business Consultant", True, "Has Consultant"),
    ("Analyst - Business Consulting Risk", True, "Has Consulting"),
    ("Functional Consultant - Requisition to Pay", True, "Has Consultant"),
    ("Freelance Strategy Consultant: MedCare", True, "Has Consultant"),
    ("Assistant Director - Manager - Global CS Strategy Execution Office", False, "No consulting keyword"),
    ("Associate Managing Consultant", True, "Has Consultant"),
    ("EY - GDS Consulting - AIA - Gen AI - Manager", True, "Has Consulting"),
    ("Computer Vision Consultant", True, "Has Consultant"),
    ("Oracle Fusion Procurement Functional Consultant", True, "Has Consultant"),
    ("Solution Consultant II", True, "Has Consultant"),
    ("SAP FIORI CONSULTANT", True, "Has Consultant"),
    ("Consultant - Security", True, "Has Consultant"),
    ("Cisco Umbrella Consultant", True, "Has Consultant"),
]

print("="*80)
print("TESTING CONSULTING JOB FILTER")
print("="*80)

scraper = UnifiedIndiaJobsScraper(sheet_id="test", credentials_file="test")

passed = 0
failed = 0

for job_title, expected_valid, description in test_jobs:
    is_valid, reason = scraper.is_valid_consulting_job(job_title)
    
    status = "✅ PASS" if is_valid == expected_valid else "❌ FAIL"
    
    if is_valid != expected_valid:
        failed += 1
        print(f"{status} | Expected: {expected_valid}, Got: {is_valid}")
        print(f"       Title: {job_title}")
        print(f"       Reason: {reason}")
        print(f"       ({description})")
        print()
    else:
        passed += 1
        action = "ACCEPTED" if is_valid else "REJECTED"
        print(f"{status} | {action:10} | {job_title[:60]}")

print("\n" + "="*80)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_jobs)} tests")
print("="*80)

if failed == 0:
    print("✅ All tests passed! Filter is working correctly.")
else:
    print(f"⚠️  {failed} test(s) failed. Review the filter logic.")
