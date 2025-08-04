#!/usr/bin/env python3
"""
Test patient identifier extraction with the specific ID 2544557646
"""
from xml.etree import ElementTree as ET


def extract_patient_identifiers_simple(cda_content):
    """Extract patient identifiers from CDA content"""
    try:
        root = ET.fromstring(cda_content)

        # Define namespace
        namespaces = {"hl7": "urn:hl7-org:v3"}

        # Find all patient ID elements
        patient_ids = root.findall(
            ".//hl7:recordTarget/hl7:patientRole/hl7:id", namespaces
        )

        identifiers = []
        for id_elem in patient_ids:
            identifier = {
                "extension": id_elem.get("extension"),
                "root": id_elem.get("root"),
            }
            identifiers.append(identifier)

        return identifiers
    except Exception as e:
        print(f"Error extracting identifiers: {e}")
        return []


def test_specific_id():
    """Test with the CDA containing 2544557646"""

    # Read the test CDA
    with open("test_cda_with_2544557646.xml", "r", encoding="utf-8") as f:
        cda_content = f.read()

    print("Testing CDA with patient ID 2544557646...")

    identifiers = extract_patient_identifiers_simple(cda_content)

    print(f"Found {len(identifiers)} identifiers:")

    for i, identifier in enumerate(identifiers, 1):
        print(f"  {i}. Extension: {identifier.get('extension', 'N/A')}")
        print(f"     Root: {identifier.get('root', 'N/A')}")
        print()

    # Test if this contains the search ID
    search_id = "2544557646"
    found_search_id = any(
        identifier.get("extension") == search_id for identifier in identifiers
    )

    print(f"Search ID '{search_id}' found: {found_search_id}")

    # Show how these would appear in the template
    print("\nHow these would appear in the CDA template:")
    for identifier in identifiers:
        extension = identifier.get("extension", "N/A")
        root = identifier.get("root", "N/A")
        print(f"  Patient ID ({root}): {extension}")


if __name__ == "__main__":
    test_specific_id()
