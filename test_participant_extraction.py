#!/usr/bin/env python3
"""
Test script to verify participant extraction from Latvia CDA document
Tests extraction of emergency contacts, next of kin, and primary care providers
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.cda_administrative_extractor import (
    CDAAdministrativeExtractor,
)


def test_participant_extraction():
    """Test participant extraction with Latvia CDA document"""
    print("🔍 Testing Participant Extraction from Latvia CDA Document")
    print("=" * 60)

    # Read the Latvia L3 CDA document
    cda_file_path = "test_data/eu_member_states/LV/2025-04-01T11-25-07.284098Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    try:
        with open(cda_file_path, "r", encoding="utf-8") as file:
            cda_content = file.read()

        print(f"✅ Successfully loaded CDA document: {cda_file_path}")
        print(f"📄 Document size: {len(cda_content)} characters")

    except FileNotFoundError:
        print(f"❌ ERROR: Could not find CDA file: {cda_file_path}")
        return
    except Exception as e:
        print(f"❌ ERROR loading CDA file: {e}")
        return

    # Extract administrative data including participants
    extractor = CDAAdministrativeExtractor()

    try:
        admin_data = extractor.extract_administrative_data(cda_content)
        print("✅ Administrative data extraction completed")

    except Exception as e:
        print(f"❌ ERROR during extraction: {e}")
        return

    # Display participant information
    print("\n📋 PARTICIPANT EXTRACTION RESULTS")
    print("=" * 50)

    if admin_data.other_contacts:
        print(f"🔗 Found {len(admin_data.other_contacts)} participants:")

        for i, contact in enumerate(admin_data.other_contacts, 1):
            print(f"\n{i}. {contact.role}")
            print(f"   Name: {contact.given_name} {contact.family_name}")

            if contact.specialty:
                print(f"   Period: {contact.specialty}")

            if contact.contact_info.addresses:
                for addr in contact.contact_info.addresses:
                    address_parts = []
                    if "street" in addr:
                        address_parts.append(addr["street"])
                    if "city" in addr:
                        address_parts.append(addr["city"])
                    if "postalCode" in addr:
                        address_parts.append(addr["postalCode"])
                    if "country" in addr:
                        address_parts.append(addr["country"])
                    if address_parts:
                        print(f"   Address: {', '.join(address_parts)}")

            if contact.contact_info.telecoms:
                for telecom in contact.contact_info.telecoms:
                    if "type" in telecom and "value" in telecom:
                        print(f"   {telecom['type']}: {telecom['value']}")

            if contact.organization.name:
                print(f"   Organization: {contact.organization.name}")
    else:
        print("❌ No participants found")

    # Show comparison with existing contacts
    print("\n📊 CONTACT SUMMARY")
    print("=" * 30)
    print(
        f"👤 Patient Contact Info: {len(admin_data.patient_contact_info.addresses)} addresses, {len(admin_data.patient_contact_info.telecoms)} telecoms"
    )
    print(
        f"✍️  Author HCP: {admin_data.author_hcp.given_name} {admin_data.author_hcp.family_name}"
    )
    print(
        f"📝 Legal Authenticator: {admin_data.legal_authenticator.given_name} {admin_data.legal_authenticator.family_name}"
    )
    print(f"🏢 Custodian: {admin_data.custodian_organization.name}")
    print(f"👥 Participants: {len(admin_data.other_contacts)} contacts")

    print("\n✅ Participant extraction test completed successfully!")


if __name__ == "__main__":
    test_participant_extraction()
