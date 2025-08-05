"""
Test Contact Card System with Legal Authenticator Data
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


def test_contact_card_system():
    """Test the new contact card system with real data"""

    print("🎴 TESTING CONTACT CARD SYSTEM")
    print("=" * 50)

    from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAParser
    from patient_data.templatetags.contact_cards import normalize_contact_data

    # Test with the same Italian file
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    parser = EnhancedCDAParser()

    try:
        with open(test_file, "r", encoding="utf-8") as f:
            xml_content = f.read()

        result = parser.parse_cda_document(xml_content)
        admin_info = result.get("administrative_info", {})

        print("📋 ADMINISTRATIVE DATA EXTRACTED:")
        print(
            f"  Legal Authenticator: {'✓' if admin_info.get('legal_authenticator') else '✗'}"
        )
        print(f"  Authors: {len(admin_info.get('authors', []))} found")
        print(f"  Custodian: {'✓' if admin_info.get('custodian') else '✗'}")
        print(f"  Patient Contact: {'✓' if admin_info.get('patient_contact') else '✗'}")

        # Test legal authenticator normalization
        if admin_info.get("legal_authenticator"):
            print("\n⚖️ LEGAL AUTHENTICATOR NORMALIZATION TEST:")
            legal_auth = admin_info["legal_authenticator"]

            print("  Raw data keys:", list(legal_auth.keys()))

            # Test normalization
            normalized = normalize_contact_data(legal_auth)
            print("  Normalized keys:", list(normalized.keys()))

            # Test template-friendly access
            print("\n  🎭 TEMPLATE ACCESS RESULTS:")
            print(f"    full_name: '{normalized.get('full_name')}'")
            print(f"    given_name: '{normalized.get('given_name')}'")
            print(f"    family_name: '{normalized.get('family_name')}'")
            print(f"    role: '{normalized.get('role')}'")
            print(f"    signature_code: '{normalized.get('signature_code')}'")

            # Test organization access
            org = normalized.get("organization", {})
            print(f"    organization.name: '{org.get('name')}'")

            # Test address access
            address = normalized.get("address", {})
            print(f"    address.full_address: '{address.get('full_address')}'")
            print(f"    address.city: '{address.get('city')}'")
            print(f"    address.country: '{address.get('country')}'")

            # Test telecoms access
            telecoms = normalized.get("telecoms", [])
            print(f"    telecoms: {len(telecoms)} found")
            for i, telecom in enumerate(telecoms):
                print(
                    f"      telecom[{i}]: {telecom.get('type')} - {telecom.get('display_value')}"
                )

        # Test authors normalization
        if admin_info.get("authors"):
            print(f"\n👥 AUTHORS NORMALIZATION TEST:")
            authors = admin_info["authors"]

            for i, author in enumerate(authors[:2]):  # Test first 2 authors
                print(f"\n  Author {i+1}:")
                normalized = normalize_contact_data(author)

                print(f"    full_name: '{normalized.get('full_name')}'")
                print(f"    role: '{normalized.get('role')}'")

                org = normalized.get("organization", {})
                print(f"    organization.name: '{org.get('name')}'")

                telecoms = normalized.get("telecoms", [])
                print(f"    telecoms: {len(telecoms)} contact methods")

        # Test template card context simulation
        print(f"\n🎴 CONTACT CARD CONTEXT SIMULATION:")

        if admin_info.get("legal_authenticator"):
            legal_auth_normalized = normalize_contact_data(
                admin_info["legal_authenticator"]
            )

            # Simulate what the contact_card template tag would receive
            card_context = {
                "contact": legal_auth_normalized,
                "card_title": "Legal Authenticator",
                "card_type": "legal_auth",
                "has_name": bool(legal_auth_normalized.get("full_name")),
                "has_organization": bool(
                    legal_auth_normalized.get("organization", {}).get("name")
                ),
                "has_address": bool(
                    legal_auth_normalized.get("address", {}).get("full_address")
                ),
                "has_contact_info": bool(legal_auth_normalized.get("telecoms")),
                "has_role": bool(legal_auth_normalized.get("role")),
                "has_id": bool(legal_auth_normalized.get("id")),
                "has_time": bool(legal_auth_normalized.get("time")),
            }

            print("  Card context flags:")
            for key, value in card_context.items():
                if key.startswith("has_"):
                    print(f"    {key}: {value}")

        print(f"\n✅ CONTACT CARD SYSTEM READY!")
        print("🎯 Template Usage Examples:")
        print("   {% load contact_cards %}")
        print(
            "   {% contact_card legal_authenticator 'Legal Authenticator' 'legal_auth' %}"
        )
        print("   {% contact_card_list authors 'Document Authors' 'author' %}")
        print("   {{ legal_authenticator|get_contact_name }}")
        print("   {{ legal_authenticator|get_organization_name }}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_contact_card_system()
