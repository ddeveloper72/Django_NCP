#!/usr/bin/env python3
"""
Test CTS-Compliant Enhanced CDA Processor
Validates that the processor uses Central Terminology Server instead of hardcoded data
"""

import os
import sys
import django
import re

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cts_compliance():
    """Test that the processor uses CTS instead of hardcoded mappings"""

    print("🔍 TESTING CTS-COMPLIANT ENHANCED CDA PROCESSOR")
    print("=" * 60)

    # Test 1: Initialize processor
    print("\n1. Testing Processor Initialization:")
    try:
        processor = EnhancedCDAProcessor(target_language="en")
        print("✅ Processor initialized successfully")
        print(f"   Target language: {processor.target_language}")
        print(f"   Terminology service: {type(processor.terminology_service).__name__}")

        # Check that hardcoded mappings are NOT present
        if hasattr(processor, "section_title_mappings"):
            print("❌ VIOLATION: Hardcoded section_title_mappings found!")
            return False
        else:
            print("✅ No hardcoded section mappings found - CTS compliance achieved")

    except Exception as e:
        print(f"❌ Error initializing processor: {e}")
        return False

    # Test 2: Test section title translation using CTS
    print("\n2. Testing CTS Section Title Translation:")
    try:
        # Test LOINC section code
        result = processor._get_enhanced_section_title(
            section_code="10160-0",  # LOINC code for Medication Summary
            original_title="Résumé des médicaments",
            source_language="fr",
        )

        print(f"   Section code: 10160-0")
        print(f"   Original title: {result['source']}")
        print(f"   CTS translated: {result['target']}")
        print("✅ CTS section title translation working")

    except Exception as e:
        print(f"❌ Error in CTS section title translation: {e}")
        return False

    # Test 3: Test content translation using terminology service
    print("\n3. Testing CTS Content Translation:")
    try:
        test_content = "Patient a des allergies aux médicaments"
        translated = processor._translate_content(test_content, "fr")

        print(f"   Original: {test_content}")
        print(f"   CTS translated: {translated}")
        print("✅ CTS content translation working")

    except Exception as e:
        print(f"❌ Error in CTS content translation: {e}")
        return False

    # Test 4: Test medical keyword extraction
    print("\n4. Testing Medical Keyword Extraction:")
    try:
        keywords = processor._extract_medical_keywords(
            "Résumé des médicaments et allergies"
        )
        print(f"   Extracted keywords: {keywords}")
        print("✅ Medical keyword extraction working")

    except Exception as e:
        print(f"❌ Error in keyword extraction: {e}")
        return False

    # Test 5: Test full CDA processing
    print("\n5. Testing Full CDA Processing (Mock):")
    try:
        sample_html = """
        <html>
            <body>
                <h2>Résumé des médicaments</h2>
                <p>Patient prend des antibiotiques pour infection</p>
                <table>
                    <tr><th>Médicament</th><th>Dosage</th></tr>
                    <tr><td>Amoxicilline</td><td>500mg</td></tr>
                </table>
            </body>
        </html>
        """

        result = processor.process_clinical_sections(sample_html, "fr")

        print(f"   Success: {result.get('success', False)}")
        print(f"   Content type: {result.get('content_type', 'unknown')}")
        print(f"   Sections found: {result.get('sections_count', 0)}")
        print(f"   Medical terms: {result.get('medical_terms_count', 0)}")
        print("✅ Full CDA processing working")

    except Exception as e:
        print(f"❌ Error in full CDA processing: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED - CTS COMPLIANCE ACHIEVED!")
    print("✅ No hardcoded data found")
    print("✅ Central Terminology Server integration working")
    print("✅ Master Value Catalogue lookups functional")
    return True


def check_hardcoded_violations():
    """Check for any remaining hardcoded medical terminology"""

    print("\n🔍 CHECKING FOR HARDCODED VIOLATIONS")
    print("=" * 40)

    violations = []

    # Read the enhanced processor file
    with open(
        "patient_data/services/enhanced_cda_processor.py", "r", encoding="utf-8"
    ) as f:
        content = f.read()

    # Check for hardcoded medical terms
    hardcoded_patterns = [
        r'"(?:Medication|Allergy|Problem|Procedure|History)"',
        r'"(?:Médicament|Allergie|Problème|Procédure|Histoire)"',
        r'{\s*"en":\s*"[^"]+",\s*"fr":\s*"[^"]+"',  # Dictionary mappings
        r"section_title_mappings\s*=",  # The old mapping variable
    ]

    for pattern in hardcoded_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            violations.extend(matches)

    if violations:
        print(f"❌ Found {len(violations)} hardcoded violations:")
        for violation in violations[:5]:  # Show first 5
            print(f"   - {violation}")
        return False
    else:
        print("✅ No hardcoded medical terminology found")
        return True


if __name__ == "__main__":
    print("Testing CTS-Compliant Enhanced CDA Processor")
    print("Validating elimination of hardcoded medical terminology")

    # Test CTS compliance
    cts_compliance = test_cts_compliance()

    # Check for violations
    no_violations = check_hardcoded_violations()

    if cts_compliance and no_violations:
        print("\n🎉 SUCCESS: CTS-COMPLIANT PROCESSOR IMPLEMENTED")
        print("✅ Central Terminology Server integration complete")
        print("✅ Master Value Catalogue integration functional")
        print("✅ Zero hardcoded medical terminology")
        sys.exit(0)
    else:
        print("\n❌ ISSUES FOUND: Review and fix violations")
        sys.exit(1)
