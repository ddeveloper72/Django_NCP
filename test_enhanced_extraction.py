#!/usr/bin/env python3
"""
Test the enhanced patient identifier extraction function
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.views import extract_patient_identifiers_from_cda


def test_enhanced_extraction():
    """Test the enhanced extraction function"""

    # Read the sample CDA
    with open("patient_data/test_data/sample_cda_document.xml", "r") as f:
        cda_content = f.read()

    print("Testing enhanced patient identifier extraction function...")

    try:
        identifiers = extract_patient_identifiers_from_cda(cda_content)

        print(f"Function returned {len(identifiers)} identifiers:")

        for i, identifier in enumerate(identifiers, 1):
            print(f"  {i}. Extension: {identifier.get('extension', 'N/A')}")
            print(f"     Root: {identifier.get('root', 'N/A')}")
            print()
    except Exception as e:
        print(f"Error calling function: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_enhanced_extraction()
