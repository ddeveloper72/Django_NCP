#!/usr/bin/env python
"""
Test Administrative Data Extraction
Tests the CDAAdministrativeExtractor with Malta CDA document
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(".")

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.cda_administrative_extractor import (
    CDAAdministrativeExtractor,
)


def test_administrative_extraction():
    """Test administrative data extraction"""
    print("=== ADMINISTRATIVE DATA EXTRACTION TEST ===")

    # Initialize extractor
    extractor = CDAAdministrativeExtractor()

    # Test with Malta CDA document
    cda_file = "test_data/eu_member_states/MT/Mario_Borg_9999002M.xml"

    if not os.path.exists(cda_file):
        print(f"ERROR: Test file not found: {cda_file}")
        return

    try:
        # Read the CDA file
        with open(cda_file, "r", encoding="utf-8") as f:
            cda_content = f.read()

        print(f"Reading CDA file: {cda_file}")
        print(f"CDA content length: {len(cda_content)} characters")

        # Extract administrative data
        admin_data = extractor.extract_administrative_data(cda_content)

        # Display results
        print("\n--- EXTRACTION RESULTS ---")
        print(
            f"Patient Contact Addresses: {len(admin_data.patient_contact_info.addresses)}"
        )
        print(
            f"Patient Contact Telecoms: {len(admin_data.patient_contact_info.telecoms)}"
        )
        print(
            f"Author HCP Name: '{admin_data.author_hcp.given_name}' '{admin_data.author_hcp.family_name}'"
        )
        print(f"Author Organization: '{admin_data.author_hcp.organization.name}'")
        print(
            f"Legal Authenticator: '{admin_data.legal_authenticator.given_name}' '{admin_data.legal_authenticator.family_name}'"
        )
        print(f"Custodian Organization: '{admin_data.custodian_organization.name}'")
        print(
            f"Guardian: '{admin_data.guardian.given_name}' '{admin_data.guardian.family_name}'"
        )
        print(f"Other Contacts: {len(admin_data.other_contacts)}")
        print(f"Preferred HCP: '{admin_data.preferred_hcp.name}'")

        if admin_data.patient_contact_info.addresses:
            print("\n--- Patient Addresses ---")
            for i, addr in enumerate(admin_data.patient_contact_info.addresses):
                print(f"  Address {i+1}: {addr}")

        if admin_data.patient_contact_info.telecoms:
            print("\n--- Patient Telecoms ---")
            for i, telecom in enumerate(admin_data.patient_contact_info.telecoms):
                print(f"  Telecom {i+1}: {telecom}")

        if admin_data.author_hcp.organization.addresses:
            print("\n--- Author Organization Addresses ---")
            for i, addr in enumerate(admin_data.author_hcp.organization.addresses):
                print(f"  Address {i+1}: {addr}")

        # Check if we have any meaningful data
        has_data = (
            admin_data.patient_contact_info.addresses
            or admin_data.patient_contact_info.telecoms
            or admin_data.author_hcp.family_name
            or admin_data.author_hcp.organization.name
            or admin_data.legal_authenticator.family_name
            or admin_data.custodian_organization.name
        )

        print(f"\n--- SUMMARY ---")
        print(f"Has administrative data: {has_data}")

        if has_data:
            print("✅ Administrative data extraction successful!")
        else:
            print("⚠️  No administrative data found - may need to debug XML parsing")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_administrative_extraction()
