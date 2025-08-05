#!/usr/bin/env python3
"""
Test the patient ID structure fix
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


def test_patient_id_structure():
    """Test that patient identifiers have correct structure for template"""

    print("🔍 PATIENT ID STRUCTURE TEST")
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

    # Raw XML check first
    print("🔍 RAW XML CHECK:")
    root = ET.fromstring(xml_content)

    patient_role = root.find(
        ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
    )
    if patient_role is not None:
        patient_id_elem = patient_role.find("{urn:hl7-org:v3}id")
        if patient_id_elem is not None:
            extension = patient_id_elem.get("extension")
            authority = patient_id_elem.get("assigningAuthorityName")
            root_val = patient_id_elem.get("root")
            print(f"✅ Found patient ID: {extension}")
            print(f"   Authority: {authority}")
            print(f"   Root: {root_val}")

    print("\n🔧 ENHANCED PARSER TEST:")

    # Test with Enhanced parser
    parser = EnhancedCDAXMLParser()

    try:
        result = parser.parse_cda_file(test_file)
        print(f"✅ Parse successful: {result is not None}")

        if result:
            # Check patient_identity (this is what gets passed to template)
            patient_identity = result.get("patient_identity", {})
            print(f"\n📋 Patient Identity Structure:")
            print(f"   Keys: {list(patient_identity.keys())}")
            print(f"   Given name: {patient_identity.get('given_name')}")
            print(f"   Family name: {patient_identity.get('family_name')}")
            print(f"   Patient ID: {patient_identity.get('patient_id')}")

            # Check patient identifiers structure (critical for template)
            identifiers = patient_identity.get("patient_identifiers", [])
            print(f"\n🆔 Patient Identifiers:")
            print(f"   Count: {len(identifiers)}")

            for i, identifier in enumerate(identifiers):
                print(f"   Identifier {i}: {type(identifier).__name__}")
                if isinstance(identifier, dict):
                    print(f"      Extension: {identifier.get('extension')}")
                    print(
                        f"      Authority: {identifier.get('assigningAuthorityName')}"
                    )
                    print(f"      Root: {identifier.get('root')}")
                    print(f"      ✅ Correct structure for template")
                else:
                    print(f"      Value: {identifier}")
                    print(
                        f"      ❌ Wrong structure - should be dict with 'extension' key"
                    )

    except Exception as e:
        print(f"❌ Parser error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_patient_id_structure()
