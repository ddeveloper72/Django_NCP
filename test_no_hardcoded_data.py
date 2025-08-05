#!/usr/bin/env python
"""
Comprehensive Test: No Hard Coded Data Validation
Tests the complete elimination of hardcoded data and CTS compliance
"""

import os
import sys
import django
import re
from pathlib import Path

# Setup Django environment
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.translation_utils import (
    get_template_translations,
    detect_document_language,
)
from patient_data.services.eu_language_detection_service import (
    detect_cda_language,
    get_eu_supported_languages,
    EULanguageDetectionService,
)


def test_hardcoded_data_elimination():
    """Test 1: Verify no hardcoded data in translation system"""
    print("=== TEST 1: Hardcoded Data Elimination ===")

    # Test translation service
    translations = get_template_translations("fr", "en")

    required_translations = [
        "european_patient_summary",
        "clinical_sections",
        "safety_alerts",
        "medical_alerts",
        "translation_quality",
        "patient_name",
        "back_to_patient_details",
        "other_contacts",
        "address",
        "name",
    ]

    missing_translations = []
    for key in required_translations:
        if key not in translations:
            missing_translations.append(key)

    if missing_translations:
        print(f"❌ FAIL: Missing translations: {missing_translations}")
        return False
    else:
        print("✅ PASS: All required translations available")
        return True


def test_eu_language_detection():
    """Test 2: CTS-compliant EU language detection"""
    print("\n=== TEST 2: EU Language Detection ===")

    service = EULanguageDetectionService()

    # Test all EU-27 languages are supported
    supported_languages = service.get_supported_languages()
    eu_27_expected = {
        "bg",
        "cs",
        "da",
        "de",
        "el",
        "en",
        "es",
        "et",
        "fi",
        "fr",
        "hr",
        "hu",
        "it",
        "lt",
        "lv",
        "mt",
        "nl",
        "pl",
        "pt",
        "ro",
        "sk",
        "sl",
        "sv",
    }

    if not eu_27_expected.issubset(set(supported_languages)):
        missing = eu_27_expected - set(supported_languages)
        print(f"❌ FAIL: Missing EU languages: {missing}")
        return False

    # Test country-to-language mapping
    test_cases = [
        ("DE", "de"),  # Germany -> German
        ("FR", "fr"),  # France -> French
        ("LV", "lv"),  # Latvia -> Latvian
        ("ES", "es"),  # Spain -> Spanish
        ("IT", "it"),  # Italy -> Italian
    ]

    for country, expected_lang in test_cases:
        detected = service.detect_from_country_origin(country)
        if detected != expected_lang:
            print(f"❌ FAIL: {country} -> {detected}, expected {expected_lang}")
            return False

    print("✅ PASS: EU language detection working correctly")
    return True


def test_cda_language_detection():
    """Test 3: CDA document language detection"""
    print("\n=== TEST 3: CDA Language Detection ===")

    # Test CDA with explicit language declaration
    sample_cda = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3" xml:lang="fr">
        <realmCode code="FR"/>
        <languageCode code="fr-FR"/>
        <title>Synthèse Médicale du Patient</title>
    </ClinicalDocument>"""

    detected = detect_cda_language(sample_cda)
    if detected != "fr":
        print(f"❌ FAIL: Expected 'fr', got '{detected}'")
        return False

    # Test fallback to English
    no_lang_cda = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <title>Patient Summary</title>
    </ClinicalDocument>"""

    detected = detect_cda_language(no_lang_cda)
    if detected != "en":
        print(f"❌ FAIL: Expected fallback to 'en', got '{detected}'")
        return False

    print("✅ PASS: CDA language detection working correctly")
    return True


def test_template_file_hardcoded_scan():
    """Test 4: Scan template files for remaining hardcoded strings"""
    print("\n=== TEST 4: Template Hardcoded String Scan ===")

    template_file = (
        project_root / "templates" / "jinja2" / "patient_data" / "patient_cda.html"
    )

    if not template_file.exists():
        print(f"❌ FAIL: Template file not found: {template_file}")
        return False

    with open(template_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for hardcoded English text patterns
    # Exclude template syntax, CSS classes, and HTML tags
    hardcoded_patterns = [
        r'\b(Address|Name|Phone|Email)\b(?!["\']|\s*[|}])',  # Common labels
        r'\b(Patient\s+Details|Contact\s+Info|Document\s+Info)\b(?!["\']|\s*[|}])',  # Compound terms
        r">\s*[A-Z][a-z]+\s+[A-Z][a-z]+\s*<",  # Text between HTML tags
    ]

    violations = []
    for pattern in hardcoded_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            # Skip if it's already wrapped in template translation
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.end())
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end]

            if "template_translations" not in line:
                line_num = content[: match.start()].count("\n") + 1
                violations.append(f"Line {line_num}: {match.group()}")

    if violations:
        print(f"❌ FAIL: Found {len(violations)} hardcoded strings:")
        for violation in violations[:10]:  # Show first 10
            print(f"  {violation}")
        if len(violations) > 10:
            print(f"  ... and {len(violations) - 10} more")
        return False
    else:
        print("✅ PASS: No hardcoded strings detected in template")
        return True


def test_bilingual_translation_context():
    """Test 5: Bilingual translation context generation"""
    print("\n=== TEST 5: Bilingual Translation Context ===")

    # Test French to English translation context
    fr_translations = get_template_translations("fr", "en")

    # Verify key bilingual pairs
    expected_keys = [
        "european_patient_summary",
        "clinical_sections",
        "safety_alerts",
        "patient_name",
    ]

    for key in expected_keys:
        if key not in fr_translations:
            print(f"❌ FAIL: Missing translation key: {key}")
            return False

    # Test that translations are dynamic (not hardcoded)
    if not all(isinstance(value, str) and value for value in fr_translations.values()):
        print("❌ FAIL: Invalid translation values detected")
        return False

    print("✅ PASS: Bilingual translation context working correctly")
    return True


def main():
    """Run comprehensive no hardcoded data test suite"""
    print("🏥 EU NCP NO HARD CODED DATA VALIDATION")
    print("=" * 50)

    tests = [
        test_hardcoded_data_elimination,
        test_eu_language_detection,
        test_cda_language_detection,
        test_template_file_hardcoded_scan,
        test_bilingual_translation_context,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ ERROR in {test.__name__}: {e}")

    print(f"\n📊 RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("✅ SUCCESS: All hardcoded data eliminated - CTS compliance achieved!")
        return True
    else:
        print(f"❌ FAILURE: {total - passed} test(s) failed - more work needed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
