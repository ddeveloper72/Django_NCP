#!/usr/bin/env python3
"""
Test Enhanced Administrative Data Extraction
Verify comprehensive extraction of contact information and organizational data
"""

import os
import sys
import django
from pathlib import Path

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def test_enhanced_administrative_extraction():
    """Test enhanced administrative data extraction"""

    print("🔍 ENHANCED ADMINISTRATIVE DATA EXTRACTION TEST")
    print("=" * 50)

    # Try to find test files
    test_folders = [
        "test_data/eu_member_states/IT",
        "test_data/eu_member_states/FR",
        "test_data/eu_member_states/DE",
        "test_data",
    ]

    test_file = None
    for folder in test_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            xml_files = list(folder_path.glob("*.xml"))
            if xml_files:
                test_file = xml_files[0]
                print(f"📁 Using test file: {test_file}")
                break

    if not test_file:
        print("❌ No test files found")
        return

    print("\n🔧 TESTING ENHANCED PARSER:")

    # Test with Enhanced parser
    parser = EnhancedCDAXMLParser()

    try:
        result = parser.parse_cda_file(test_file)

        if not result:
            print("❌ Parser returned no result")
            return

        print("✅ Parse successful!")

        # Test administrative data
        admin_data = result.get("administrative_data", {})
        print(f"\n📋 ADMINISTRATIVE DATA SUMMARY:")
        print(f"  Document Title: {admin_data.get('document_title', 'N/A')}")
        print(f"  Document Type: {admin_data.get('document_type', 'N/A')}")
        print(f"  Creation Date: {admin_data.get('document_creation_date', 'N/A')}")
        print(f"  Document ID: {admin_data.get('document_id', 'N/A')}")

        # Test patient contact information
        patient_contact = admin_data.get("patient_contact_info", {})
        print(f"\n👤 PATIENT CONTACT INFORMATION:")

        addresses = patient_contact.get("addresses", [])
        print(f"  Addresses Found: {len(addresses)}")
        for i, addr in enumerate(addresses):
            print(f"    Address {i+1} ({addr.get('use', 'unknown')}):")
            print(f"      Full: {addr.get('full_address', 'N/A')}")
            print(f"      Street: {addr.get('street_address_line', 'N/A')}")
            print(f"      City: {addr.get('city', 'N/A')}")
            print(f"      Country: {addr.get('country', 'N/A')}")

        telecoms = patient_contact.get("telecoms", [])
        print(f"  Telecoms Found: {len(telecoms)}")
        for i, tel in enumerate(telecoms):
            print(f"    Telecom {i+1} ({tel.get('type', 'unknown')}):")
            print(f"      Use: {tel.get('use', 'N/A')}")
            print(f"      Value: {tel.get('display_value', 'N/A')}")

        # Primary contacts
        primary_addr = patient_contact.get("primary_address")
        primary_phone = patient_contact.get("primary_phone")
        primary_email = patient_contact.get("primary_email")

        print(
            f"  Primary Address: {primary_addr.get('full_address', 'None') if primary_addr else 'None'}"
        )
        print(
            f"  Primary Phone: {primary_phone.get('display_value', 'None') if primary_phone else 'None'}"
        )
        print(
            f"  Primary Email: {primary_email.get('display_value', 'None') if primary_email else 'None'}"
        )

        # Test author information
        authors = admin_data.get("author_information", [])
        print(f"\n👨‍⚕️ AUTHOR INFORMATION:")
        print(f"  Authors Found: {len(authors)}")
        for i, author in enumerate(authors):
            print(f"    Author {i+1}:")
            print(f"      Name: {author.get('person', {}).get('full_name', 'N/A')}")
            print(f"      Role: {author.get('role', 'N/A')}")
            print(f"      Time: {author.get('time', 'N/A')}")
            print(
                f"      Organization: {author.get('organization', {}).get('name', 'N/A')}"
            )

        # Test custodian information
        custodian = admin_data.get("custodian_organization", {})
        print(f"\n🏥 CUSTODIAN ORGANIZATION:")
        print(f"  Name: {custodian.get('name', 'N/A')}")
        print(
            f"  ID: {custodian.get('id', {}).get('extension', 'N/A') if custodian.get('id') else 'N/A'}"
        )

        custodian_addr = custodian.get("address", {})
        if custodian_addr:
            print(f"  Address: {custodian_addr.get('full_address', 'N/A')}")

        custodian_telecoms = custodian.get("telecoms", [])
        print(f"  Telecoms: {len(custodian_telecoms)}")
        for tel in custodian_telecoms:
            print(
                f"    {tel.get('type', 'unknown')}: {tel.get('display_value', 'N/A')}"
            )

        # Test legal authenticator
        legal_auth = admin_data.get("legal_authenticator", {})
        print(f"\n📝 LEGAL AUTHENTICATOR:")
        print(f"  Name: {legal_auth.get('person', {}).get('full_name', 'N/A')}")
        print(f"  Time: {legal_auth.get('time', 'N/A')}")
        print(f"  Signature Code: {legal_auth.get('signature_code', 'N/A')}")

        # Test backward compatibility
        print(f"\n🔄 BACKWARD COMPATIBILITY:")
        author_hcp = admin_data.get("author_hcp", {})
        print(f"  Author HCP Name: {author_hcp.get('full_name', 'N/A')}")
        print(f"  Custodian Name (legacy): {admin_data.get('custodian_name', 'N/A')}")

        print(f"\n📊 DATA SUMMARY:")
        print(f"  Patient Addresses: {len(patient_contact.get('addresses', []))}")
        print(f"  Patient Telecoms: {len(patient_contact.get('telecoms', []))}")
        print(f"  Authors: {len(authors)}")
        print(f"  Custodian Telecoms: {len(custodian.get('telecoms', []))}")

    except Exception as e:
        print(f"❌ Parser error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_enhanced_administrative_extraction()
