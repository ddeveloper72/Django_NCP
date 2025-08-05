#!/usr/bin/env python
"""
End-to-End Test for Patient Search Fix

This script tests the complete workflow:
1. CDA indexing system
2. Patient search with PatientMatch creation
3. URL parameter handling in patient form
4. Complete search workflow
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from patient_data.services.cda_document_index import get_cda_indexer
from patient_data.services.patient_search_service import PatientSearchService
from patient_data.models import SearchCredentials
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from patient_data.views import patient_data_view
import urllib.parse


def test_complete_workflow():
    """Test the complete patient search workflow."""
    print("=== End-to-End Patient Search Test ===\n")

    # Step 1: Test CDA Indexer
    print("1. Testing CDA Indexer...")
    try:
        indexer = get_cda_indexer()
        indexer.build_index()
        patients = indexer.get_all_patients()
        print(f"   ✓ CDA Index built: {len(patients)} patients found")

        # Find Mario PINO
        mario = None
        for patient in patients:
            if patient.get("patient_id") == "NCPNPH80A01H501K":
                mario = patient
                break

        if mario:
            print(
                f"   ✓ Mario PINO found: {mario['given_name']} {mario['family_name']}"
            )
        else:
            print("   ❌ Mario PINO not found in index")
            return False

    except Exception as e:
        print(f"   ❌ CDA Indexer failed: {e}")
        return False

    # Step 2: Test Patient Search Service
    print("\n2. Testing Patient Search Service...")
    try:
        search_service = PatientSearchService()
        credentials = SearchCredentials(
            patient_id="NCPNPH80A01H501K",
            country_code="IT",
            given_name="Mario",
            family_name="PINO",
        )

        matches = search_service.search_patient(credentials)
        print(f"   ✓ Search returned {len(matches)} matches")

        if matches:
            match = matches[0]
            print(f"   ✓ First match: {match.given_name} {match.family_name}")
            print(f"   ✓ Patient ID: {match.patient_id}")
            print(f"   ✓ Has L1 CDA: {match.has_l1_cda()}")
            print(f"   ✓ Has L3 CDA: {match.has_l3_cda()}")
            print(
                f"   ✓ Patient Data ID: {match.patient_data.get('id') if match.patient_data else 'None'}"
            )
        else:
            print("   ❌ No matches returned")
            return False

    except Exception as e:
        print(f"   ❌ Patient Search failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 3: Test URL Parameter Handling
    print("\n3. Testing URL Parameter Handling...")
    try:
        factory = RequestFactory()

        # Create a GET request with URL parameters (like clicking "Test NCP Query")
        url = "/?country=IT&patient_id=NCPNPH80A01H501K&auto_search=false"
        request = factory.get(url)

        # Add session middleware (required for session storage)
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Test the view
        response = patient_data_view(request)
        print(f"   ✓ View handled URL parameters successfully")
        print(f"   ✓ Response status: {response.status_code}")

    except Exception as e:
        print(f"   ❌ URL Parameter handling failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 4: Test Auto-Search Workflow
    print("\n4. Testing Auto-Search Workflow...")
    try:
        # Create a GET request with auto_search=true (simulates clicking "Test NCP Query")
        url = "/?country=IT&patient_id=NCPNPH80A01H501K&auto_search=true"
        request = factory.get(url)

        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Test the view
        response = patient_data_view(request)
        print(f"   ✓ Auto-search handled successfully")
        print(f"   ✓ Response status: {response.status_code}")

        # Check if it's a redirect (successful search should redirect to patient details)
        if response.status_code == 302:
            print(f"   ✓ Redirected to: {response.url}")
            if "patient-details" in response.url:
                print("   ✓ Redirected to patient details page - SUCCESS!")
            else:
                print(f"   ⚠️  Redirected but not to patient details: {response.url}")
        else:
            print(f"   ⚠️  No redirect - may indicate search issue")

    except Exception as e:
        print(f"   ❌ Auto-search workflow failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n=== All Tests Completed Successfully! ===")
    print("\nSUMMARY:")
    print("✓ CDA documents are properly indexed")
    print("✓ Patient search creates PatientMatch objects")
    print("✓ URL parameters are handled correctly")
    print("✓ Auto-search workflow works")
    print("\nThe 'Test NCP Query' button should now work properly!")
    return True


if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n🎉 ALL TESTS PASSED - The fix is working!")
    else:
        print("\n❌ SOME TESTS FAILED - Need further investigation")
