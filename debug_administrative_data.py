#!/usr/bin/env python3
"""
Administrative Data Extraction Test
Test comprehensive extraction of administrative and contact data from CDA
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

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def test_administrative_extraction():
    """Test comprehensive administrative data extraction"""

    print("🔍 ADMINISTRATIVE DATA EXTRACTION TEST")
    print("=" * 50)

    # Test file from the current screenshot
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        # Try to find any IT file
        it_folder = Path("test_data/eu_member_states/IT")
        if it_folder.exists():
            xml_files = list(it_folder.glob("*.xml"))
            if xml_files:
                test_file = xml_files[0]
                print(f"🔄 Using alternative file: {test_file}")
            else:
                print("❌ No XML files found in IT folder")
                return
        else:
            print("❌ IT folder not found")
            return

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    print("🔍 ANALYZING XML STRUCTURE FOR ADMINISTRATIVE DATA:")
    root = ET.fromstring(xml_content)

    # 1. Patient Contact Information
    print("\n1. PATIENT CONTACT INFORMATION:")
    patient_role = root.find(
        ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
    )

    if patient_role is not None:
        # Addresses
        addresses = patient_role.findall("{urn:hl7-org:v3}addr")
        print(f"   Found {len(addresses)} patient addresses:")
        for i, addr in enumerate(addresses):
            use = addr.get("use", "unknown")
            country = addr.find("{urn:hl7-org:v3}country")
            state = addr.find("{urn:hl7-org:v3}state")
            city = addr.find("{urn:hl7-org:v3}city")
            postal = addr.find("{urn:hl7-org:v3}postalCode")
            street = addr.find("{urn:hl7-org:v3}streetAddressLine")

            print(f"     Address {i+1} ({use}):")
            if street is not None:
                print(f"       Street: {street.text}")
            if city is not None:
                print(f"       City: {city.text}")
            if state is not None:
                print(f"       State: {state.text}")
            if postal is not None:
                print(f"       Postal: {postal.text}")
            if country is not None:
                print(f"       Country: {country.text}")

        # Telecoms (phone, email)
        telecoms = patient_role.findall("{urn:hl7-org:v3}telecom")
        print(f"   Found {len(telecoms)} patient telecoms:")
        for i, telecom in enumerate(telecoms):
            use = telecom.get("use", "unknown")
            value = telecom.get("value", "")
            print(f"     Telecom {i+1} ({use}): {value}")

    # 2. Custodian Organization Details
    print("\n2. CUSTODIAN ORGANIZATION:")
    custodian = root.find(".//{urn:hl7-org:v3}custodian")
    if custodian is not None:
        org = custodian.find(".//{urn:hl7-org:v3}representedCustodianOrganization")
        if org is not None:
            # Organization ID
            org_id = org.find("{urn:hl7-org:v3}id")
            if org_id is not None:
                print(
                    f"   Organization ID: {org_id.get('extension', 'N/A')} (Root: {org_id.get('root', 'N/A')})"
                )

            # Organization Name
            org_name = org.find("{urn:hl7-org:v3}name")
            if org_name is not None:
                print(f"   Organization Name: {org_name.text}")

            # Organization Address
            org_addr = org.find("{urn:hl7-org:v3}addr")
            if org_addr is not None:
                country = org_addr.find("{urn:hl7-org:v3}country")
                state = org_addr.find("{urn:hl7-org:v3}state")
                print(f"   Organization Address:")
                if country is not None:
                    print(f"     Country: {country.text}")
                if state is not None:
                    print(f"     State: {state.text}")

            # Organization Telecom
            org_telecom = org.find("{urn:hl7-org:v3}telecom")
            if org_telecom is not None:
                use = org_telecom.get("use", "unknown")
                value = org_telecom.get("value", "")
                print(f"   Organization Telecom ({use}): {value}")

    # 3. Author Information
    print("\n3. AUTHOR INFORMATION:")
    authors = root.findall(".//{urn:hl7-org:v3}author")
    print(f"   Found {len(authors)} authors:")
    for i, author in enumerate(authors):
        # Author time
        time_elem = author.find("{urn:hl7-org:v3}time")
        if time_elem is not None:
            print(f"     Author {i+1} Time: {time_elem.get('value', 'N/A')}")

        # Assigned Author
        assigned_author = author.find("{urn:hl7-org:v3}assignedAuthor")
        if assigned_author is not None:
            # Author ID
            author_id = assigned_author.find("{urn:hl7-org:v3}id")
            if author_id is not None:
                print(f"     Author ID: {author_id.get('extension', 'N/A')}")

            # Author Code
            author_code = assigned_author.find("{urn:hl7-org:v3}code")
            if author_code is not None:
                print(
                    f"     Author Code: {author_code.get('code', 'N/A')} ({author_code.get('displayName', 'N/A')})"
                )

            # Author Address
            author_addr = assigned_author.find("{urn:hl7-org:v3}addr")
            if author_addr is not None:
                country = author_addr.find("{urn:hl7-org:v3}country")
                if country is not None:
                    print(f"     Author Country: {country.text}")

            # Author Telecom
            author_telecom = assigned_author.find("{urn:hl7-org:v3}telecom")
            if author_telecom is not None:
                use = author_telecom.get("use", "unknown")
                value = author_telecom.get("value", "")
                print(f"     Author Telecom ({use}): {value}")

            # Assigned Person
            assigned_person = assigned_author.find("{urn:hl7-org:v3}assignedPerson")
            if assigned_person is not None:
                name = assigned_person.find("{urn:hl7-org:v3}name")
                if name is not None:
                    family = name.find("{urn:hl7-org:v3}family")
                    given = name.find("{urn:hl7-org:v3}given")
                    if family is not None:
                        print(f"     Author Family: {family.text}")
                    if given is not None:
                        print(f"     Author Given: {given.text}")

            # Represented Organization
            org = assigned_author.find("{urn:hl7-org:v3}representedOrganization")
            if org is not None:
                org_name = org.find("{urn:hl7-org:v3}name")
                if org_name is not None:
                    print(f"     Author Organization: {org_name.text}")

    # 4. Legal Authenticator
    print("\n4. LEGAL AUTHENTICATOR:")
    legal_auth = root.find(".//{urn:hl7-org:v3}legalAuthenticator")
    if legal_auth is not None:
        # Time
        time_elem = legal_auth.find("{urn:hl7-org:v3}time")
        if time_elem is not None:
            print(f"   Authentication Time: {time_elem.get('value', 'N/A')}")

        # Signature Code
        sig_code = legal_auth.find("{urn:hl7-org:v3}signatureCode")
        if sig_code is not None:
            print(f"   Signature Code: {sig_code.get('code', 'N/A')}")

        # Assigned Entity
        assigned_entity = legal_auth.find("{urn:hl7-org:v3}assignedEntity")
        if assigned_entity is not None:
            # Entity ID
            entity_id = assigned_entity.find("{urn:hl7-org:v3}id")
            if entity_id is not None:
                print(f"   Authenticator ID: {entity_id.get('extension', 'N/A')}")

            # Assigned Person
            assigned_person = assigned_entity.find("{urn:hl7-org:v3}assignedPerson")
            if assigned_person is not None:
                name = assigned_person.find("{urn:hl7-org:v3}name")
                if name is not None:
                    family = name.find("{urn:hl7-org:v3}family")
                    given = name.find("{urn:hl7-org:v3}given")
                    if family is not None:
                        print(f"   Authenticator Family: {family.text}")
                    if given is not None:
                        print(f"   Authenticator Given: {given.text}")

    print("\n🔧 CURRENT ENHANCED PARSER OUTPUT:")

    # Test with current Enhanced parser
    parser = EnhancedCDAXMLParser()

    try:
        result = parser.parse_cda_file(test_file)
        if result:
            admin_data = result.get("administrative_data", {})
            print("Current administrative data keys:")
            for key, value in admin_data.items():
                print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Parser error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_administrative_extraction()
