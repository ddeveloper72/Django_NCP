#!/usr/bin/env python
"""
Debug Mario PINO patient identifier extraction
"""
import os
import sys
import django

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

import xml.etree.ElementTree as ET
from patient_data.models import PatientData


def debug_mario_pino_identifiers():
    """Debug Mario PINO patient identifier extraction from CDA"""
    print("=== Mario PINO CDA Identifier Debug ===")
    print()

    # Get Mario PINO from database
    mario_patients = PatientData.objects.filter(given_name="Mario", family_name="PINO")

    if not mario_patients.exists():
        print("❌ No Mario PINO patients found in database")
        return False

    mario = mario_patients.first()
    print(f"✅ Found Mario PINO (DB ID: {mario.id})")
    print(f"   Name: {mario.given_name} {mario.family_name}")
    print(f"   Birth Date: {mario.birth_date}")

    # Load the actual CDA file that was shown in the screenshot
    test_data_paths = [
        "test_data/eu_member_states/EU/Mario_Pino_NCPNPH80.xml",
        "test_data/eu_member_states/EU/Mario_Pino_NCPNPH80_1.xml",
        "test_data/eu_member_states/EU/Mario_Pino_NCPNPH80_2.xml",
        "test_data/eu_member_states/EU/Mario_Pino_NCPNPH80_3.xml",
        "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml",
    ]

    cda_content = None
    used_file = None

    for file_path in test_data_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                cda_content = f.read()
                used_file = file_path
                print(f"✅ Loaded CDA content from: {file_path}")
                break
        except FileNotFoundError:
            continue

    if not cda_content:
        print("❌ Could not find any Mario PINO CDA files")
        return False

    print(f"\n=== Extracting Patient Identifiers from CDA ===")
    print(f"File: {used_file}")

    try:
        # Parse the XML
        root = ET.fromstring(cda_content)
        namespaces = {
            "hl7": "urn:hl7-org:v3",
            "ext": "urn:hl7-EE-DL-Ext:v1",
        }

        print("\n🔍 Looking for patientRole...")
        patient_role = root.find(".//hl7:patientRole", namespaces)
        if patient_role is None:
            print("❌ No patientRole found")
            return False

        print("✅ Found patientRole")

        print("\n🔍 Looking for id elements...")
        id_elements = patient_role.findall("hl7:id", namespaces)
        print(f"✅ Found {len(id_elements)} id elements")

        patient_identifiers = []

        for idx, id_elem in enumerate(id_elements):
            extension = id_elem.get("extension", "")
            root_attr = id_elem.get("root", "")
            assigning_authority = id_elem.get("assigningAuthorityName", "")
            displayable = id_elem.get("displayable", "")

            print(f"\n--- ID Element {idx + 1} ---")
            print(f"extension: '{extension}'")
            print(f"root: '{root_attr}'")
            print(f"assigningAuthorityName: '{assigning_authority}'")
            print(f"displayable: '{displayable}'")

            if extension:
                identifier_info = {
                    "extension": extension,
                    "root": root_attr,
                    "assigningAuthorityName": assigning_authority,
                    "displayable": displayable,
                    "type": "primary" if idx == 0 else "secondary",
                }
                patient_identifiers.append(identifier_info)

                print(f"✅ Added to patient_identifiers array")
            else:
                print(f"⚠️  Skipped (no extension)")

        print(f"\n=== Final Results ===")
        print(f"Total valid identifiers: {len(patient_identifiers)}")

        if patient_identifiers:
            print("\n📋 Patient Identifiers Array:")
            for i, identifier in enumerate(patient_identifiers):
                print(f"  [{i}] {identifier}")

            print("\n🎯 Template Display Logic Test:")
            for identifier in patient_identifiers:
                if identifier.get("assigningAuthorityName"):
                    display_text = f"{identifier['assigningAuthorityName']}: {identifier['extension']}"
                    print(f"  ✅ {display_text}")
                elif identifier.get("root"):
                    display_text = (
                        f"ID ({identifier['root'][:15]}...): {identifier['extension']}"
                    )
                    print(f"  ✅ {display_text}")
                else:
                    print(f"  ⚠️  {identifier['extension']}")
        else:
            print("❌ No valid patient identifiers found!")

        return len(patient_identifiers) > 0

    except ET.ParseError as e:
        print(f"❌ XML Parse Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = debug_mario_pino_identifiers()
    if success:
        print("\n🎉 Patient identifiers should be displaying correctly!")
        print("   If they're not, the issue is in the session data storage/retrieval.")
    else:
        print("\n⚠️  Issue with CDA identifier extraction logic")
