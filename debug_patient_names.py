#!/usr/bin/env python3
"""
Debug patient name extraction specifically across multiple files.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from patient_data.utils.administrative_extractor import EnhancedAdministrativeExtractor


def debug_patient_names():
    """Debug patient name extraction across EU files."""

    print("🔍 DEBUGGING PATIENT NAME EXTRACTION")
    print("=" * 50)

    # Test a few files from different countries
    test_files = [
        "test_data/eu_member_states/BE/3-1234-W7.xml",
        "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml",
        "test_data/eu_member_states/LU/Norbert_Claude_Peters_25445576_5.xml",
    ]

    extractor = EnhancedAdministrativeExtractor()

    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue

        print(f"\n📄 Testing: {os.path.basename(file_path)}")
        print("-" * 40)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Check raw XML for patient data
            print("🔍 RAW XML PATIENT SEARCH:")

            # Look for recordTarget
            record_targets = root.findall(".//{urn:hl7-org:v3}recordTarget")
            print(f"  recordTarget elements: {len(record_targets)}")

            for rt in record_targets:
                patient_role = rt.find(".//{urn:hl7-org:v3}patientRole")
                if patient_role is not None:
                    print("  patientRole found:")

                    # Check for ID
                    ids = patient_role.findall(".//{urn:hl7-org:v3}id")
                    for id_elem in ids:
                        print(
                            f"    ID: {id_elem.get('extension', 'N/A')} (root: {id_elem.get('root', 'N/A')})"
                        )

                    # Check for patient names
                    patient = patient_role.find(".//{urn:hl7-org:v3}patient")
                    if patient is not None:
                        print("  patient element found:")
                        names = patient.findall(".//{urn:hl7-org:v3}name")
                        print(f"    name elements: {len(names)}")

                        for name in names:
                            given = name.find(".//{urn:hl7-org:v3}given")
                            family = name.find(".//{urn:hl7-org:v3}family")
                            print(f"    Name parts:")
                            print(
                                f"      Given: {given.text if given is not None else 'N/A'}"
                            )
                            print(
                                f"      Family: {family.text if family is not None else 'N/A'}"
                            )

            # Test our extractor
            print("\n🧪 EXTRACTOR TEST:")
            patient_info = extractor.extract_patient_contact_info(root)
            print(f"  Extracted name: {patient_info.get('name', 'N/A')}")
            print(f"  Extracted given: {patient_info.get('given_name', 'N/A')}")
            print(f"  Extracted family: {patient_info.get('family_name', 'N/A')}")
            print(f"  Extracted ID: {patient_info.get('patient_id', 'N/A')}")
            print(f"  Extracted birth date: {patient_info.get('birth_date', 'N/A')}")

        except Exception as e:
            print(f"❌ Error processing file: {str(e)}")

    print("\n✅ Patient name debugging completed!")


if __name__ == "__main__":
    debug_patient_names()
