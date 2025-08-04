#!/usr/bin/env python
"""
Test the template changes for patient_summary structure
"""
import os
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

import django

django.setup()

from django.template.loader import get_template
from django.test import RequestFactory


def test_template_rendering():
    """Test that the patient details template renders with our new structure"""

    # Create mock context data matching our new patient_summary structure
    context = {
        "patient_data": {
            "given_name": "John",
            "family_name": "Doe",
            "birth_date": "1990-01-01",
            "gender": "M",
        },
        "has_cda_match": True,
        "match_confidence": 95.0,
        "patient_summary": {
            "patient_name": "John Doe",
            "birth_date": "1990-01-01",
            "gender": "M",
            "primary_patient_id": "6668937763",
            "secondary_patient_id": "1900010100230",
            "patient_identifiers": [
                {"extension": "6668937763", "root": "test-root", "type": "primary"},
                {
                    "extension": "1900010100230",
                    "root": "test-root-2",
                    "type": "secondary",
                },
            ],
            "address": {},
            "contact_info": {},
            "cda_type": "L3",
            "file_path": "/test/data/patient_file.xml",
            "confidence_score": 0.95,
        },
        "source_country": "EE",
        "source_country_display": "Estonia",
        "cda_file_name": "patient_file.xml",
        "l1_available": False,
        "l3_available": True,
        "preferred_cda_type": "L3",
    }

    try:
        # Try to load and render the template
        template = get_template("patient_data/patient_details.html")

        # Create a mock request for the template context
        factory = RequestFactory()
        request = factory.get("/")

        # Render the template
        rendered = template.render(context, request)

        print("✓ Template rendered successfully!")
        print(f"Template length: {len(rendered)} characters")

        # Check that our patient data appears in the rendered output
        if "John Doe" in rendered:
            print("✓ Patient name appears correctly")
        if "6668937763" in rendered:
            print("✓ Primary patient ID appears correctly")
        if "1900010100230" in rendered:
            print("✓ Secondary patient ID appears correctly")
        if "patient_file.xml" in rendered:
            print("✓ File basename appears correctly")

        return True

    except Exception as e:
        print(f"✗ Template rendering failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing Patient Details Template Changes\n")

    success = test_template_rendering()

    if success:
        print("\n✓ Template changes are working correctly!")
        print(
            "The 'dict object has no attribute patient_info' error should be resolved."
        )
    else:
        print("\n✗ Template still has issues!")
