#!/usr/bin/env python
"""
Simple test to check if CDA indexing system works.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from patient_data.services.cda_document_index import get_cda_indexer


def test_cda_indexer():
    """Test the CDA indexing system."""
    print("=== Testing CDA Indexer ===\n")

    try:
        # Get the indexer instance
        indexer = get_cda_indexer()
        print("✓ CDA indexer instance obtained")

        # Build the index
        print("Building CDA index...")
        indexer.build_index()
        print("✓ Index built successfully")

        # Get indexed patients
        patients = indexer.get_all_patients()
        print(f"✓ Found {len(patients)} patients in index")

        # Look for Mario PINO specifically
        mario_found = False
        for patient in patients:
            if patient.get("patient_id") == "NCPNPH80A01H501K":
                mario_found = True
                print("\n✓ Found Mario PINO:")
                print(f"  - ID: {patient.get('patient_id')}")
                print(
                    f"  - Name: {patient.get('given_name')} {patient.get('family_name')}"
                )
                print(f"  - Country: {patient.get('country_code')}")
                break

        if not mario_found:
            print("❌ Mario PINO not found in index")
            print("Available patients:")
            for patient in patients[:5]:  # Show first 5
                print(
                    f"  - {patient.get('patient_id')}: {patient.get('given_name')} {patient.get('family_name')}"
                )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_cda_indexer()
