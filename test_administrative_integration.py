#!/usr/bin/env python3
"""
Enhanced Administrative Parser Integration Test
Test and fix the administrative data extraction to work with contact cards
"""

import os
import sys
import django
from pathlib import Path
import xml.etree.ElementTree as ET
import json

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def test_administrative_extraction_integration():
    """Test and demonstrate the administrative data extraction integration"""

    print("🔧 ADMINISTRATIVE EXTRACTION INTEGRATION TEST")
    print("=" * 60)

    # Use Italian file as example
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    print(f"📄 Testing: {test_file.name}")

    # Parse with current parser
    parser = EnhancedCDAXMLParser()

    try:
        result = parser.parse_cda_content(xml_content)

        print(f"\n📊 PARSER RESULT STRUCTURE:")
        print(f"  Total keys: {len(result)}")
        for key, value in result.items():
            if isinstance(value, dict):
                print(f"  {key}: dict with {len(value)} keys")
            elif isinstance(value, list):
                print(f"  {key}: list with {len(value)} items")
            else:
                print(f"  {key}: {type(value).__name__} - {value}")

        # Focus on administrative_data
        admin_data = result.get("administrative_data", {})
        print(f"\n🏛️ ADMINISTRATIVE_DATA STRUCTURE:")
        if admin_data:
            print(f"  Keys: {list(admin_data.keys())}")

            # Check for patient contact info
            patient_contact = admin_data.get("patient_contact_info", {})
            print(f"\n👤 PATIENT CONTACT INFO:")
            if patient_contact:
                print(f"    Keys: {list(patient_contact.keys())}")
                addresses = patient_contact.get("addresses", [])
                telecoms = patient_contact.get("telecoms", [])
                print(f"    Addresses: {len(addresses)}")
                print(f"    Telecoms: {len(telecoms)}")
                if addresses:
                    print(f"    First address: {addresses[0]}")
                if telecoms:
                    print(f"    First telecom: {telecoms[0]}")
            else:
                print("    No patient contact info found")

            # Check for legal authenticator
            legal_auth = admin_data.get("legal_authenticator", {})
            print(f"\n⚖️ LEGAL AUTHENTICATOR:")
            if legal_auth:
                print(f"    Keys: {list(legal_auth.keys())}")
                print(f"    Person: {legal_auth.get('person', {})}")
                print(f"    Organization: {legal_auth.get('organization', {})}")
            else:
                print("    No legal authenticator found")

            # Check for custodian
            custodian_org = admin_data.get("custodian_organization", {})
            print(f"\n🏛️ CUSTODIAN:")
            if custodian_org:
                print(f"    Keys: {list(custodian_org.keys())}")
                print(f"    Name: {custodian_org.get('name', 'N/A')}")
            else:
                print("    No custodian found")

            # Check for authors
            authors = admin_data.get("author_information", [])
            print(f"\n✍️ AUTHORS:")
            print(f"    Count: {len(authors)}")
            if authors:
                first_author = authors[0]
                print(f"    First author keys: {list(first_author.keys())}")
                print(f"    First author person: {first_author.get('person', {})}")
                print(f"    First author org: {first_author.get('organization', {})}")
        else:
            print("  No administrative data found")

        # Transform for contact cards compatibility
        print(f"\n🎴 TRANSFORMING FOR CONTACT CARDS:")
        transformed = transform_to_contact_card_format(admin_data)

        print(f"  Transformed keys: {list(transformed.keys())}")
        for key, value in transformed.items():
            if isinstance(value, dict) and value:
                print(f"    {key}: {len(value)} fields")
            elif isinstance(value, list):
                print(f"    {key}: {len(value)} items")
            else:
                print(f"    {key}: {type(value).__name__}")

        # Test contact card compatibility
        print(f"\n🧪 CONTACT CARD COMPATIBILITY TEST:")
        test_contact_card_compatibility(transformed)

    except Exception as e:
        print(f"❌ Parser error: {e}")
        import traceback

        traceback.print_exc()


def transform_to_contact_card_format(admin_data):
    """Transform administrative_data to administrative_info format for contact cards"""

    transformed = {}

    # Transform patient contact
    patient_contact = admin_data.get("patient_contact_info", {})
    if patient_contact:
        transformed["patient_contact"] = {
            "full_name": patient_contact.get("full_name", ""),
            "given_name": patient_contact.get("given_name", ""),
            "family_name": patient_contact.get("family_name", ""),
            "birth_date": patient_contact.get("birth_date", ""),
            "gender": patient_contact.get("gender", ""),
            "patient_id": patient_contact.get("patient_id", ""),
            "addresses": patient_contact.get("addresses", []),
            "telecoms": patient_contact.get("telecoms", []),
        }

    # Transform legal authenticator
    legal_auth = admin_data.get("legal_authenticator", {})
    if legal_auth:
        person = legal_auth.get("person", {})
        org = legal_auth.get("organization", {})

        transformed["legal_authenticator"] = {
            "full_name": person.get("full_name", ""),
            "given_name": person.get("given_name", ""),
            "family_name": person.get("family_name", ""),
            "title": person.get("title", ""),
            "role": legal_auth.get("role", ""),
            "signature_code": legal_auth.get("signature_code", ""),
            "time": legal_auth.get("time", ""),
            "organization": {
                "name": org.get("name", ""),
                "id": org.get("id", ""),
                "addresses": org.get("addresses", []),
                "telecoms": org.get("telecoms", []),
            },
            "addresses": legal_auth.get("addresses", []),
            "telecoms": legal_auth.get("telecoms", []),
        }

    # Transform custodian
    custodian_org = admin_data.get("custodian_organization", {})
    if custodian_org:
        transformed["custodian"] = {
            "organization_name": custodian_org.get("name", ""),
            "organization_id": custodian_org.get("id", ""),
            "addresses": custodian_org.get("addresses", []),
            "telecoms": custodian_org.get("telecoms", []),
        }

    # Transform authors
    authors = admin_data.get("author_information", [])
    if authors:
        transformed["authors"] = []
        for author in authors:
            person = author.get("person", {})
            org = author.get("organization", {})

            transformed_author = {
                "full_name": person.get("full_name", ""),
                "given_name": person.get("given_name", ""),
                "family_name": person.get("family_name", ""),
                "title": person.get("title", ""),
                "role": author.get("role", ""),
                "time": author.get("time", ""),
                "organization": {
                    "name": org.get("name", ""),
                    "id": org.get("id", ""),
                    "addresses": org.get("addresses", []),
                    "telecoms": org.get("telecoms", []),
                },
                "addresses": author.get("addresses", []),
                "telecoms": author.get("telecoms", []),
            }
            transformed["authors"].append(transformed_author)

    return transformed


def test_contact_card_compatibility(transformed_data):
    """Test if the transformed data works with contact card templates"""

    # Test data availability for each contact type
    contact_types = {
        "patient_contact": "Patient Contact",
        "legal_authenticator": "Legal Authenticator",
        "custodian": "Custodian",
        "authors": "Authors",
    }

    for contact_type, display_name in contact_types.items():
        contact_data = transformed_data.get(contact_type)

        if contact_type == "authors":
            if contact_data and isinstance(contact_data, list):
                print(f"  ✅ {display_name}: {len(contact_data)} authors available")
                if contact_data:
                    first_author = contact_data[0]
                    print(
                        f"    First author name: {first_author.get('full_name', 'N/A')}"
                    )
                    print(
                        f"    Organization: {first_author.get('organization', {}).get('name', 'N/A')}"
                    )
            else:
                print(f"  ❌ {display_name}: No authors found")
        else:
            if contact_data:
                print(f"  ✅ {display_name}: Available")
                name_fields = ["full_name", "given_name", "family_name"]
                name_info = [contact_data.get(field, "") for field in name_fields]
                print(f"    Name info: {' '.join(filter(None, name_info)) or 'N/A'}")

                # Check organization
                if "organization" in contact_data:
                    org = contact_data["organization"]
                    if isinstance(org, dict):
                        org_name = org.get("name", "N/A")
                        print(f"    Organization: {org_name}")
                elif "organization_name" in contact_data:
                    print(
                        f"    Organization: {contact_data.get('organization_name', 'N/A')}"
                    )

                # Check addresses
                addresses = contact_data.get("addresses", [])
                print(f"    Addresses: {len(addresses)}")

                # Check telecoms
                telecoms = contact_data.get("telecoms", [])
                print(f"    Telecoms: {len(telecoms)}")
            else:
                print(f"  ❌ {display_name}: Not available")

    # Test template tag compatibility simulation
    print(f"\n📋 TEMPLATE TAG SIMULATION:")
    from patient_data.templatetags.contact_cards import normalize_contact_data

    for contact_type, display_name in contact_types.items():
        contact_data = transformed_data.get(contact_type)

        if contact_type == "authors":
            if contact_data and contact_data:
                try:
                    normalized = normalize_contact_data(contact_data[0])
                    print(f"  ✅ {display_name}: Template normalization successful")
                    print(f"    Normalized name: {normalized.get('full_name', 'N/A')}")
                except Exception as e:
                    print(f"  ❌ {display_name}: Template normalization failed - {e}")
        else:
            if contact_data:
                try:
                    normalized = normalize_contact_data(contact_data)
                    print(f"  ✅ {display_name}: Template normalization successful")
                    print(f"    Normalized name: {normalized.get('full_name', 'N/A')}")
                except Exception as e:
                    print(f"  ❌ {display_name}: Template normalization failed - {e}")


if __name__ == "__main__":
    test_administrative_extraction_integration()
