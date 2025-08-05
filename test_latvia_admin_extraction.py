#!/usr/bin/env python3
"""
Test enhanced administrative data extraction for Latvia patient
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def test_latvia_admin_extraction():
    """Test administrative data extraction for Latvia patient"""
    print("=== Testing Latvia Administrative Data Extraction ===")

    # Path to the Latvia L3 CDA file
    latvia_file = "test_data/eu_member_states/LV/2025-04-01T11-25-06.811660Z_CDA_EHDSI---PIVOT-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    if not os.path.exists(latvia_file):
        print(f"❌ File not found: {latvia_file}")
        return

    # Read the CDA content
    with open(latvia_file, "r", encoding="utf-8") as f:
        cda_content = f.read()

    # Parse with enhanced parser
    parser = EnhancedCDAXMLParser()
    result = parser.parse_cda_content(cda_content)

    if result and "administrative_data" in result:
        admin_data = result["administrative_data"]

        print("✅ Administrative data extracted successfully")
        print(f"Document title: {admin_data.get('document_title', 'Unknown')}")
        print(f"Creation date: {admin_data.get('document_creation_date', 'Unknown')}")

        # Check author information
        print(f"\n📋 Author HCP Information:")
        author_hcp = admin_data.get("author_hcp", {})
        print(f"  Raw author_hcp data: {dict(author_hcp)}")
        if author_hcp.get("family_name"):
            print(
                f"  Name: {author_hcp.get('given_name', '')} {author_hcp.get('family_name', '')}"
            )
            print(f"  Title: {author_hcp.get('title', 'N/A')}")

            # Check organization
            org = author_hcp.get("organization", {})
            print(f"  Organization data: {dict(org) if org else 'None'}")
            if org.get("name"):
                print(f"  Organization: {org.get('name')}")
                if org.get("addresses"):
                    print(f"  Organization addresses: {len(org.get('addresses', []))}")
                    for addr in org.get("addresses", []):
                        print(f"    Address: {addr}")
                if org.get("telecoms"):
                    print(f"  Organization telecoms: {len(org.get('telecoms', []))}")
                    for tel in org.get("telecoms", []):
                        print(f"    Telecom: {tel}")
            else:
                print("  ❌ No organization information found")
        else:
            print("  ❌ No author information found")

        # Check legal authenticator
        print(f"\n⚖️ Legal Authenticator Information:")
        legal_auth = admin_data.get("legal_authenticator", {})
        print(f"  Raw legal_authenticator data: {dict(legal_auth)}")
        if legal_auth.get("family_name"):
            print(
                f"  Name: {legal_auth.get('given_name', '')} {legal_auth.get('family_name', '')}"
            )
            print(f"  Title: {legal_auth.get('title', 'N/A')}")

            # Check organization
            org = legal_auth.get("organization", {})
            print(f"  Organization data: {dict(org) if org else 'None'}")
            if org.get("name"):
                print(f"  Organization: {org.get('name')}")
                if org.get("addresses"):
                    print(f"  Organization addresses: {len(org.get('addresses', []))}")
                    for addr in org.get("addresses", []):
                        print(f"    Address: {addr}")
                if org.get("telecoms"):
                    print(f"  Organization telecoms: {len(org.get('telecoms', []))}")
                    for tel in org.get("telecoms", []):
                        print(f"    Telecom: {tel}")
            else:
                print("  ❌ No organization information found")
        else:
            print("  ❌ No legal authenticator information found")

        # Check custodian
        print(f"\n🏢 Custodian Organization:")
        custodian = admin_data.get("custodian_organization", {})
        if custodian.get("name"):
            print(f"  Name: {custodian.get('name')}")
            if custodian.get("addresses"):
                print(f"  Addresses: {len(custodian.get('addresses', []))}")
            if custodian.get("telecoms"):
                print(f"  Telecoms: {len(custodian.get('telecoms', []))}")
        else:
            print("  ❌ No custodian information found")

        # Check patient contact info
        print(f"\n👤 Patient Contact Information:")
        patient_contact = admin_data.get("patient_contact_info", {})
        if patient_contact.get("addresses"):
            print(f"  Addresses: {len(patient_contact.get('addresses', []))}")
        if patient_contact.get("telecoms"):
            print(f"  Telecoms: {len(patient_contact.get('telecoms', []))}")

        print(f"\n✅ Test completed successfully")

    else:
        print("❌ Failed to extract administrative data")


if __name__ == "__main__":
    test_latvia_admin_extraction()
