#!/usr/bin/env python3
"""
Test enhanced patient identifier extraction with assigningAuthorityName
"""
import os
import sys
import django
from xml.etree import ElementTree as ET

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")


def test_enhanced_extraction_with_authority():
    """Test the enhanced extraction with Italian CDA"""

    italian_cda = "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    with open(italian_cda, "r", encoding="utf-8") as f:
        cda_content = f.read()

    print("Testing enhanced patient identifier extraction...")
    print("=" * 60)

    # Parse the CDA manually to simulate our enhanced extraction
    root = ET.fromstring(cda_content)
    namespaces = {"hl7": "urn:hl7-org:v3"}

    # Find patient role
    patient_role = root.find(".//hl7:recordTarget/hl7:patientRole", namespaces)

    if patient_role is not None:
        id_elements = patient_role.findall("hl7:id", namespaces)
        patient_identifiers = []

        for idx, id_elem in enumerate(id_elements):
            extension = id_elem.get("extension", "")
            root_attr = id_elem.get("root", "")
            assigning_authority = id_elem.get("assigningAuthorityName", "")
            displayable = id_elem.get("displayable", "")

            if extension:
                identifier_info = {
                    "extension": extension,
                    "root": root_attr,
                    "assigningAuthorityName": assigning_authority,
                    "displayable": displayable,
                    "type": "primary" if idx == 0 else "secondary",
                }
                patient_identifiers.append(identifier_info)

        print(f"Found {len(patient_identifiers)} patient identifiers:")

        for i, identifier in enumerate(patient_identifiers, 1):
            print(f"  {i}. Extension: {identifier['extension']}")
            print(f"     Root: {identifier['root']}")
            print(f"     Assigning Authority: {identifier['assigningAuthorityName']}")
            print(f"     Displayable: {identifier['displayable']}")
            print(f"     Type: {identifier['type']}")
            print()

        # Test template display formats
        print("Template banner display:")
        for identifier in patient_identifiers:
            if identifier["assigningAuthorityName"]:
                print(
                    f"  {identifier['assigningAuthorityName']}: {identifier['extension']}"
                )
            else:
                print(f"  ID: {identifier['extension']}")

        print("\nTemplate info section display:")
        for identifier in patient_identifiers:
            if identifier["assigningAuthorityName"]:
                label = f"Patient ID ({identifier['assigningAuthorityName']})"
            elif identifier["root"]:
                label = f"Patient ID ({identifier['root']})"
            else:
                label = "Patient ID"
            print(f"  {label}: {identifier['extension']}")


if __name__ == "__main__":
    test_enhanced_extraction_with_authority()
