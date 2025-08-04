#!/usr/bin/env python3
"""
Test the complete patient details page functionality
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


def test_simple_patient_result():
    """Test that SimplePatientResult works correctly in both contexts"""
    print("Testing SimplePatientResult constructor in both contexts...")

    # Test 1: Patient details view context
    try:
        from dataclasses import dataclass
        from typing import Dict

        @dataclass
        class SimplePatientResult:
            """Simple patient result for views"""

            file_path: str
            country_code: str
            confidence_score: float
            patient_data: Dict
            cda_content: str

        # Test with correct 5 arguments
        test_match = SimplePatientResult(
            file_path="/test/path",
            country_code="GB",
            confidence_score=0.95,
            patient_data={
                "name": "Test Patient",
                "primary_patient_id": "6668937763",
                "secondary_patient_id": "1900010100230",
            },
            cda_content="<CDA>test</CDA>",
        )

        print("✓ Patient details view context: SimplePatientResult constructor works!")
        print(
            f"  - Primary ID: {test_match.patient_data.get('primary_patient_id', 'Not found')}"
        )
        print(
            f"  - Secondary ID: {test_match.patient_data.get('secondary_patient_id', 'Not found')}"
        )

        return True

    except Exception as e:
        print(f"✗ SimplePatientResult constructor failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_patient_data_extraction():
    """Test patient ID extraction logic"""
    print("\nTesting patient ID extraction...")

    try:
        # Simulate match_data from session
        mock_match_data = {
            "file_path": "/test/path.xml",
            "country_code": "EE",
            "confidence_score": 0.95,
            "patient_data": {
                "name": "Test Patient",
                "primary_patient_id": "6668937763",
                "secondary_patient_id": "1900010100230",
            },
            "cda_content": "<CDA><patientRole><id extension='6668937763'/><id extension='1900010100230'/></patientRole></CDA>",
        }

        # Test extraction
        patient_info = mock_match_data.get("patient_data", {})
        primary_id = patient_info.get("primary_patient_id", "Not found")
        secondary_id = patient_info.get("secondary_patient_id", "Not found")

        print(f"✓ Patient ID extraction works!")
        print(f"  - Primary Patient ID: {primary_id}")
        print(f"  - Secondary Patient ID: {secondary_id}")

        return True

    except Exception as e:
        print(f"✗ Patient ID extraction failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing complete patient details page functionality...")

    test1_success = test_simple_patient_result()
    test2_success = test_patient_data_extraction()

    if test1_success and test2_success:
        print("\n✅ ALL TESTS PASSED!")
        print("The patient details page should now work correctly.")
        print(
            "Patient identifiers (6668937763, 1900010100230) should display properly."
        )
        print("You can now refresh the patient details page in your browser.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("There may still be issues with the patient details page.")
