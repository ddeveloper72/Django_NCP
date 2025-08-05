#!/usr/bin/env python3
"""
Debug patient ID extraction specifically
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


def debug_patient_id():
    """Debug patient ID extraction specifically"""

    print("🔍 PATIENT ID DEBUG TEST")
    print("=" * 50)

    # Test file from the current screenshot
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # Raw XML check
    print("🔍 RAW XML CHECK:")
    root = ET.fromstring(xml_content)

    # Check for patient role with namespace
    patient_role = root.find(
        ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
    )
    print(f"Patient Role found: {patient_role is not None}")

    if patient_role is not None:
        # Check for ID element
        patient_id_elem = patient_role.find("{urn:hl7-org:v3}id")
        print(f"Patient ID element found: {patient_id_elem is not None}")

        if patient_id_elem is not None:
            extension = patient_id_elem.get("extension")
            authority = patient_id_elem.get("assigningAuthorityName")
            root_val = patient_id_elem.get("root")
            print(f"Extension: {extension}")
            print(f"Authority: {authority}")
            print(f"Root: {root_val}")

        # Check patient name as well
        patient = patient_role.find("{urn:hl7-org:v3}patient")
        if patient is not None:
            name = patient.find("{urn:hl7-org:v3}name")
            if name is not None:
                given = name.find("{urn:hl7-org:v3}given")
                family = name.find("{urn:hl7-org:v3}family")
                print(f"Given name: {given.text if given is not None else 'None'}")
                print(f"Family name: {family.text if family is not None else 'None'}")

    print("\n🔧 ENHANCED PARSER TEST:")

    # Test with Enhanced parser
    parser = EnhancedCDAXMLParser()

    try:
        result = parser.parse_cda_file(test_file)
        print(f"Parse successful: {result is not None}")

        if result:
            patient_info = result.get("patient_info", {})
            print(f"Patient ID: {patient_info.get('patient_id')}")
            print(f"Given name: {patient_info.get('given_name')}")
            print(f"Family name: {patient_info.get('family_name')}")
            print(f"Birth date: {patient_info.get('birth_date')}")

            # Check the full result structure
            print(f"\nFull patient_info keys: {list(patient_info.keys())}")

    except Exception as e:
        print(f"❌ Parser error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_patient_id()
