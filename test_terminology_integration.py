#!/usr/bin/env python

"""
Test script for terminology database integration
Tests the enhanced PSTableRenderer with MVC database lookups
"""

import os
import sys
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
django.setup()

from patient_data.services.ps_table_renderer import PSTableRenderer
from translation_services.terminology_translator import TerminologyTranslator


def test_terminology_lookup():
    """Test terminology database lookups"""
    print("=== Testing Terminology Database Integration ===\n")

    # Initialize renderer with English target language
    renderer = PSTableRenderer(target_language="en")
    print(f"✅ PSTableRenderer initialized with terminology translator")

    # Test LOINC code lookup
    print("\n--- Testing LOINC Code Lookup ---")
    loinc_codes = ["48765-2", "10160-0", "11450-4", "47519-4", "30954-2"]

    for code in loinc_codes:
        display_name = renderer._get_loinc_display_name(code)
        print(f"LOINC {code}: {display_name}")

    # Test direct terminology translator
    print("\n--- Testing Direct TerminologyTranslator ---")
    translator = TerminologyTranslator(target_language="en")

    test_codes = [
        {"code": "48765-2", "system": "2.16.840.1.113883.6.1", "name": "LOINC"},
        {"code": "232353008", "system": "2.16.840.1.113883.6.96", "name": "SNOMED CT"},
        {"code": "Z51.11", "system": "2.16.840.1.113883.6.3", "name": "ICD-10"},
    ]

    for test_code in test_codes:
        translation = translator._translate_term(
            code=test_code["code"], system=test_code["system"], original_display=None
        )
        if translation:
            print(
                f"✅ {test_code['name']} {test_code['code']}: {translation['display']}"
            )
            print(f"   Source: {translation.get('source', 'Unknown')}")
        else:
            print(f"❌ {test_code['name']} {test_code['code']}: No translation found")

    # Test enhanced clinical codes extraction
    print("\n--- Testing Enhanced Clinical Codes Extraction ---")
    sample_section = {
        "title": "Allergies and adverse reactions",
        "section_code": "48765-2",
        "entries": [
            {
                "code": {
                    "code": "232353008",
                    "codeSystem": "2.16.840.1.113883.6.96",
                    "displayName": "Nuts allergy",
                }
            }
        ],
        "content": {
            "original": "Patient has known allergy to nuts (SNOMED: 232353008)"
        },
    }

    clinical_codes = renderer._extract_clinical_codes(sample_section)
    print(f"Extracted codes: {clinical_codes}")
    print(f"Formatted display: {clinical_codes.get('formatted_display', 'None')}")

    # Test complete section rendering
    print("\n--- Testing Complete Section Rendering ---")
    rendered_section = renderer.render_section(sample_section)
    print(f"Rendered section keys: {list(rendered_section.keys())}")
    if rendered_section.get("clinical_codes"):
        codes = rendered_section["clinical_codes"]
        print(f"Clinical codes found: {codes.get('formatted_display', 'None')}")

    print("\n=== Terminology Integration Test Complete ===")


if __name__ == "__main__":
    test_terminology_lookup()
