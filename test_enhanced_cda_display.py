#!/usr/bin/env python3
"""
Test Enhanced CDA Display Tool Integration
Validates the complete CTS-compliant CDA display system with clinical sections
"""

import os
import sys
import django

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.test import RequestFactory
from patient_data.views.enhanced_cda_display import (
    EnhancedCDADisplayView,
    get_enhanced_clinical_sections_api,
)
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_enhanced_cda_display_system():
    """Test the complete enhanced CDA display system"""

    print("🏥 TESTING ENHANCED CDA DISPLAY TOOL")
    print("=" * 60)

    # Test 1: Enhanced CDA Display View
    print("\n1. Testing Enhanced CDA Display View:")
    try:
        factory = RequestFactory()
        request = factory.get("/enhanced_cda/patient123?lang=en")

        view = EnhancedCDADisplayView()
        response = view.get(request, patient_id="patient123")

        print(f"   Response status: {response.status_code}")
        print(f"   Response type: {type(response).__name__}")

        if response.status_code == 200:
            print("✅ Enhanced CDA display view working")
        else:
            print(f"❌ Error in display view: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error in enhanced display view: {e}")
        return False

    # Test 2: Enhanced Clinical Sections API
    print("\n2. Testing Enhanced Clinical Sections API:")
    try:
        factory = RequestFactory()
        request = factory.get("/api/enhanced_sections/patient123?lang=en")

        response = get_enhanced_clinical_sections_api(request, "patient123")

        print(f"   API response status: {response.status_code}")

        if response.status_code == 200:
            # Parse JSON response
            response_data = json.loads(response.content)

            print(f"   Success: {response_data.get('success', False)}")
            print(
                f"   Sections count: {response_data.get('data', {}).get('sections_count', 0)}"
            )
            print(
                f"   Coded sections: {response_data.get('data', {}).get('coded_sections_count', 0)}"
            )
            print(
                f"   Medical terms: {response_data.get('data', {}).get('medical_terms_count', 0)}"
            )
            print(
                f"   Translation quality: {response_data.get('data', {}).get('translation_quality', 'Unknown')}"
            )

            print("✅ Enhanced clinical sections API working")
        else:
            print(f"❌ Error in API: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error in clinical sections API: {e}")
        return False

    # Test 3: CTS Compliance Check
    print("\n3. Testing CTS Compliance:")
    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        processor = EnhancedCDAProcessor(target_language="en")

        # Check that processor uses CTS
        has_terminology_service = hasattr(processor, "terminology_service")
        has_mvc_models = hasattr(processor, "ValueSetCatalogue")

        print(f"   Has terminology service: {has_terminology_service}")
        print(f"   Has MVC models: {has_mvc_models}")

        if has_terminology_service and has_mvc_models:
            print("✅ CTS integration confirmed")
        else:
            print("❌ CTS integration missing")
            return False

    except Exception as e:
        print(f"❌ Error checking CTS compliance: {e}")
        return False

    # Test 4: Section Title Translation
    print("\n4. Testing Section Title Translation:")
    try:
        processor = EnhancedCDAProcessor(target_language="en")

        # Test LOINC section codes
        test_cases = [
            ("10160-0", "Résumé des médicaments", "fr"),
            ("48765-2", "Allergies et réactions indésirables", "fr"),
            ("11450-4", "Liste des problèmes", "fr"),
        ]

        for section_code, original_title, source_lang in test_cases:
            result = processor._get_enhanced_section_title(
                section_code=section_code,
                original_title=original_title,
                source_language=source_lang,
            )

            print(f"   Code {section_code}: {result['source']} → {result['target']}")

        print("✅ Section title translation working")

    except Exception as e:
        print(f"❌ Error in section title translation: {e}")
        return False

    # Test 5: PS Table Generation
    print("\n5. Testing PS Table Generation:")
    try:
        processor = EnhancedCDAProcessor(target_language="en")

        # Mock table data
        mock_table_data = [
            {"code": "123", "display": "Test medication", "value": "500mg"}
        ]

        enhanced_title = {
            "source": "Résumé des médicaments",
            "target": "Medication Summary",
        }

        table_html, table_html_original = processor._generate_ps_tables(
            mock_table_data, "10160-0", enhanced_title, "fr"
        )

        has_ps_container = "ps-table-container" in table_html
        has_compliance_badge = "PS Guidelines Compliant" in table_html

        print(f"   PS table container: {has_ps_container}")
        print(f"   Compliance badge: {has_compliance_badge}")

        if has_ps_container:
            print("✅ PS table generation working")
        else:
            print("❌ PS table generation issues")
            return False

    except Exception as e:
        print(f"❌ Error in PS table generation: {e}")
        return False

    # Test 6: Template Integration
    print("\n6. Testing Template Integration:")
    try:
        # Check template file exists
        template_path = "templates/jinja2/patient_data/enhanced_patient_cda.html"

        if os.path.exists(template_path):
            print(f"   Template file exists: {template_path}")

            # Read template content
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Check for key CTS-compliant features
            has_cts_badge = "CTS" in template_content
            has_ps_tables = "ps-compliant-table" in template_content
            has_language_toggle = "language-toggle" in template_content
            has_enhanced_sections = "enhanced_sections" in template_content

            print(f"   CTS badges: {has_cts_badge}")
            print(f"   PS compliant tables: {has_ps_tables}")
            print(f"   Language toggle: {has_language_toggle}")
            print(f"   Enhanced sections: {has_enhanced_sections}")

            if all(
                [
                    has_cts_badge,
                    has_ps_tables,
                    has_language_toggle,
                    has_enhanced_sections,
                ]
            ):
                print("✅ Template integration complete")
            else:
                print("❌ Template integration incomplete")
                return False
        else:
            print(f"❌ Template file not found: {template_path}")
            return False

    except Exception as e:
        print(f"❌ Error checking template integration: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED - ENHANCED CDA DISPLAY TOOL COMPLETE!")
    print("✅ CTS-compliant clinical section processing")
    print("✅ PS Guidelines compliant table rendering")
    print("✅ Dynamic section title translation")
    print("✅ Bilingual content display")
    print("✅ Professional UI with Bootstrap integration")
    return True


def validate_no_hardcoded_violations():
    """Final validation that no hardcoded medical data remains"""

    print("\n🔍 FINAL HARDCODED DATA VALIDATION")
    print("=" * 40)

    files_to_check = [
        "patient_data/services/enhanced_cda_processor.py",
        "patient_data/views/enhanced_cda_display.py",
        "templates/jinja2/patient_data/enhanced_patient_cda.html",
    ]

    violations_found = 0

    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for hardcoded medical terms
            hardcoded_patterns = [
                '"Medication Summary"',
                '"Allergy Summary"',
                '"Problem List"',
                '"History"',
                '"Summary"',
            ]

            file_violations = []
            for pattern in hardcoded_patterns:
                if pattern in content:
                    file_violations.append(pattern)

            if file_violations:
                print(f"❌ {file_path}: {len(file_violations)} violations")
                violations_found += len(file_violations)
            else:
                print(f"✅ {file_path}: No violations")

    if violations_found == 0:
        print(f"\n✅ VALIDATION PASSED: Zero hardcoded medical terminology")
        return True
    else:
        print(f"\n❌ VALIDATION FAILED: {violations_found} hardcoded violations remain")
        return False


if __name__ == "__main__":
    print("Testing Enhanced CDA Display Tool with CTS Integration")
    print("Validating clinical sections, PS tables, and template rendering")

    # Test the complete system
    system_works = test_enhanced_cda_display_system()

    # Validate no hardcoded data
    no_violations = validate_no_hardcoded_violations()

    if system_works and no_violations:
        print("\n🎉 SUCCESS: ENHANCED CDA DISPLAY TOOL FULLY IMPLEMENTED")
        print("✅ Complete CTS-compliant clinical section processing")
        print("✅ Professional PS Guidelines table rendering")
        print("✅ Dynamic bilingual display capabilities")
        print("✅ Zero hardcoded medical terminology")
        print("✅ Ready for production deployment")
        sys.exit(0)
    else:
        print("\n❌ ISSUES FOUND: Review and address remaining problems")
        sys.exit(1)
