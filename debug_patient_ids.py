#!/usr/bin/env python3
"""
Debug script to test patient identifier extraction
"""

import os
import sys
import xml.etree.ElementTree as ET

# Add the project path
sys.path.insert(0, os.path.dirname(__file__))

from patient_data.services import EUPatientSearchService


def test_patient_id_extraction():
    """Test patient ID extraction from Norbert Peters XML"""

    xml_file = "test_data/eu_member_states/LU/Norbert_Claude_Peters_25445576.xml"

    if not os.path.exists(xml_file):
        print(f"File not found: {xml_file}")
        return

    print("=== Testing Patient ID Extraction ===")
    print(f"File: {xml_file}")

    # Read and parse XML directly
    with open(xml_file, "r", encoding="utf-8") as f:
        content = f.read()

    root = ET.fromstring(content)
    namespaces = {"hl7": "urn:hl7-org:v3", "ext": "urn:hl7-EE-DL-Ext:v1"}

    # Find patient role
    patient_role = root.find(".//hl7:patientRole", namespaces)
    if patient_role is None:
        print("ERROR: Could not find patientRole element")
        return

    print("✓ Found patientRole element")

    # Extract patient IDs
    id_elements = patient_role.findall("hl7:id", namespaces)
    print(f"✓ Found {len(id_elements)} ID elements")

    for idx, id_elem in enumerate(id_elements):
        extension = id_elem.get("extension", "")
        root_attr = id_elem.get("root", "")
        print(f"  ID {idx + 1}: extension={extension}, root={root_attr}")

    # Test with the service
    print("\n=== Testing with EUPatientSearchService ===")
    service = EUPatientSearchService()

    # Parse using service method
    patient_data = {}
    try:
        # Find patient role using service namespaces
        patient_role = root.find(".//hl7:patientRole", service.namespaces)
        if patient_role is not None:
            print("✓ Service found patientRole")

            # Extract patient IDs using service logic
            id_elements = patient_role.findall("hl7:id", service.namespaces)
            patient_identifiers = []
            primary_patient_id = ""
            secondary_patient_id = ""

            for idx, id_elem in enumerate(id_elements):
                extension = id_elem.get("extension", "")
                root_attr = id_elem.get("root", "")

                if extension:
                    identifier_info = {
                        "extension": extension,
                        "root": root_attr,
                        "type": "primary" if idx == 0 else "secondary",
                    }
                    patient_identifiers.append(identifier_info)

                    if idx == 0:
                        primary_patient_id = extension
                    elif idx == 1:
                        secondary_patient_id = extension

            print(f"  Primary ID: {primary_patient_id}")
            print(f"  Secondary ID: {secondary_patient_id}")
            print(f"  All identifiers: {patient_identifiers}")
        else:
            print("ERROR: Service could not find patientRole")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    test_patient_id_extraction()
