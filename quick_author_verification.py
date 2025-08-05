"""
Quick verification that author details are comprehensive
"""

import os
import sys
import django
from pathlib import Path
import xml.etree.ElementTree as ET

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def quick_author_test():
    """Quick test to verify author details are comprehensive"""

    print("🔍 QUICK AUTHOR VERIFICATION")
    print("=" * 40)

    from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAParser

    # Test with the same file
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

        # Check administrative info
        admin_info = result.get("administrative_info", {})
        authors = admin_info.get("authors", [])
        legal_auth = admin_info.get("legal_authenticator", {})

        print(f"📋 Authors found: {len(authors)}")
        print(f"⚖️ Legal authenticator: {legal_auth.get('full_name', 'None')}")

        if authors:
            author = authors[0]  # Check first author
            print(f"\n👤 FIRST AUTHOR DETAILS:")
            print(f"  Name: {author.get('full_name', 'None')}")
            print(f"  Role: {author.get('role', 'None')}")

            org = author.get("organization", {})
            print(f"  Organization: {org.get('name', 'None')}")

            address = org.get("address", {})
            print(f"  Address: {address.get('full_address', 'None')}")

            telecoms = org.get("telecoms", [])
            print(f"  Contact methods: {len(telecoms)}")

            # Check structure completeness
            expected_keys = [
                "time",
                "family_name",
                "given_name",
                "full_name",
                "person",
                "organization",
                "id",
                "code",
                "role",
            ]
            missing = [k for k in expected_keys if k not in author]

            if missing:
                print(f"  ⚠️ Missing keys: {missing}")
            else:
                print(f"  ✅ All expected keys present")

        print(f"\n🎯 TEMPLATE ACCESS TEST:")

        # Test legal authenticator template access
        print(f"  legal_authenticator.full_name: '{legal_auth.get('full_name')}'")
        print(f"  legal_authenticator.given_name: '{legal_auth.get('given_name')}'")

        # Test author template access
        if authors:
            author = authors[0]
            print(f"  author.full_name: '{author.get('full_name')}'")
            print(
                f"  author.organization.name: '{author.get('organization', {}).get('name')}'"
            )

        print("\n✅ VERIFICATION COMPLETE")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    quick_author_test()
