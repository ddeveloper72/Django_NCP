#!/usr/bin/env python3
"""
Check XML namespace structure for field mapping
"""

import xml.etree.ElementTree as ET

# Load the Portuguese CDA
with open("test_data/eu_member_states/PT/2-1234-W7.xml", "r", encoding="utf-8") as f:
    content = f.read()

root = ET.fromstring(content)

print("XML Structure Analysis:")
print("=" * 50)
print(f"Root tag: {root.tag}")
print(f"Root attributes: {root.attrib}")

# Check namespace
if root.tag.startswith("{"):
    namespace = root.tag.split("}")[0] + "}"
    print(f"Namespace: {namespace}")
else:
    namespace = ""
    print("No namespace found")

namespaces = {"hl7": "urn:hl7-org:v3"}

# Test patient data extraction with proper namespaces
print(f"\nPatient Data Extraction Test:")
print("=" * 30)

# Record Target
record_target = root.find(".//hl7:recordTarget", namespaces)
if record_target is not None:
    print("✅ Found recordTarget")

    # Patient Role
    patient_role = record_target.find("hl7:patientRole", namespaces)
    if patient_role is not None:
        print("✅ Found patientRole")

        # Patient IDs
        ids = patient_role.findall("hl7:id", namespaces)
        print(f"✅ Found {len(ids)} patient IDs")
        for i, id_elem in enumerate(ids):
            extension = id_elem.get("extension")
            root_attr = id_elem.get("root")
            print(f"   ID {i+1}: {extension} (root: {root_attr})")

        # Patient
        patient = patient_role.find("hl7:patient", namespaces)
        if patient is not None:
            print("✅ Found patient")

            # Name
            name = patient.find("hl7:name", namespaces)
            if name is not None:
                given = name.find("hl7:given", namespaces)
                family = name.find("hl7:family", namespaces)
                prefix = name.find("hl7:prefix", namespaces)

                print(f"   Given: {given.text if given is not None else 'Not found'}")
                print(
                    f"   Family: {family.text if family is not None else 'Not found'}"
                )
                print(
                    f"   Prefix: {prefix.text if prefix is not None else 'Not found'}"
                )

            # Gender
            gender = patient.find("hl7:administrativeGenderCode", namespaces)
            if gender is not None:
                print(f"   Gender: {gender.get('code')}")

            # Birthdate
            birthtime = patient.find("hl7:birthTime", namespaces)
            if birthtime is not None:
                print(f"   Birthdate: {birthtime.get('value')}")

print(f"\nXPath Pattern Analysis:")
print("=" * 25)
print("JSON XPath: /ClinicalDocument/recordTarget/patientRole/patient/name/given")
print("Required:   .//hl7:recordTarget/hl7:patientRole/hl7:patient/hl7:name/hl7:given")
print("Issue: JSON patterns lack namespace prefixes!")
