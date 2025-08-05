#!/usr/bin/env python
"""
Test CDA Search Integration
Tests that search results are properly passed to translation services for clinical sections
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
    PatientMatch,
)
from patient_data.services.cda_translation_manager import CDATranslationManager
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_search_to_translation_integration():
    """Test that search results provide proper context to translation service"""
    print("\n=== Testing Search Result to Translation Service Integration ===")

    # Initialize services
    search_service = EUPatientSearchService()
    translation_manager = CDATranslationManager(target_language="en")

    # Test with a specific patient ID from IT (Mario PINO)
    test_credentials = PatientCredentials(country_code="IT", patient_id="597948")

    print(
        f"Searching for patient: {test_credentials.patient_id} in {test_credentials.country_code}"
    )

    # Get search results
    search_results = search_service.search_patient(test_credentials)

    if not search_results:
        print("❌ No search results found")
        return False

    print(f"✅ Found {len(search_results)} search result(s)")

    # Take the first result
    search_result = search_results[0]
    print(f"Search result: {search_result.given_name} {search_result.family_name}")
    print(f"Country: {search_result.country_code}")
    print(f"Has L1 CDA: {search_result.has_l1_cda()}")
    print(f"Has L3 CDA: {search_result.has_l3_cda()}")

    # Get the rendering CDA content and type
    cda_content, cda_type = search_result.get_rendering_cda()

    if not cda_content:
        print("❌ No CDA content available from search result")
        return False

    print(f"✅ Got {cda_type} CDA content ({len(cda_content)} characters)")

    # Determine source language
    source_language = "it"  # Italian for Mario PINO

    # Test translation manager with the CDA content
    print(f"\nTesting translation manager with {cda_type} CDA...")
    try:
        translation_result = translation_manager.process_cda_for_viewer(
            cda_content, source_language
        )

        if translation_result.get("success"):
            clinical_sections = translation_result.get("clinical_sections", [])
            print(f"✅ Translation manager processed successfully")
            print(f"✅ Found {len(clinical_sections)} clinical sections")

            # Show section details
            for i, section in enumerate(clinical_sections[:3]):  # Show first 3 sections
                print(f"  Section {i+1}: {section.get('title', 'Unknown')}")
                print(
                    f"    - Has coded elements: {section.get('has_coded_elements', False)}"
                )
                print(f"    - Medical terms: {section.get('medical_terms_count', 0)}")
                print(
                    f"    - Original content length: {len(section.get('original_content', ''))}"
                )

            return len(clinical_sections) > 0

        else:
            error_msg = translation_result.get("error", "Unknown error")
            print(f"❌ Translation manager failed: {error_msg}")
            return False

    except Exception as e:
        print(f"❌ Exception in translation manager: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_session_data_reconstruction():
    """Test that we can reconstruct PatientMatch from session-like data"""
    print("\n=== Testing Session Data Reconstruction ===")

    # Simulate session data structure
    mock_session_data = {
        "country_code": "IT",
        "confidence_score": 0.95,
        "file_path": "test_data/eu_member_states/IT/Mario_PINO_597948.xml",
        "l1_cda_content": None,
        "l3_cda_content": "<html><body>Mock L3 CDA content...</body></html>",
        "l1_cda_path": None,
        "l3_cda_path": "test_data/eu_member_states/IT/Mario_PINO_597948.xml",
        "cda_content": "<html><body>Mock L3 CDA content...</body></html>",
        "patient_data": {
            "id": "597948",
            "given_name": "Mario",
            "family_name": "PINO",
            "birth_date": "1970-01-01",
            "gender": "M",
        },
    }

    # Reconstruct PatientMatch from session data
    patient_info = mock_session_data.get("patient_data", {})
    search_result = PatientMatch(
        patient_id="597948",
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
        f"✅ Reconstructed PatientMatch: {search_result.given_name} {search_result.family_name}"
    )
    print(f"✅ Country: {search_result.country_code}")
    print(f"✅ Has L3 CDA: {search_result.has_l3_cda()}")

    cda_content, cda_type = search_result.get_rendering_cda()
    print(
        f"✅ Rendering CDA: {cda_type} ({len(cda_content) if cda_content else 0} chars)"
    )

    return True


if __name__ == "__main__":
    print("Testing CDA Search Integration...")

    success1 = test_search_to_translation_integration()
    success2 = test_session_data_reconstruction()

    if success1 and success2:
        print(
            "\n🎉 All tests passed! Search results are properly integrated with translation services."
        )
    else:
        print(
            "\n❌ Some tests failed. Check the integration between search and translation services."
        )
