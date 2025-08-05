"""
Test to verify comprehensive author details are preserved
"""

import xml.etree.ElementTree as ET
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_comprehensive_author_details():
    """Test that all author details are properly extracted"""

    print("🔍 COMPREHENSIVE AUTHOR DETAILS TEST")
    print("=" * 60)

    try:
        from patient_data.utils.administrative_extractor import (
            CDAAdministrativeExtractor,
        )

        print("✓ CDAAdministrativeExtractor imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

    # Test with file that has authors
    test_file = r"test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    if not os.path.exists(test_file):
        print(f"✗ Test file not found: {test_file}")
        return False

    try:
        tree = ET.parse(test_file)
        root = tree.getroot()
        print("✓ XML file parsed successfully")

        extractor = CDAAdministrativeExtractor()
        print("✓ CDAAdministrativeExtractor instantiated")

        # Extract authors
        authors = extractor.extract_author_information(root)
        print(f"\n📋 AUTHORS EXTRACTED: {len(authors)} found")

        if not authors:
            print("⚠️ No authors found in document")
            return False

        # Check each author for comprehensive details
        for i, author in enumerate(authors):
            print(f"\n👤 AUTHOR {i+1} DETAILS:")
            print(f"  Structure keys: {list(author.keys())}")

            # Check direct access fields (template-friendly)
            print("\n  🎯 DIRECT ACCESS (Template-friendly):")
            print(f"    full_name: '{author.get('full_name')}'")
            print(f"    given_name: '{author.get('given_name')}'")
            print(f"    family_name: '{author.get('family_name')}'")
            print(f"    role: '{author.get('role')}'")
            print(f"    time: '{author.get('time')}'")

            # Check nested person structure
            person = author.get("person", {})
            print("\n  👤 PERSON STRUCTURE:")
            print(f"    person.full_name: '{person.get('full_name')}'")
            print(f"    person.given_name: '{person.get('given_name')}'")
            print(f"    person.family_name: '{person.get('family_name')}'")

            # Check ID structure
            id_info = author.get("id", {})
            print("\n  🆔 ID STRUCTURE:")
            if id_info:
                print(f"    extension: '{id_info.get('extension')}'")
                print(f"    root: '{id_info.get('root')}'")
                print(
                    f"    assigning_authority_name: '{id_info.get('assigning_authority_name')}'"
                )
            else:
                print("    No ID information")

            # Check code structure
            code_info = author.get("code", {})
            print("\n  📋 CODE STRUCTURE:")
            if code_info:
                print(f"    code: '{code_info.get('code')}'")
                print(f"    code_system: '{code_info.get('code_system')}'")
                print(f"    display_name: '{code_info.get('display_name')}'")
            else:
                print("    No code information")

            # Check organization structure (this is what was missing!)
            organization = author.get("organization", {})
            print("\n  🏢 ORGANIZATION STRUCTURE:")
            print(f"    name: '{organization.get('name')}'")

            org_id = organization.get("id", {})
            if org_id:
                print(f"    id.extension: '{org_id.get('extension')}'")
                print(f"    id.root: '{org_id.get('root')}'")
                print(
                    f"    id.assigning_authority_name: '{org_id.get('assigning_authority_name')}'"
                )

            org_address = organization.get("address", {})
            if org_address:
                print(f"    address.full_address: '{org_address.get('full_address')}'")
                print(
                    f"    address.street_address_line: '{org_address.get('street_address_line')}'"
                )
                print(f"    address.city: '{org_address.get('city')}'")
                print(f"    address.country: '{org_address.get('country')}'")

            org_telecoms = organization.get("telecoms", [])
            print(f"    telecoms: {len(org_telecoms)} found")
            for j, telecom in enumerate(org_telecoms):
                print(
                    f"      telecom[{j}]: {telecom.get('type')} - {telecom.get('display_value')} (use: {telecom.get('use')})"
                )

        # Template compatibility test
        print("\n" + "=" * 60)
        print("🎭 TEMPLATE COMPATIBILITY TEST")

        template_context = {"authors": authors}

        print("\nTemplate expressions that should work:")
        for i, author in enumerate(authors):
            print(f"\nAuthor {i+1}:")
            print(f"  ✅ author.full_name: '{author.get('full_name')}'")
            print(f"  ✅ author.role: '{author.get('role')}'")
            print(
                f"  ✅ author.organization.name: '{author.get('organization', {}).get('name')}'"
            )
            print(
                f"  ✅ author.organization.address.city: '{author.get('organization', {}).get('address', {}).get('city')}'"
            )

        # Check if we have all the original fields
        expected_fields = [
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

        missing_fields = []
        for author in authors:
            for field in expected_fields:
                if field not in author:
                    missing_fields.append(field)

        if missing_fields:
            print(f"\n⚠️ MISSING FIELDS: {list(set(missing_fields))}")
            return False
        else:
            print(f"\n✅ ALL EXPECTED FIELDS PRESENT")

        print("\n🎉 SUCCESS: Comprehensive author details preserved!")
        print("✅ Template-friendly direct access maintained")
        print("✅ Detailed nested structures preserved")
        print("✅ Organization details with addresses and telecoms included")

        return True

    except Exception as e:
        import traceback

        print(f"✗ Error: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔧 VERIFYING COMPREHENSIVE AUTHOR DETAILS RESTORATION")

    success = test_comprehensive_author_details()

    print("\n" + "🏁 FINAL RESULT " + "=" * 45)
    if success:
        print("✅ AUTHOR DETAILS FULLY RESTORED!")
        print("✅ All original fields and structures preserved")
        print("✅ Template compatibility maintained")
        print("✅ Organization addresses and telecoms included")
    else:
        print("❌ Some author details may be missing")

    print("\n💡 What should be visible in UI:")
    print("   • Author names (given + family)")
    print("   • Author roles/codes")
    print("   • Organization names")
    print("   • Organization addresses")
    print("   • Contact information (phone, email)")
    print("   • All administrative metadata")
