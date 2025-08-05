#!/usr/bin/env python3
"""
Focused Administrative Data Extraction Analysis
Compare current parser output vs. raw XML structure to identify gaps
"""

import os
import sys
import django
from pathlib import Path
import xml.etree.ElementTree as ET
import json

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def analyze_single_file_detailed():
    """Detailed analysis of a single file to understand extraction gaps"""

    print("🔍 DETAILED ADMINISTRATIVE EXTRACTION ANALYSIS")
    print("=" * 60)

    # Use Italian file as example
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    print(f"📄 Analyzing: {test_file.name}")

    # 1. Parse with current parser
    print("\n🔧 CURRENT PARSER OUTPUT:")
    parser = EnhancedCDAXMLParser()

    try:
        result = parser.parse_cda_content(xml_content)
        admin_info = result.get("administrative_info", {})

        print(f"Administrative sections found: {len(admin_info)}")
        for section, data in admin_info.items():
            if isinstance(data, list):
                print(f"  {section}: {len(data)} items")
                if data:
                    print(
                        f"    First item keys: {list(data[0].keys()) if data[0] else 'Empty'}"
                    )
            elif isinstance(data, dict):
                print(f"  {section}: {len(data)} fields")
                print(f"    Keys: {list(data.keys())}")
            else:
                print(f"  {section}: {type(data)} - {data}")

    except Exception as e:
        print(f"❌ Parser error: {e}")
        import traceback

        traceback.print_exc()
        return

    # 2. Analyze raw XML structure
    print(f"\n🔍 RAW XML STRUCTURE ANALYSIS:")
    root = ET.fromstring(xml_content)

    # Patient/RecordTarget
    print(f"\n👤 PATIENT (recordTarget):")
    record_targets = root.findall(".//{urn:hl7-org:v3}recordTarget")
    print(f"  Found {len(record_targets)} recordTarget elements")

    if record_targets:
        patient_role = record_targets[0].find("{urn:hl7-org:v3}patientRole")
        if patient_role is not None:
            # Patient ID
            id_elem = patient_role.find("{urn:hl7-org:v3}id")
            if id_elem is not None:
                print(
                    f"  Patient ID: {id_elem.get('extension')} (root: {id_elem.get('root')})"
                )

            # Patient addresses
            addresses = patient_role.findall("{urn:hl7-org:v3}addr")
            print(f"  Addresses: {len(addresses)}")
            if addresses:
                analyze_address_structure(addresses[0], "    ")

            # Patient telecoms
            telecoms = patient_role.findall("{urn:hl7-org:v3}telecom")
            print(f"  Telecoms: {len(telecoms)}")
            for i, telecom in enumerate(telecoms):
                print(
                    f"    {i+1}: {telecom.get('value')} (use: {telecom.get('use', 'N/A')})"
                )

            # Patient info
            patient = patient_role.find("{urn:hl7-org:v3}patient")
            if patient is not None:
                names = patient.findall("{urn:hl7-org:v3}name")
                if names:
                    analyze_name_structure(names[0], "    ")

                birth_time = patient.find("{urn:hl7-org:v3}birthTime")
                if birth_time is not None:
                    print(f"    Birth date: {birth_time.get('value')}")

                gender = patient.find("{urn:hl7-org:v3}administrativeGenderCode")
                if gender is not None:
                    print(
                        f"    Gender: {gender.get('code')} ({gender.get('displayName', 'N/A')})"
                    )

    # Legal Authenticator
    print(f"\n⚖️ LEGAL AUTHENTICATOR:")
    legal_auths = root.findall(".//{urn:hl7-org:v3}legalAuthenticator")
    print(f"  Found {len(legal_auths)} legalAuthenticator elements")

    if legal_auths:
        legal_auth = legal_auths[0]

        # Signature code
        sig_code = legal_auth.find("{urn:hl7-org:v3}signatureCode")
        if sig_code is not None:
            print(f"  Signature code: {sig_code.get('code')}")

        # Time
        time_elem = legal_auth.find("{urn:hl7-org:v3}time")
        if time_elem is not None:
            print(f"  Time: {time_elem.get('value')}")

        # Assigned entity
        assigned_entity = legal_auth.find("{urn:hl7-org:v3}assignedEntity")
        if assigned_entity is not None:
            analyze_assigned_entity(assigned_entity, "    Legal Auth")

    # Custodian
    print(f"\n🏛️ CUSTODIAN:")
    custodians = root.findall(".//{urn:hl7-org:v3}custodian")
    print(f"  Found {len(custodians)} custodian elements")

    if custodians:
        custodian = custodians[0]
        assigned_custodian = custodian.find("{urn:hl7-org:v3}assignedCustodian")
        if assigned_custodian is not None:
            rep_org = assigned_custodian.find(
                "{urn:hl7-org:v3}representedCustodianOrganization"
            )
            if rep_org is not None:
                analyze_organization(rep_org, "    Custodian")

    # Authors
    print(f"\n✍️ AUTHORS:")
    authors = root.findall(".//{urn:hl7-org:v3}author")
    print(f"  Found {len(authors)} author elements")

    for i, author in enumerate(authors[:3]):  # Show first 3
        print(f"  Author {i+1}:")

        time_elem = author.find("{urn:hl7-org:v3}time")
        if time_elem is not None:
            print(f"    Time: {time_elem.get('value')}")

        assigned_author = author.find("{urn:hl7-org:v3}assignedAuthor")
        if assigned_author is not None:
            analyze_assigned_entity(assigned_author, f"    Author {i+1}")

    # 3. Compare parser vs XML
    print(f"\n🔄 PARSER VS XML COMPARISON:")
    print("=" * 40)

    # Compare patient data
    patient_info = result.get("patient_info", {})
    print(f"Patient comparison:")
    print(f"  Parser ID: {patient_info.get('patient_id', 'Missing')}")
    print(
        f"  Parser Name: {patient_info.get('given_name', '')} {patient_info.get('family_name', '')}"
    )
    print(f"  Parser Birth: {patient_info.get('birth_date', 'Missing')}")

    # Compare administrative
    print(f"Administrative comparison:")
    print(
        f"  Legal Auth (parser): {'Found' if admin_info.get('legal_authenticator') else 'Missing'}"
    )
    print(f"  Legal Auth (XML): {'Found' if legal_auths else 'Missing'}")
    print(
        f"  Custodian (parser): {'Found' if admin_info.get('custodian') else 'Missing'}"
    )
    print(f"  Custodian (XML): {'Found' if custodians else 'Missing'}")
    print(f"  Authors (parser): {len(admin_info.get('authors', []))}")
    print(f"  Authors (XML): {len(authors)}")


def analyze_address_structure(addr_elem, prefix=""):
    """Analyze address element structure"""
    print(f"{prefix}Address components:")
    for child in addr_elem:
        local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        value = child.text if child.text else ""
        print(f"{prefix}  {local_name}: '{value}'")


def analyze_name_structure(name_elem, prefix=""):
    """Analyze name element structure"""
    print(f"{prefix}Name components:")
    for child in name_elem:
        local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        value = child.text if child.text else ""
        print(f"{prefix}  {local_name}: '{value}'")


def analyze_assigned_entity(entity_elem, prefix=""):
    """Analyze assignedEntity/assignedAuthor structure"""
    print(f"{prefix} Entity:")

    # IDs
    id_elems = entity_elem.findall("{urn:hl7-org:v3}id")
    print(f"{prefix}   IDs: {len(id_elems)}")
    for i, id_elem in enumerate(id_elems):
        print(
            f"{prefix}     {i+1}: {id_elem.get('extension', 'N/A')} (root: {id_elem.get('root', 'N/A')})"
        )

    # Addresses
    addresses = entity_elem.findall("{urn:hl7-org:v3}addr")
    print(f"{prefix}   Addresses: {len(addresses)}")
    if addresses:
        analyze_address_structure(addresses[0], f"{prefix}     ")

    # Telecoms
    telecoms = entity_elem.findall("{urn:hl7-org:v3}telecom")
    print(f"{prefix}   Telecoms: {len(telecoms)}")
    for i, telecom in enumerate(telecoms):
        print(
            f"{prefix}     {i+1}: {telecom.get('value')} (use: {telecom.get('use', 'N/A')})"
        )

    # Person
    assigned_person = entity_elem.find("{urn:hl7-org:v3}assignedPerson")
    if assigned_person is not None:
        print(f"{prefix}   Person found")
        names = assigned_person.findall("{urn:hl7-org:v3}name")
        if names:
            analyze_name_structure(names[0], f"{prefix}     ")

    # Organization
    rep_org = entity_elem.find("{urn:hl7-org:v3}representedOrganization")
    if rep_org is not None:
        analyze_organization(rep_org, f"{prefix}   Org")


def analyze_organization(org_elem, prefix=""):
    """Analyze organization structure"""
    print(f"{prefix}:")

    # IDs
    id_elems = org_elem.findall("{urn:hl7-org:v3}id")
    print(f"{prefix}   IDs: {len(id_elems)}")
    for i, id_elem in enumerate(id_elems):
        print(
            f"{prefix}     {i+1}: {id_elem.get('extension', 'N/A')} (root: {id_elem.get('root', 'N/A')})"
        )

    # Name
    names = org_elem.findall("{urn:hl7-org:v3}name")
    print(f"{prefix}   Names: {len(names)}")
    for i, name in enumerate(names):
        print(f"{prefix}     {i+1}: '{name.text if name.text else 'Empty'}'")

    # Addresses
    addresses = org_elem.findall("{urn:hl7-org:v3}addr")
    print(f"{prefix}   Addresses: {len(addresses)}")
    if addresses:
        analyze_address_structure(addresses[0], f"{prefix}     ")

    # Telecoms
    telecoms = org_elem.findall("{urn:hl7-org:v3}telecom")
    print(f"{prefix}   Telecoms: {len(telecoms)}")
    for i, telecom in enumerate(telecoms):
        print(
            f"{prefix}     {i+1}: {telecom.get('value')} (use: {telecom.get('use', 'N/A')})"
        )


if __name__ == "__main__":
    analyze_single_file_detailed()
