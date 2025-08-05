#!/usr/bin/env python3
"""
Test script to verify the complete administrative data structure
that's being passed to templates including participants
"""

import os
import sys
import django
from pathlib import Path
import json

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def test_complete_administrative_structure():
    """Test complete administrative data structure for templates"""
    print("🔍 Testing Complete Administrative Data Structure for Templates")
    print("=" * 70)

    # Read the Latvia L3 CDA document
    cda_file_path = "test_data/eu_member_states/LV/2025-04-01T11-25-07.284098Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    try:
        with open(cda_file_path, "r", encoding="utf-8") as file:
            cda_content = file.read()

        print(f"✅ Successfully loaded CDA document: {cda_file_path}")

    except FileNotFoundError:
        print(f"❌ ERROR: Could not find CDA file: {cda_file_path}")
        return
    except Exception as e:
        print(f"❌ ERROR loading CDA file: {e}")
        return

    # Parse administrative data using enhanced parser
    parser = EnhancedCDAXMLParser()

    try:
        # Parse the complete document
        parsed_data = parser.parse_cda_content(cda_content)

        # Extract administrative data structure
        admin_data = parsed_data.get("administrative_data", {})

        print("✅ Administrative data parsing completed")
        print(f"📊 Administrative data keys: {list(admin_data.keys())}")

    except Exception as e:
        print(f"❌ ERROR during parsing: {e}")
        import traceback

        traceback.print_exc()
        return

    # Display administrative data structure
    print("\n📋 ADMINISTRATIVE DATA STRUCTURE")
    print("=" * 50)

    # Display other_contacts (participants)
    if "other_contacts" in admin_data and admin_data["other_contacts"]:
        print(
            f"👥 Found {len(admin_data['other_contacts'])} other_contacts (participants):"
        )

        for i, contact in enumerate(admin_data["other_contacts"], 1):
            print(f"\n{i}. Contact Information:")
            print(f"   Role: {contact.get('role', 'Unknown')}")
            print(
                f"   Name: {contact.get('given_name', '')} {contact.get('family_name', '')}"
            )
            print(f"   Full Name: {contact.get('full_name', '')}")

            if contact.get("specialty"):
                print(f"   Period: {contact.get('specialty')}")

            # Contact info
            contact_info = contact.get("contact_info", {})
            if contact_info.get("telecoms"):
                print(f"   Telecoms: {len(contact_info['telecoms'])} entries")
                for telecom in contact_info["telecoms"]:
                    print(
                        f"     - {telecom.get('type', 'unknown')}: {telecom.get('value', '')}"
                    )

            if contact_info.get("addresses"):
                print(f"   Addresses: {len(contact_info['addresses'])} entries")
                for addr in contact_info["addresses"]:
                    parts = []
                    if addr.get("street"):
                        parts.append(addr["street"])
                    if addr.get("city"):
                        parts.append(addr["city"])
                    if addr.get("postalCode"):
                        parts.append(addr["postalCode"])
                    if addr.get("country"):
                        parts.append(addr["country"])
                    print(f"     - {', '.join(parts)}")

            # Organization info
            organization = contact.get("organization", {})
            if organization.get("name"):
                print(f"   Organization: {organization['name']}")
    else:
        print("❌ No other_contacts found in administrative data")

    # Display other administrative sections
    print("\n📋 OTHER ADMINISTRATIVE SECTIONS")
    print("=" * 40)

    # Patient contact info
    patient_contact = admin_data.get("patient_contact_info", {})
    if patient_contact:
        print(
            f"👤 Patient Contact: {len(patient_contact.get('addresses', []))} addresses, {len(patient_contact.get('telecoms', []))} telecoms"
        )

    # Author information
    author_info = admin_data.get("author_information", [])
    if author_info:
        print(f"✍️  Authors: {len(author_info)} entries")
        for author in author_info:
            person = author.get("person", {})
            print(
                f"   - {person.get('full_name', 'Unknown')} ({person.get('role', 'Unknown role')})"
            )

    # Legal authenticator
    legal_auth = admin_data.get("legal_authenticator", {})
    if legal_auth.get("full_name"):
        print(f"📝 Legal Authenticator: {legal_auth['full_name']}")

    # Custodian
    custodian = admin_data.get("custodian_organization", {})
    if custodian.get("name"):
        print(f"🏢 Custodian: {custodian['name']}")

    # Save structure to file for template development
    admin_structure = {
        "other_contacts_count": len(admin_data.get("other_contacts", [])),
        "sample_contact": (
            admin_data.get("other_contacts", [{}])[0]
            if admin_data.get("other_contacts")
            else {}
        ),
        "all_keys": list(admin_data.keys()),
        "sample_structure": {k: type(v).__name__ for k, v in admin_data.items()},
    }

    with open("administrative_structure_debug.json", "w") as f:
        # Convert to JSON-serializable format
        json_data = json.dumps(admin_structure, indent=2, default=str)
        f.write(json_data)

    print(
        f"\n💾 Administrative structure saved to 'administrative_structure_debug.json'"
    )
    print("\n✅ Complete administrative structure test completed!")


if __name__ == "__main__":
    test_complete_administrative_structure()
