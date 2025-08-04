#!/usr/bin/env python3
"""
Test script to verify PatientMatch constructor fix
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


# Test the PatientMatch constructor
def test_patient_match_constructor():
    try:
        # Import directly from the main services module
        from patient_data import services as patient_services

        PatientMatch = patient_services.PatientMatch

        # Test constructor with 5 arguments as defined in services.py
        test_match = PatientMatch(
            file_path="/test/path",
            country_code="GB",
            confidence_score=0.95,
            patient_data={"name": "Test Patient"},
            cda_content="<CDA>test</CDA>",
        )

        print("✓ PatientMatch constructor works correctly!")
        print(f"  - file_path: {test_match.file_path}")
        print(f"  - country_code: {test_match.country_code}")
        print(f"  - confidence_score: {test_match.confidence_score}")
        print(f"  - patient_data: {test_match.patient_data}")
        print(
            f"  - cda_content length: {len(test_match.cda_content) if test_match.cda_content else 0}"
        )

        return True

    except Exception as e:
        print(f"✗ PatientMatch constructor failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing PatientMatch constructor fix...")
    success = test_patient_match_constructor()
    if success:
        print(
            "\n✓ Fix successful! The PatientMatch constructor should now work in the application."
        )
    else:
        print("\n✗ Fix failed! There may still be import conflicts.")
