#!/usr/bin/env python
"""
Test script to verify the patient search fix works correctly.
This tests the PatientMatch creation that was just fixed.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from patient_data.services.patient_search_service import PatientSearchService
from patient_data.models import SearchCredentials


def test_patient_search_fix():
    """Test that the patient search now creates PatientMatch objects correctly."""
    print("=== Testing Patient Search Fix ===\n")

    # Initialize the search service
    search_service = PatientSearchService()
    print("✓ Patient search service initialized")

    # Test with Mario PINO (known patient from test data)
    test_credentials = SearchCredentials(
        patient_id="NCPNPH80A01H501K",
        country_code="IT",
        given_name="Mario",
        family_name="PINO",
    )

    print(
        f"Testing search for: {test_credentials.given_name} {test_credentials.family_name}"
    )
    print(f"Patient ID: {test_credentials.patient_id}")
    print(f"Country: {test_credentials.country_code}\n")

    try:
        # Perform the search
        matches = search_service.search_patient(test_credentials)

        print(f"Search returned {len(matches)} matches")

        if matches:
            print("✓ SUCCESS: PatientMatch objects were created!")

            for i, match in enumerate(matches, 1):
                print(f"\nMatch {i}:")
                print(f"  - Patient ID: {match.patient_id}")
                print(f"  - Name: {match.given_name} {match.family_name}")
                print(f"  - Country: {match.country_code}")
                print(f"  - Match Score: {match.match_score}")
                print(f"  - Has L1 CDA: {match.has_l1_cda()}")
                print(f"  - Has L3 CDA: {match.has_l3_cda()}")
                print(f"  - Available Documents: {match.available_documents}")

                # Check if patient_data is populated
                if hasattr(match, "patient_data") and match.patient_data:
                    print(
                        f"  - Patient Data ID: {match.patient_data.get('id', 'Not set')}"
                    )
                    print(
                        f"  - Patient Data Name: {match.patient_data.get('name', 'Not set')}"
                    )

        else:
            print("❌ FAILED: No PatientMatch objects returned")
            print("This indicates the fix didn't work - matches list is empty")

    except Exception as e:
        print(f"❌ ERROR during search: {e}")
        import traceback

        traceback.print_exc()

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_patient_search_fix()
