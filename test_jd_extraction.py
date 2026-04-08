#!/usr/bin/env python3
"""
Test script to verify job description extraction logic.
"""

from job_description_extractor import JobDescriptionExtractor

# Sample LinkedIn HTML (from your example)
linkedin_html = """
<div class="_037030c5 bf0a3c99 _3449b89b _24b4c949 fe600429 ed572227 e14def77 _7e7c9934 _6c3e6f39 _55fe9113 _5e46bee6">
    <div class="ed572227 fbe0c389 _8f59eabb _6c3e6f39 _55fe9113 _5e46bee6"></div>
    <div class="ed572227 fbe0c389 _7e7c9934 _6c3e6f39 _55fe9113 _5e46bee6 _4c4b1ce1">
        <h2 class="_9a287b82 db4cc1ff d9633dd2 _60336034 _4aaab8b3 ad8b4dc4 e9bba4b5 e2946e59 _81563674 _73bff215 _4b80986e">About the job</h2>
    </div>
    <p class="_9a287b82 e30101d1 _60336034 _4aaab8b3 _7ac97b09 dc967f2a e2946e59 _81563674 _73bff215 _4b80986e cf312a20">
        <span class="ec6bd25d b652a7b7" tabindex="-1" data-testid="expandable-text-box">
            <strong>Company Description</strong>
            <span class="c27dbadc"> </span>
            <p>Internzvalley is committed to delivering outstanding upskilling opportunities for aspiring professionals and students.</p>
            <span class="c27dbadc"> </span>
            <strong>Role Description</strong>
            <span class="c27dbadc"> </span>
            <p>We are seeking a Marketing Team Lead for a full-time, on-site role located in Bengaluru.</p>
            <span class="c27dbadc"> </span>
            <strong>Qualifications</strong>
            <span class="c27dbadc"> </span>
            <ul class="_89d2b19b _5d67558c">
                <li>Strong Team Leadership and Team Management skills</li>
                <li>Strong Communication skills to effectively interact</li>
                <li>Proven experience in Marketing and Sales</li>
            </ul>
        </span>
    </p>
</div>
"""

# Sample Indeed HTML (with garbage)
indeed_html = """
<div id="jobDescriptionText">
    <h3>What we offer:</h3>
    <ul>
        <li>-----------------</li>
    </ul>
    <p>At Magna, you can expect an engaging and dynamic environment.</p>
    <h3>Your Responsibilities:</h3>
    <ul>
        <li>Plan, coordinate, and support internal and external IT audits</li>
        <li>Act as the interface between IT operations and auditors</li>
    </ul>
    <h3>Worker Type:</h3>
    <ul>
        <li>---------------</li>
    </ul>
    <p>Regular / Permanent</p>
</div>
"""

def test_linkedin_extraction():
    """Test LinkedIn extraction."""
    print("=" * 80)
    print("TESTING LINKEDIN EXTRACTION")
    print("=" * 80)
    
    extractor = JobDescriptionExtractor()
    result = extractor._process_linkedin_html(linkedin_html)
    
    print("\nEXTRACTED HTML:")
    print(result)
    
    # Verify structure
    checks = [
        ('<h3>Company Description</h3>' in result, "✅ Company Description is H3"),
        ('<h3>Role Description</h3>' in result, "✅ Role Description is H3"),
        ('<h3>Qualifications</h3>' in result, "✅ Qualifications is H3"),
        ('<p>Internzvalley' in result, "✅ Paragraph preserved"),
        ('<ul>' in result, "✅ List preserved"),
        ('<li>Strong Team Leadership' in result, "✅ List items preserved"),
    ]
    
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    for passed, message in checks:
        print(f"{'✅' if passed else '❌'} {message}")
    
    all_passed = all(check[0] for check in checks)
    print(f"\n{'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}")
    return all_passed

def test_indeed_extraction():
    """Test Indeed extraction with garbage filtering."""
    print("\n" + "=" * 80)
    print("TESTING INDEED EXTRACTION")
    print("=" * 80)
    
    extractor = JobDescriptionExtractor()
    result = extractor.extract_indeed(indeed_html)
    
    print("\nEXTRACTED HTML:")
    print(result)
    
    # Verify structure
    checks = [
        ('<h3>What we offer:</h3>' in result, "✅ Heading preserved"),
        ('<h3>Your Responsibilities:</h3>' in result, "✅ Heading preserved"),
        ('<p>At Magna' in result, "✅ Paragraph preserved"),
        ('<li>Plan, coordinate' in result, "✅ Valid list item preserved"),
        ('<li>-----------------</li>' not in result, "✅ Garbage filtered out"),
        ('<li>---------------</li>' not in result, "✅ Garbage filtered out"),
    ]
    
    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("=" * 80)
    for passed, message in checks:
        print(f"{'✅' if passed else '❌'} {message}")
    
    all_passed = all(check[0] for check in checks)
    print(f"\n{'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}")
    return all_passed

if __name__ == '__main__':
    linkedin_passed = test_linkedin_extraction()
    indeed_passed = test_indeed_extraction()
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"LinkedIn Extraction: {'✅ PASSED' if linkedin_passed else '❌ FAILED'}")
    print(f"Indeed Extraction: {'✅ PASSED' if indeed_passed else '❌ FAILED'}")
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if (linkedin_passed and indeed_passed) else '❌ SOME TESTS FAILED'}")
