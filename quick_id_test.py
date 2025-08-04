#!/usr/bin/env python3
"""
Quick test for patient identifier extraction
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from xml.etree import ElementTree as ET


def test_simple_extraction():
    """Test identifier extraction from sample CDA"""

    # Read the sample CDA
    with open("patient_data/test_data/sample_cda_document.xml", "r") as f:
        cda_content = f.read()

    print("Testing CDA patient identifier extraction...")

    # Parse XML
    root = ET.fromstring(cda_content)

    # Look for HL7 namespace
    namespaces = {"hl7": "urn:hl7-org:v3"}

    # Find patient IDs
    patient_ids = root.findall(".//hl7:recordTarget/hl7:patientRole/hl7:id", namespaces)

    print(f"Found {len(patient_ids)} patient ID elements:")

    for id_elem in patient_ids:
        extension = id_elem.get("extension", "N/A")
        root_attr = id_elem.get("root", "N/A")
        print(f"  - Extension: {extension}")
        print(f"    Root: {root_attr}")
        print()


if __name__ == "__main__":
    test_simple_extraction()
