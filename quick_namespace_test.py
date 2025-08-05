#!/usr/bin/env python3
"""
Quick test to verify Enhanced parser namespace fix
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


def quick_namespace_test():
    """Quick test to verify namespace fix"""

    print("🔧 QUICK NAMESPACE FIX TEST")
    print("=" * 50)

    # Test file
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # First, let's check the raw XML for patient data
    root = ET.fromstring(xml_content)

    print("🔍 RAW XML CHECK:")

    # Check for patient with namespace
    patient_role = root.find(
        ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
    )
    if patient_role is not None:
        print("✅ Found patientRole with namespace")

        patient = patient_role.find("{urn:hl7-org:v3}patient")
        if patient is not None:
            name = patient.find("{urn:hl7-org:v3}name")
            if name is not None:
                given = name.find("{urn:hl7-org:v3}given")
                family = name.find("{urn:hl7-org:v3}family")
                print(f"   Given: {given.text if given is not None else 'Not found'}")
                print(
                    f"   Family: {family.text if family is not None else 'Not found'}"
                )
    else:
        print("❌ patientRole not found with namespace")

    # Now test the Enhanced parser
    print("\\n🧪 ENHANCED PARSER TEST:")
    parser = EnhancedCDAXMLParser()
    result = parser.parse_cda_content(xml_content)

    patient_identity = result.get("patient_identity", {})
    print(f"   Given Name: {patient_identity.get('given_name', 'N/A')}")
    print(f"   Family Name: {patient_identity.get('family_name', 'N/A')}")
    print(f"   Birth Date: {patient_identity.get('birth_date', 'N/A')}")
    print(f"   Patient ID: {patient_identity.get('patient_id', 'N/A')}")

    admin_data = result.get("administrative_data", {})
    print(f"\\n📋 Administrative Data:")
    print(f"   Document Title: {admin_data.get('document_title', 'N/A')}")
    print(f"   Creation Date: {admin_data.get('document_creation_date', 'N/A')}")
    print(f"   Document Type: {admin_data.get('document_type', 'N/A')}")
    print(f"   Custodian: {admin_data.get('custodian_name', 'N/A')}")

    # Assessment
    if patient_identity.get("given_name") != "Unknown":
        print("\\n🎉 SUCCESS: Namespace fix worked! Patient data extracted!")
    else:
        print("\\n❌ ISSUE: Still getting 'Unknown' - namespace issue persists")


if __name__ == "__main__":
    quick_namespace_test()
