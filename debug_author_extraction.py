#!/usr/bin/env python3
"""
Debug Author Extraction Specifically
Test why author extraction is returning 0 authors when XML has 1
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

from patient_data.utils.flexible_cda_extractor import FlexibleCDAExtractor
from patient_data.utils.administrative_extractor import EnhancedAdministrativeExtractor


def debug_author_extraction():
    """Debug author extraction specifically"""

    print("🔍 DEBUGGING AUTHOR EXTRACTION")
    print("=" * 50)

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

    root = ET.fromstring(xml_content)

    # 1. Raw XML author check
    print(f"\n🔍 RAW XML AUTHOR CHECK:")
    authors_xml = root.findall(".//{urn:hl7-org:v3}author")
    print(f"  Direct XML search: {len(authors_xml)} author elements found")

    if authors_xml:
        for i, author in enumerate(authors_xml):
            print(f"  Author {i+1}:")

            # Check time
            time_elem = author.find("{urn:hl7-org:v3}time")
            if time_elem is not None:
                print(f"    Time: {time_elem.get('value')}")

            # Check assigned author
            assigned_author = author.find("{urn:hl7-org:v3}assignedAuthor")
            if assigned_author is not None:
                print(f"    Assigned author found")

                # Check person
                person = assigned_author.find("{urn:hl7-org:v3}assignedPerson")
                if person is not None:
                    print(f"    Person found")
                    name = person.find("{urn:hl7-org:v3}name")
                    if name is not None:
                        given = name.find("{urn:hl7-org:v3}given")
                        family = name.find("{urn:hl7-org:v3}family")
                        print(
                            f"      Given: {given.text if given is not None and given.text else 'None'}"
                        )
                        print(
                            f"      Family: {family.text if family is not None and family.text else 'None'}"
                        )

                # Check organization
                org = assigned_author.find("{urn:hl7-org:v3}representedOrganization")
                if org is not None:
                    print(f"    Organization found")
                    org_name = org.find("{urn:hl7-org:v3}name")
                    if org_name is not None:
                        print(
                            f"      Org name: {org_name.text if org_name.text else 'None'}"
                        )

    # 2. Test FlexibleCDAExtractor directly
    print(f"\n🔧 FLEXIBLE EXTRACTOR TEST:")
    flexible_extractor = FlexibleCDAExtractor()

    try:
        authors_flexible = flexible_extractor.extract_author_flexible(root)
        print(f"  Flexible extractor: {len(authors_flexible)} authors found")

        for i, author in enumerate(authors_flexible):
            print(f"  Author {i+1}:")
            print(f"    Full name: {author.get('full_name', 'None')}")
            print(f"    Given name: {author.get('given_name', 'None')}")
            print(f"    Family name: {author.get('family_name', 'None')}")
            print(
                f"    Organization: {author.get('organization', {}).get('name', 'None')}"
            )
            print(f"    Time: {author.get('time', 'None')}")

    except Exception as e:
        print(f"  ❌ Flexible extractor error: {e}")
        import traceback

        traceback.print_exc()

    # 3. Test Enhanced Administrative Extractor
    print(f"\n🏛️ ENHANCED ADMIN EXTRACTOR TEST:")

    try:
        admin_extractor = EnhancedAdministrativeExtractor()
        authors_admin = admin_extractor.extract_author_information(root)
        print(f"  Enhanced admin extractor: {len(authors_admin)} authors found")

        for i, author in enumerate(authors_admin):
            print(f"  Author {i+1}:")
            print(f"    Full name: {author.get('full_name', 'None')}")
            print(f"    Person: {author.get('person', {})}")
            print(f"    Organization: {author.get('organization', {})}")
            print(f"    Time: {author.get('time', 'None')}")

    except Exception as e:
        print(f"  ❌ Enhanced admin extractor error: {e}")
        import traceback

        traceback.print_exc()

    # 4. Debug flexible search method
    print(f"\n🔍 DEBUG FLEXIBLE SEARCH:")

    try:
        # Test finding author elements
        test_paths = [
            ".//author",
            "author",
            ".//hl7:author",
            ".//{urn:hl7-org:v3}author",
        ]

        for path in test_paths:
            try:
                elements = flexible_extractor.find_elements_flexible(root, path)
                print(f"  Path '{path}': {len(elements) if elements else 0} elements")
            except Exception as e:
                print(f"  Path '{path}': Error - {e}")

    except Exception as e:
        print(f"  ❌ Debug search error: {e}")


if __name__ == "__main__":
    debug_author_extraction()
