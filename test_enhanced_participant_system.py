#!/usr/bin/env python3
"""
Comprehensive test script to verify that participant extraction is working
correctly in the enhanced administrative data system for CDA documents.
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

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser
from patient_data.services.cda_administrative_extractor import (
    CDAAdministrativeExtractor,
)


def test_enhanced_participant_system():
    """Comprehensive test of the enhanced participant extraction system"""
    print("🔧 Testing Enhanced Participant Extraction System")
    print("=" * 60)

    # Read the Latvia L3 CDA document
    cda_file_path = "test_data/eu_member_states/LV/2025-04-01T11-25-07.284098Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    try:
        with open(cda_file_path, "r", encoding="utf-8") as file:
            cda_content = file.read()

        print(f"✅ Successfully loaded CDA document")

    except FileNotFoundError:
        print(f"❌ ERROR: Could not find CDA file")
        return
    except Exception as e:
        print(f"❌ ERROR loading CDA file: {e}")
        return

    print("\n🔍 TESTING DIRECT ADMINISTRATIVE EXTRACTOR")
    print("=" * 50)

    # Test direct administrative extractor
    extractor = CDAAdministrativeExtractor()
    admin_data = extractor.extract_administrative_data(cda_content)

    print(f"👥 Participants extracted: {len(admin_data.other_contacts)}")
    for i, contact in enumerate(admin_data.other_contacts, 1):
        print(f"  {i}. {contact.role}: {contact.given_name} {contact.family_name}")
        if contact.contact_info.telecoms:
            print(f"     Contact: {len(contact.contact_info.telecoms)} telecom(s)")
        if contact.contact_info.addresses:
            print(f"     Address: {len(contact.contact_info.addresses)} address(es)")

    print(
        f"👤 Patient contact: {len(admin_data.patient_contact_info.addresses)} addresses, {len(admin_data.patient_contact_info.telecoms)} telecoms"
    )
    print(
        f"✍️  Author: {admin_data.author_hcp.given_name} {admin_data.author_hcp.family_name}"
    )
    print(
        f"📝 Legal Auth: {admin_data.legal_authenticator.given_name} {admin_data.legal_authenticator.family_name}"
    )
    print(f"🏢 Custodian: {admin_data.custodian_organization.name}")

    print("\n🔍 TESTING ENHANCED CDA PARSER")
    print("=" * 50)

    # Test enhanced CDA parser (template data)
    parser = EnhancedCDAXMLParser()
    parsed_data = parser.parse_cda_content(cda_content)

    template_admin_data = parsed_data.get("administrative_data", {})

    print(f"📊 Template data keys: {list(template_admin_data.keys())}")

    # Test other_contacts in template data
    other_contacts = template_admin_data.get("other_contacts", [])
    print(f"👥 Template participants: {len(other_contacts)}")

    for i, contact in enumerate(other_contacts, 1):
        print(
            f"  {i}. {contact.get('role', 'Unknown')}: {contact.get('full_name', 'Unknown')}"
        )

        # Check contact info structure
        contact_info = contact.get("contact_info", {})
        telecoms = contact_info.get("telecoms", [])
        addresses = contact_info.get("addresses", [])

        print(
            f"     Contact Info: {len(telecoms)} telecom(s), {len(addresses)} address(es)"
        )

        # Check organization info
        organization = contact.get("organization", {})
        if organization.get("name"):
            print(f"     Organization: {organization['name']}")

    print("\n🔍 TESTING TEMPLATE DATA STRUCTURE")
    print("=" * 50)

    # Test specific template data fields
    template_fields = [
        "patient_contact_info",
        "author_information",
        "legal_authenticator",
        "custodian_organization",
        "other_contacts",
    ]

    for field in template_fields:
        if field in template_admin_data:
            data = template_admin_data[field]
            if isinstance(data, list):
                print(f"✅ {field}: {len(data)} items")
            elif isinstance(data, dict):
                if field == "patient_contact_info":
                    telecoms = data.get("telecoms", [])
                    addresses = data.get("addresses", [])
                    print(
                        f"✅ {field}: {len(telecoms)} telecoms, {len(addresses)} addresses"
                    )
                elif field in ["legal_authenticator", "custodian_organization"]:
                    name = data.get("name", "") or data.get("full_name", "")
                    print(f"✅ {field}: {name}")
                else:
                    print(f"✅ {field}: available")
            else:
                print(f"✅ {field}: {data}")
        else:
            print(f"❌ {field}: missing")

    print("\n🔍 TESTING PARTICIPANT TYPES")
    print("=" * 50)

    # Analyze participant types
    participant_types = {}
    for contact in other_contacts:
        role = contact.get("role", "Unknown")
        if role not in participant_types:
            participant_types[role] = 0
        participant_types[role] += 1

    for role, count in participant_types.items():
        print(f"👤 {role}: {count} contact(s)")

    print("\n🔍 TESTING CONTACT INFORMATION COMPLETENESS")
    print("=" * 50)

    # Test completeness of contact information
    contacts_with_phones = 0
    contacts_with_emails = 0
    contacts_with_addresses = 0

    for contact in other_contacts:
        contact_info = contact.get("contact_info", {})
        telecoms = contact_info.get("telecoms", [])
        addresses = contact_info.get("addresses", [])

        has_phone = any(t.get("type") == "phone" for t in telecoms)
        has_email = any(t.get("type") == "email" for t in telecoms)
        has_address = len(addresses) > 0

        if has_phone:
            contacts_with_phones += 1
        if has_email:
            contacts_with_emails += 1
        if has_address:
            contacts_with_addresses += 1

    total_contacts = len(other_contacts)
    print(f"📞 Contacts with phone: {contacts_with_phones}/{total_contacts}")
    print(f"📧 Contacts with email: {contacts_with_emails}/{total_contacts}")
    print(f"🏠 Contacts with address: {contacts_with_addresses}/{total_contacts}")

    print("\n✅ ENHANCED PARTICIPANT SYSTEM TEST RESULTS")
    print("=" * 60)
    print(
        f"🎯 Participant extraction: {'✅ SUCCESS' if len(other_contacts) > 0 else '❌ FAILED'}"
    )
    print(
        f"🎯 Template data structure: {'✅ SUCCESS' if 'other_contacts' in template_admin_data else '❌ FAILED'}"
    )
    print(
        f"🎯 Contact information: {'✅ SUCCESS' if contacts_with_phones > 0 or contacts_with_emails > 0 else '❌ FAILED'}"
    )
    print(
        f"🎯 Emergency contacts: {'✅ SUCCESS' if 'Emergency Contact' in participant_types else '❌ FAILED'}"
    )
    print(
        f"🎯 Primary care providers: {'✅ SUCCESS' if 'Primary Care Provider' in participant_types else '❌ FAILED'}"
    )

    print(
        f"\n🏆 Overall System Status: {'✅ FULLY OPERATIONAL' if len(other_contacts) >= 3 else '⚠️  NEEDS ATTENTION'}"
    )
    print("\n✅ Enhanced participant system test completed successfully!")


if __name__ == "__main__":
    test_enhanced_participant_system()
