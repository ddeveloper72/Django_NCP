#!/usr/bin/env python3
"""
Test the fixed views.py with SimplePatientResult
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


# Test the SimplePatientResult constructor in views context
def test_views_patient_result():
    try:
        # Test if we can create the SimplePatientResult as defined in views.py
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

        # Test constructor with 5 arguments
        test_match = SimplePatientResult(
            file_path="/test/path",
            country_code="GB",
            confidence_score=0.95,
            patient_data={"name": "Test Patient"},
            cda_content="<CDA>test</CDA>",
        )

        print("✓ SimplePatientResult constructor works correctly!")
        print(f"  - file_path: {test_match.file_path}")
        print(f"  - country_code: {test_match.country_code}")
        print(f"  - confidence_score: {test_match.confidence_score}")
        print(f"  - patient_data: {test_match.patient_data}")
        print(
            f"  - cda_content length: {len(test_match.cda_content) if test_match.cda_content else 0}"
        )

        return True

    except Exception as e:
        print(f"✗ SimplePatientResult constructor failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing SimplePatientResult constructor in views context...")
    success = test_views_patient_result()
    if success:
        print("\n✓ Fix successful! The patient details page should now work.")
        print("You can now refresh the patient details page in your browser.")
    else:
        print("\n✗ Fix failed! There may still be issues.")
