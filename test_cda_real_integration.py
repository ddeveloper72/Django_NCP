#!/usr/bin/env python
"""
Simple test for CDA search integration with actual test data
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.patient_search_service import (
    EUPatientSearchService,
    PatientCredentials,
)
from patient_data.services.cda_translation_manager import CDATranslationManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_actual_file_processing():
    """Test with actual L3 CDA file from test data"""
    print("\n=== Testing with Actual Test Data ===")

    # Find an actual L3 CDA file
    test_file = "test_data/eu_member_states/IT/2025-03-28T13-29-58.949209Z_CDA_EHDSI---PIVOT-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False

    print(f"✅ Found test file: {test_file}")

    # Read the file content
    try:
        with open(test_file, "r", encoding="utf-8") as f:
            cda_content = f.read()
        print(f"✅ Read CDA content ({len(cda_content)} characters)")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    # Test translation manager
    translation_manager = CDATranslationManager(target_language="en")
    source_language = "it"  # Italian

    print(f"\nTesting translation manager...")
    try:
        translation_result = translation_manager.process_cda_for_viewer(
            cda_content, source_language
        )

        if translation_result.get("success"):
            clinical_sections = translation_result.get("clinical_sections", [])
            print(f"✅ Translation successful!")
            print(f"✅ Found {len(clinical_sections)} clinical sections")

            if len(clinical_sections) > 0:
                print("\nSection details:")
                for i, section in enumerate(clinical_sections[:3]):
                    title = section.get("title", "Unknown")
                    has_coded = section.get("has_coded_elements", False)
                    terms_count = section.get("medical_terms_count", 0)
                    content_len = len(section.get("original_content", ""))

                    print(f"  {i+1}. {title}")
                    print(f"     - Coded elements: {has_coded}")
                    print(f"     - Medical terms: {terms_count}")
                    print(f"     - Content length: {content_len}")

                return True
            else:
                print("⚠️ No clinical sections found")
                return False

        else:
            error_msg = translation_result.get("error", "Unknown error")
            print(f"❌ Translation failed: {error_msg}")
            return False

    except Exception as e:
        print(f"❌ Exception in translation: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_view_context_simulation():
    """Simulate what happens in the CDA view"""
    print("\n=== Simulating CDA View Context ===")

    # Mock session data like what would be stored
    mock_session_data = {
        "country_code": "IT",
        "confidence_score": 0.95,
        "file_path": "test_data/eu_member_states/IT/2025-03-28T13-29-58.949209Z_CDA_EHDSI---PIVOT-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml",
        "l1_cda_content": None,
        "l3_cda_content": None,  # Will be loaded
        "l1_cda_path": None,
        "l3_cda_path": "test_data/eu_member_states/IT/2025-03-28T13-29-58.949209Z_CDA_EHDSI---PIVOT-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml",
        "cda_content": None,  # Will be loaded
        "patient_data": {
            "id": "331404",
            "given_name": "Test",
            "family_name": "Patient",
            "birth_date": "1970-01-01",
            "gender": "M",
        },
    }

    # Load the actual file content (simulating what search service would do)
    test_file = mock_session_data["l3_cda_path"]
    if os.path.exists(test_file):
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        mock_session_data["l3_cda_content"] = content
        mock_session_data["cda_content"] = content
        print(f"✅ Loaded L3 CDA content ({len(content)} chars)")
    else:
        print(f"❌ Cannot load test file: {test_file}")
        return False

    # Now simulate the view's processing
    from patient_data.services.patient_search_service import PatientMatch

    patient_info = mock_session_data.get("patient_data", {})
    search_result = PatientMatch(
        patient_id="331404",
        given_name=patient_info.get("given_name", "Unknown"),
        family_name=patient_info.get("family_name", "Unknown"),
        birth_date=patient_info.get("birth_date", ""),
        gender=patient_info.get("gender", ""),
        country_code=mock_session_data.get("country_code", ""),
        confidence_score=mock_session_data.get("confidence_score", 0.95),
        file_path=mock_session_data.get("file_path"),
        l1_cda_content=mock_session_data.get("l1_cda_content"),
        l3_cda_content=mock_session_data.get("l3_cda_content"),
        l1_cda_path=mock_session_data.get("l1_cda_path"),
        l3_cda_path=mock_session_data.get("l3_cda_path"),
        cda_content=mock_session_data.get("cda_content"),
        patient_data=patient_info,
        preferred_cda_type="L3",
    )

    print(
        f"✅ Created PatientMatch for {search_result.given_name} {search_result.family_name}"
    )

    # Get rendering CDA
    cda_content, cda_type = search_result.get_rendering_cda()
    print(f"✅ Got {cda_type} CDA for rendering ({len(cda_content)} chars)")

    # Process with translation manager
    translation_manager = CDATranslationManager(target_language="en")
    source_language = "it"

    try:
        result = translation_manager.process_cda_for_viewer(
            cda_content, source_language
        )

        if result.get("success"):
            sections = result.get("clinical_sections", [])
            print(f"✅ View processing would show {len(sections)} clinical sections")
            return len(sections) > 0
        else:
            print(f"❌ View processing failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ View processing exception: {e}")
        return False


if __name__ == "__main__":
    print("Testing CDA Search Integration with Real Data...")

    test1 = test_actual_file_processing()
    test2 = test_view_context_simulation()

    if test1 and test2:
        print(
            "\n🎉 Integration tests passed! Clinical sections should now display properly."
        )
    else:
        print(
            "\n❌ Integration tests failed. Check the translation service implementation."
        )
