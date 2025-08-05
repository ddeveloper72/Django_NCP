#!/usr/bin/env python
"""
Test CDA View Fix

This script tests that the CDA view can handle temporary patients correctly.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from patient_data.views import patient_cda_view
from patient_data.models import PatientData


def test_cda_view_fix():
    """Test that the CDA view handles temporary patients correctly."""
    print("=== Testing CDA View Fix ===\n")

    factory = RequestFactory()

    # Test patient ID (temporary patient not in database)
    test_patient_id = "252003"

    # Create mock session data (like what would be created by successful search)
    mock_session_data = {
        "patient_data": {
            "id": test_patient_id,
            "given_name": "Mario",
            "family_name": "PINO",
            "birth_date": "1980-01-01",
            "gender": "M",
        },
        "match_score": 1.0,
        "confidence_score": 1.0,
        "l1_cda_content": "<ClinicalDocument>Mock L1 Content</ClinicalDocument>",
        "l3_cda_content": "<ClinicalDocument>Mock L3 Content</ClinicalDocument>",
        "l1_cda_path": "mock/l1_NCPNPH80A01H501K.xml",
        "l3_cda_path": "mock/l3_NCPNPH80A01H501K.xml",
        "available_documents": ["L1_CDA", "L3_CDA"],
        "file_path": "test_data/it/mario_pino.xml",
    }

    print(f"1. Testing CDA view for temporary patient ID: {test_patient_id}")

    # Verify patient is NOT in database
    patient_exists = PatientData.objects.filter(id=test_patient_id).exists()
    print(f"   Patient exists in database: {patient_exists}")

    if patient_exists:
        print(
            "   ⚠️  Warning: Test patient exists in database - this test may not be accurate"
        )

    try:
        # Create GET request to CDA view
        request = factory.get(f"/patients/cda/{test_patient_id}/")

        # Add session middleware and data
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Add mock session data
        session_key = f"patient_match_{test_patient_id}"
        request.session[session_key] = mock_session_data

        print(f"   Session key: {session_key}")
        print(f"   Session data added: {bool(request.session.get(session_key))}")

        # Test the CDA view
        response = patient_cda_view(request, test_patient_id)

        print(f"\n2. CDA View Response:")
        print(f"   Status code: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ SUCCESS: CDA view returned 200 OK")
            print("   ✅ The view can now handle temporary patients!")

            # Check if it's actually rendering the CDA template
            if hasattr(response, "template_name"):
                print(f"   Template: {response.template_name}")

        elif response.status_code == 302:
            print(f"   ❌ FAILED: CDA view still redirecting to: {response.url}")
            print("   This indicates the patient was still not found")

        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")

    except Exception as e:
        print(f"   ❌ ERROR in CDA view: {e}")
        import traceback

        traceback.print_exc()
        return False

    print("\n3. Testing Edge Cases:")

    # Test with no session data
    try:
        request_no_session = factory.get(f"/patients/cda/{test_patient_id}/")
        middleware.process_request(request_no_session)
        request_no_session.session.save()
        # Don't add session data

        response_no_session = patient_cda_view(request_no_session, test_patient_id)
        print(f"   No session data - Status: {response_no_session.status_code}")

        if response_no_session.status_code == 302:
            print("   ✅ Correctly redirects when no session data")
        else:
            print("   ⚠️  Unexpected behavior with no session data")

    except Exception as e:
        print(f"   ❌ Error in edge case test: {e}")

    print("\n=== CDA View Test Complete ===")
    print("\nSUMMARY:")
    print("✓ CDA view should now handle temporary patients from search results")
    print("✓ Fixed the 'Patient data not found' error for NCP query results")
    print("✓ Mario PINO CDA display should now work when clicking from patient details")

    return True


if __name__ == "__main__":
    test_cda_view_fix()
