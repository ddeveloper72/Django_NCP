#!/usr/bin/env python3
"""
Test Luxembourg patient identifier display with both IDs: 2544557646 and 193701011247
"""
from xml.etree import ElementTree as ET


def test_luxembourg_patient_ids():
    """Test with simulated Luxembourg CDA structure"""

    # Create a simulated Luxembourg CDA structure based on the tree view
    lu_cda_content = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="EU"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="1.3.6.1.4.1.12559.11.10.1.3.1.1.3"/>
    
    <id extension="12345" root="1.2.3.4.5.6.7.8.9"/>
    <code code="60591-5" codeSystem="2.16.840.1.113883.6.1" displayName="Patient Summary"/>
    <title>CR de séjours hospitaliers et lettres de sorties 2023-11-01</title>
    <languageCode code="fr-LU"/>
    
    <recordTarget>
        <patientRole>
            <id extension="2544557646" root="1.3.182.2.4.2"/>
            <id extension="193701011247" root="1.3.182.4.4"/>
            <patient>
                <name use="L">
                    <given>Test</given>
                    <family>Patient</family>
                </name>
                <administrativeGenderCode code="M" displayName="Male"/>
                <birthTime value="19700301"/>
            </patient>
        </patientRole>
    </recordTarget>
</ClinicalDocument>"""

    print("Testing Luxembourg patient identifier extraction...")
    print("=" * 60)

    # Parse the CDA
    root = ET.fromstring(lu_cda_content)
    namespaces = {"hl7": "urn:hl7-org:v3"}

    # Find patient role
    patient_role = root.find(".//hl7:recordTarget/hl7:patientRole", namespaces)

    if patient_role is not None:
        id_elements = patient_role.findall("hl7:id", namespaces)
        patient_identifiers = []

        for idx, id_elem in enumerate(id_elements):
            extension = id_elem.get("extension", "")
            root_attr = id_elem.get("root", "")
            assigning_authority = id_elem.get("assigningAuthorityName", "")
            displayable = id_elem.get("displayable", "")

            if extension:
                identifier_info = {
                    "extension": extension,
                    "root": root_attr,
                    "assigningAuthorityName": assigning_authority,
                    "displayable": displayable,
                    "type": "primary" if idx == 0 else "secondary",
                }
                patient_identifiers.append(identifier_info)

        print(f"Found {len(patient_identifiers)} Luxembourg patient identifiers:")

        for i, identifier in enumerate(patient_identifiers, 1):
            print(f"  {i}. Extension: {identifier['extension']}")
            print(f"     Root: {identifier['root']}")
            print(
                f"     Assigning Authority: {identifier['assigningAuthorityName'] or 'N/A'}"
            )
            print(f"     Type: {identifier['type']}")
            print()

        # Test both search IDs
        search_ids = ["2544557646", "193701011247"]
        for search_id in search_ids:
            found = any(
                identifier["extension"] == search_id
                for identifier in patient_identifiers
            )
            print(f"Search ID '{search_id}' found: {found}")

        print("\n" + "=" * 60)
        print("ENHANCED TEMPLATE BANNER DISPLAY:")
        print("=" * 60)
        for i, identifier in enumerate(patient_identifiers, 1):
            css_class = "primary" if i == 1 else "secondary" if i == 2 else "additional"
            if identifier["assigningAuthorityName"]:
                display = (
                    f"{identifier['assigningAuthorityName']}: {identifier['extension']}"
                )
            else:
                root_truncated = (
                    identifier["root"][:15] + "..."
                    if len(identifier["root"]) > 15
                    else identifier["root"]
                )
                display = f"ID ({root_truncated}): {identifier['extension']}"

            print(f'  <span class="patient-id-{css_class}">{display}</span>')

        print("\n" + "=" * 60)
        print("ENHANCED TEMPLATE INFO SECTION DISPLAY:")
        print("=" * 60)
        for identifier in patient_identifiers:
            if identifier["assigningAuthorityName"]:
                label = f"Patient ID ({identifier['assigningAuthorityName']})"
            else:
                root_truncated = (
                    identifier["root"][:20] + "..."
                    if len(identifier["root"]) > 20
                    else identifier["root"]
                )
                label = f"Patient ID ({root_truncated})"

            print(f"  {label}: {identifier['extension']}")


if __name__ == "__main__":
    test_luxembourg_patient_ids()
