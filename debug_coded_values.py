#!/usr/bin/env python
"""
Debug script to verify coded participant value extraction from CDA documents.
"""

import os
import sys
import django
from xml.etree import ElementTree as ET

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def analyze_coded_participants():
    """Analyze coded participant values in a specific CDA document."""

    # Test with the document we just examined
    test_file = r"c:\Users\Duncan\VS_Code_Projects\django_ncp\test_data\eu_member_states\UNKNOWN\JOLANTA_EGLE_291003-2_3.xml"

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return

    print(f"🔍 Analyzing coded participants in: {os.path.basename(test_file)}")
    print("-" * 80)

    try:
        # Parse XML
        tree = ET.parse(test_file)
        root = tree.getroot()

        # Find namespace
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag[1 : root.tag.find("}")]
            ns = {"hl7": namespace}
        else:
            ns = {}

        # Find all participant elements
        if namespace:
            participants = root.findall('.//hl7:participant[@typeCode="IND"]', ns)
        else:
            participants = root.findall('.//participant[@typeCode="IND"]')

        print(f"📊 Found {len(participants)} participants")
        print()

        for i, participant in enumerate(participants, 1):
            print(f"👤 Participant {i}:")

            # Extract function code
            if namespace:
                function_code_elem = participant.find(".//hl7:functionCode", ns)
            else:
                function_code_elem = participant.find(".//functionCode")

            function_code = (
                function_code_elem.get("code")
                if function_code_elem is not None
                else None
            )
            print(f"   Function Code: {function_code}")

            # Extract associated entity class code
            if namespace:
                entity_elem = participant.find(".//hl7:associatedEntity", ns)
            else:
                entity_elem = participant.find(".//associatedEntity")

            class_code = (
                entity_elem.get("classCode") if entity_elem is not None else None
            )
            print(f"   Class Code: {class_code}")

            # Extract relationship code (if present)
            if entity_elem is not None:
                if namespace:
                    code_elem = entity_elem.find(".//hl7:code", ns)
                else:
                    code_elem = entity_elem.find(".//code")

                if code_elem is not None:
                    relationship_code = code_elem.get("code")
                    display_name = code_elem.get("displayName")
                    code_system = code_elem.get("codeSystem")
                    print(f"   Relationship Code: {relationship_code}")
                    print(f"   Display Name: {display_name}")
                    print(f"   Code System: {code_system}")
                else:
                    print(f"   Relationship Code: None")

            # Extract name
            if entity_elem is not None:
                if namespace:
                    person_elem = entity_elem.find(".//hl7:associatedPerson", ns)
                    if person_elem is not None:
                        name_elem = person_elem.find(".//hl7:name", ns)
                        if name_elem is not None:
                            given_elem = name_elem.find(".//hl7:given", ns)
                            family_elem = name_elem.find(".//hl7:family", ns)
                else:
                    person_elem = entity_elem.find(".//associatedPerson")
                    if person_elem is not None:
                        name_elem = person_elem.find(".//name")
                        if name_elem is not None:
                            given_elem = name_elem.find(".//given")
                            family_elem = name_elem.find(".//family")

                if person_elem is not None and name_elem is not None:
                    given_name = given_elem.text if given_elem is not None else ""
                    family_name = family_elem.text if family_elem is not None else ""
                    full_name = f"{given_name} {family_name}".strip()
                    print(f"   Name: {full_name}")
                else:
                    print(f"   Name: Not specified")

            # Determine participant type
            participant_type = "Unknown"
            if function_code == "PCP":
                participant_type = "Primary Care Provider"
            elif class_code == "ECON":
                if relationship_code == "FAMMEMB":
                    participant_type = "Emergency Contact (Family Member)"
                else:
                    participant_type = "Emergency Contact"
            elif class_code == "PRS":
                participant_type = "Person/Contact"

            print(f"   ➤ Type: {participant_type}")
            print()

        # Summary of coded values found
        print("📋 Summary of Coded Values Found:")
        function_codes = set()
        class_codes = set()
        relationship_codes = set()

        for participant in participants:
            # Function codes
            if namespace:
                function_code_elem = participant.find(".//hl7:functionCode", ns)
            else:
                function_code_elem = participant.find(".//functionCode")
            if function_code_elem is not None:
                function_codes.add(function_code_elem.get("code"))

            # Class codes
            if namespace:
                entity_elem = participant.find(".//hl7:associatedEntity", ns)
            else:
                entity_elem = participant.find(".//associatedEntity")
            if entity_elem is not None:
                class_codes.add(entity_elem.get("classCode"))

                # Relationship codes
                if namespace:
                    code_elem = entity_elem.find(".//hl7:code", ns)
                else:
                    code_elem = entity_elem.find(".//code")
                if code_elem is not None:
                    relationship_codes.add(code_elem.get("code"))

        print(f"   Function Codes: {sorted(function_codes)}")
        print(f"   Class Codes: {sorted(class_codes)}")
        print(f"   Relationship Codes: {sorted(relationship_codes)}")

    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    analyze_coded_participants()
