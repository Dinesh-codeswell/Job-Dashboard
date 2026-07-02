#!/usr/bin/env python3
"""
Test script for Job Description Formatter

Tests the formatter with real LinkedIn HTML to verify proper formatting.
"""

import sys
import logging
from pathlib import Path

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Add dashboard to path
sys.path.insert(0, str(Path(__file__).parent / "Job Dashboard" / "Dashboard"))

from dashboard.data.jd_formatter import format_job_description

# Test HTML from LinkedIn (the problematic example)
test_html = '''<section class="show-more-less-html" data-max-lines="5"> <div class="show-more-less-html__markup show-more-less-html__markup--clamp-after-5 relative overflow-hidden"> Ways of working: Mandate 3 : Onsite - Office / Field: Employees are expected to work from the office on all days out of their respective base locations.<br><br><strong>About Swiggy Instamart<br><br></strong>Swiggy Instamart, is building the convenience grocery segment in India. We offer more than 30000 + assortments / products to our customers within 10-15 mins. We are striving to augment our consumer promise of enabling unparalleled convenience by making grocery delivery instant and delightful. Instamart has been operating in 90+ cities across India and plans to expand to a few more soon. We have seen immense love from the customers till now and are excited to redefine how India shops.<br><br><strong>About The Role<br><br></strong>We are looking for a Senior Manager – Partnerships to drive strategic partnerships for NOICE, our private label brand. This role will focus on building and scaling distribution and growth partnerships, including vending machine networks, D2C brand collaborations, and new channel partnerships to expand brand reach and revenue.<br><br>The ideal candidate will have strong experience in partnership development, business development, and alternate distribution channels, especially within D2C, FMCG, retail, or vending machine ecosystems.<br><br><strong>Key Responsibilities<br><br></strong><strong>Strategic Partnerships: <br><br></strong><ul><li>Identify, evaluate, and onboard strategic partners to expand the reach of NOCIE products.</li><li>Build partnerships with vending machine operators, corporate offices, co-working spaces, airports, educational institutions, and retail chains.</li><li>Drive collaborations with D2C brands and emerging consumer brands for co-selling, bundling, and cross-promotions.<br><br></li></ul><strong>Channel Expansion<br><br></strong><ul><li>Develop new distribution channels through partnerships beyond traditional retail.</li><li>Scale vending machine business across partners.<br><br></li></ul><strong>Partnership Management<br><br></strong><ul><li>Own the end-to-end lifecycle of partnerships including sourcing, negotiation, onboarding, and relationship management.</li><li>Drive commercial negotiations, revenue share models, and joint growth plans with partners.</li><li>Monitor performance metrics, P&amp;L impact, and growth opportunities across partnerships.<br><br></li></ul><strong>Cross-Functional Collaboration<br><br></strong><ul><li>Work closely with category, supply chain, marketing, and operations teams to execute partnership initiatives.</li><li>Coordinate with product and brand teams for launches, campaigns, and partner activations.<br><br></li></ul><strong>Growth &amp; Strategy<br><br></strong><ul><li>Identify new market opportunities and innovative partnership models to grow NOCIE's distribution.</li><li>Track industry trends across vending, D2C, and new-age retail ecosystems.<br><br></li></ul><strong>Key Requirements<br><br></strong><ul><li>3–6 years of experience in partnerships, business development, or channel expansion.</li><li>Experience working with D2C brands, FMCG, retail, vending machine ecosystems, or alternate distribution models.</li><li>Strong commercial acumen and negotiation skills.</li><li>Experience building B2B partnerships and strategic alliances.</li><li>Ability to manage multiple partners and drive growth initiatives at scale.</li><li>Excellent stakeholder management and cross-functional collaboration skills.<br><br></li></ul>"We are an equal opportunity employer and all qualified applicants will receive consideration for employment without regards to race, colour, religion, sex, disability status, or any other characteristic protected by the law" </div> <button class="show-more-less-html__button show-more-less-button show-more-less-html__button--more ml-0.5" data-tracking-control-name="public_jobs_show-more-html-btn" aria-label="" aria-expanded="false"> <!----> <icon class="show-more-less-html__button-icon show-more-less-button-icon lazy-loaded" aria-hidden="true" aria-busy="false"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" preserveAspectRatio="xMinYMin meet" focusable="false" class="lazy-loaded" aria-busy="false"><path d="M8 9l5.93-4L15 6.54l-6.15 4.2a1.5 1.5 0 01-1.69 0L1 6.54 2.07 5z" fill="currentColor"></path></svg></icon> </button> <button class="show-more-less-html__button show-more-less-button show-more-less-html__button--less ml-0.5" data-tracking-control-name="public_jobs_show-less-html-btn" aria-label="" aria-expanded="true"> <!----> <icon class="show-more-less-html__button-icon show-more-less-button-icon lazy-loaded" aria-hidden="true" aria-busy="false"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" preserveAspectRatio="xMinYMin meet" focusable="false" class="lazy-loaded" aria-busy="false"><path d="M8 7l-5.9 4L1 9.5l6.2-4.2c.5-.3 1.2-.3 1.7 0L15 9.5 13.9 11 8 7z" fill="currentColor"></path></svg></icon> </button> <!----> </section>'''

def test_formatter():
    """Test the job description formatter."""
    print("=" * 80)
    print("JOB DESCRIPTION FORMATTER TEST")
    print("=" * 80)
    print()
    
    print("INPUT (Raw LinkedIn HTML):")
    print("-" * 80)
    print(test_html[:500] + "..." if len(test_html) > 500 else test_html)
    print()
    print(f"Input length: {len(test_html)} characters")
    print()
    
    print("FORMATTING...")
    print()
    formatted = format_job_description(test_html)
    print()
    
    print(f"Output length: {len(formatted)} characters")
    print()
    
    print("OUTPUT (Formatted HTML):")
    print("=" * 80)
    if formatted:
        # Show first 1000 chars
        if len(formatted) > 1000:
            print(formatted[:1000])
            print(f"\n... ({len(formatted) - 1000} more characters) ...\n")
        else:
            print(formatted)
    else:
        print("⚠️  WARNING: Formatter returned empty string!")
        print("This indicates an issue with the formatting logic.")
    print("=" * 80)
    print()
    
    # Verify key features
    print("VERIFICATION:")
    print("-" * 80)
    
    checks = [
        ("Headings converted to <h3>", "<h3>" in formatted),
        ("Paragraphs wrapped in <p>", "<p>" in formatted),
        ("Lists preserved", "<ul>" in formatted and "<li>" in formatted),
        ("LinkedIn wrappers removed", "show-more-less" not in formatted),
        ("Buttons removed", "<button" not in formatted),
        ("SVG icons removed", "<svg" not in formatted),
        ("Proper spacing (double newlines)", "\n\n" in formatted),
        ("No empty paragraphs", "<p></p>" not in formatted and "<p> </p>" not in formatted),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not check_result:
            all_passed = False
    
    print("-" * 80)
    print()
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED! Formatter is working correctly.")
    else:
        print("⚠️  SOME CHECKS FAILED. Review the output above.")
    
    print()
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = test_formatter()
    sys.exit(0 if success else 1)
