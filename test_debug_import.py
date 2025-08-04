#!/usr/bin/env python3
"""
Test script to verify PatientSearchResult constructor fix
"""
import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

# Clear module cache to ensure fresh import
import importlib

if "patient_data.services" in sys.modules:
    importlib.reload(sys.modules["patient_data.services"])


# Test the PatientSearchResult constructor
def test_patient_search_result_constructor():
    try:
        # Import directly from services.py file
        import patient_data.services as patient_services

        print(f"Available classes in patient_services: {dir(patient_services)}")

        if not hasattr(patient_services, "PatientSearchResult"):
            print("✗ PatientSearchResult class not found in patient_services module")
            return False

        PatientSearchResult = patient_services.PatientSearchResult

        # Test constructor with 5 arguments as defined in services.py
        test_match = PatientSearchResult(
            file_path="/test/path",
            country_code="GB",
            confidence_score=0.95,
            patient_data={"name": "Test Patient"},
            cda_content="<CDA>test</CDA>",
        )

        print("✓ PatientSearchResult constructor works correctly!")
        print(f"  - file_path: {test_match.file_path}")
        print(f"  - country_code: {test_match.country_code}")
        print(f"  - confidence_score: {test_match.confidence_score}")
        print(f"  - patient_data: {test_match.patient_data}")
        print(
            f"  - cda_content length: {len(test_match.cda_content) if test_match.cda_content else 0}"
        )

        return True

    except Exception as e:
        print(f"✗ PatientSearchResult constructor failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing PatientSearchResult constructor fix...")
    success = test_patient_search_result_constructor()
    if success:
        print(
            "\n✓ Fix successful! The PatientSearchResult constructor should now work in the application."
        )
    else:
        print("\n✗ Fix failed! There may still be import conflicts.")
