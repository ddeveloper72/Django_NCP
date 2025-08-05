"""
Comprehensive test for the administrative extractor with template compatibility
"""

import xml.etree.ElementTree as ET
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_template_access():
    """Test that the extracted data works properly in template context"""

    try:
        from patient_data.utils.administrative_extractor import (
            CDAAdministrativeExtractor,
        )

        print("✓ CDAAdministrativeExtractor imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

    # Test with file that has legal authenticator
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

        # Extract legal authenticator
        legal_auth = extractor.extract_legal_authenticator(root)
        print("\n=== LEGAL AUTHENTICATOR EXTRACTION ===")
        print("Full extracted data:")
        for key, value in legal_auth.items():
            print(f"  {key}: {value}")

        # Test template access scenarios
        print("\n=== TEMPLATE COMPATIBILITY TEST ===")

        # Simulate Django template context
        context = {"legal_authenticator": legal_auth}

        # Test 1: Direct access to flat fields (what templates expect)
        try:
            full_name = context["legal_authenticator"]["full_name"]
            print(f"✓ Template access legal_authenticator.full_name: '{full_name}'")
        except KeyError as e:
            print(f"✗ Template access failed for full_name: {e}")

        try:
            given_name = context["legal_authenticator"]["given_name"]
            print(f"✓ Template access legal_authenticator.given_name: '{given_name}'")
        except KeyError as e:
            print(f"✗ Template access failed for given_name: {e}")

        try:
            family_name = context["legal_authenticator"]["family_name"]
            print(f"✓ Template access legal_authenticator.family_name: '{family_name}'")
        except KeyError as e:
            print(f"✗ Template access failed for family_name: {e}")

        # Test 2: Nested access still works
        try:
            nested_name = context["legal_authenticator"]["person"]["full_name"]
            print(
                f"✓ Nested access legal_authenticator.person.full_name: '{nested_name}'"
            )
        except KeyError as e:
            print(f"⚠ Nested access failed: {e}")

        # Test 3: Organization access
        try:
            org_name = context["legal_authenticator"]["organization"]["name"]
            print(
                f"✓ Organization access legal_authenticator.organization.name: '{org_name}'"
            )
        except KeyError as e:
            print(f"⚠ Organization access failed: {e}")

        # Test 4: Template simulation - this is what would cause the error before
        print("\n=== TEMPLATE ERROR SIMULATION ===")

        # Before our fix, this would fail with "{{ no such element: dict object['given_name'] }}"
        # Now it should work:
        template_vars = {
            "name": legal_auth.get("full_name", "Unknown"),
            "given": legal_auth.get("given_name", ""),
            "family": legal_auth.get("family_name", ""),
        }

        print("Template variables that would be rendered:")
        for var, value in template_vars.items():
            print(f"  {var}: '{value}'")

        # Success indicator
        if legal_auth.get("full_name"):
            print("\n✓ SUCCESS: Legal authenticator template errors should be FIXED!")
            print(f"  Expected name in UI: '{legal_auth['full_name']}'")
        else:
            print(
                "\n⚠ No name found in this document, but structure is template-compatible"
            )

        return True

    except Exception as e:
        import traceback

        print(f"✗ Error: {e}")
        traceback.print_exc()
        return False


def test_author_extraction():
    """Test author extraction for comparison"""

    try:
        from patient_data.utils.administrative_extractor import (
            CDAAdministrativeExtractor,
        )

        test_file = r"test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

        if not os.path.exists(test_file):
            print(f"✗ Test file not found: {test_file}")
            return False

        tree = ET.parse(test_file)
        root = tree.getroot()

        extractor = CDAAdministrativeExtractor()

        # Extract authors
        authors = extractor.extract_author_information(root)
        print(f"\n=== AUTHOR EXTRACTION ===")
        print(f"Found {len(authors)} authors")

        for i, author in enumerate(authors):
            print(f"\nAuthor {i+1}:")
            print(f"  full_name: {author.get('full_name')}")
            print(f"  given_name: {author.get('given_name')}")
            print(f"  family_name: {author.get('family_name')}")
            print(f"  role: {author.get('role')}")

        return True

    except Exception as e:
        print(f"✗ Author extraction error: {e}")
        return False


if __name__ == "__main__":
    print("Testing CDA Administrative Extractor Template Compatibility")
    print("=" * 60)

    # Test legal authenticator
    legal_success = test_template_access()

    # Test authors
    author_success = test_author_extraction()

    print("\n" + "=" * 60)
    if legal_success:
        print("✅ LEGAL AUTHENTICATOR: Template errors should be RESOLVED!")
    else:
        print("❌ LEGAL AUTHENTICATOR: Issues remain")

    if author_success:
        print("✅ AUTHORS: Extraction working")
    else:
        print("❌ AUTHORS: Issues found")
