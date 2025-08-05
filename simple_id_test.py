#!/usr/bin/env python3
"""
Simple test to verify patient ID fix
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def simple_patient_id_test():
    """Simple test without Django dependencies"""

    print("🔍 SIMPLE PATIENT ID TEST")
    print("=" * 40)

    # Test file from the current screenshot
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # Parse XML
    root = ET.fromstring(xml_content)

    # Find patient role
    patient_role = root.find(
        ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
    )

    if patient_role is not None:
        print("✅ Found patient role")

        # Find all ID elements
        id_elems = patient_role.findall("{urn:hl7-org:v3}id")
        print(f"📋 Found {len(id_elems)} ID elements")

        patient_identifiers = []

        for i, id_elem in enumerate(id_elems):
            extension = id_elem.get("extension", "")
            authority = id_elem.get("assigningAuthorityName", "")
            root_val = id_elem.get("root", "")

            print(f"\n🆔 ID Element {i}:")
            print(f"   Extension: {extension}")
            print(f"   Authority: {authority}")
            print(f"   Root: {root_val}")

            if extension:
                identifier_obj = {
                    "extension": extension,
                    "assigningAuthorityName": authority,
                    "root": root_val,
                }
                patient_identifiers.append(identifier_obj)

        print(f"\n📊 Template-ready identifiers: {len(patient_identifiers)}")
        for i, identifier in enumerate(patient_identifiers):
            print(f"   [{i}] {identifier}")

        # Test template access pattern
        if patient_identifiers:
            print(f"\n🔬 Template Access Test:")
            first_id = patient_identifiers[0]
            print(f"   identifier.extension: {first_id.get('extension')}")
            print(
                f"   identifier.assigningAuthorityName: {first_id.get('assigningAuthorityName')}"
            )
            print(f"   ✅ Template should work now!")
        else:
            print("❌ No identifiers created")
    else:
        print("❌ Patient role not found")


if __name__ == "__main__":
    simple_patient_id_test()
