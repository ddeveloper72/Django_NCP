#!/usr/bin/env python3
"""
Debug script to trace the _extract_structured_data method step by step
"""

import os
import sys
import xml.etree.ElementTree as ET

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

try:
    import django

    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)


def debug_extract_structured_data():
    """Debug the _extract_structured_data method step by step"""

    print("🔍 Debugging _extract_structured_data Method")
    print("=" * 50)

    # Test XML
    simple_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <component>
            <structuredBody>
                <component>
                    <section>
                        <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem list"/>
                        <title>Active Problems</title>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                                <statusCode code="completed"/>
                                <value xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96" displayName="Hypertension"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>"""

    # Parse XML
    root = ET.fromstring(simple_xml)
    namespaces = {"hl7": "urn:hl7-org:v3"}

    # Find section and entries
    section = root.find(".//hl7:section", namespaces)
    entries = section.findall("hl7:entry", namespaces)

    print(f"📝 Found {len(entries)} entries")

    # Manually implement _extract_structured_data logic
    structured_data = []

    for i, entry in enumerate(entries):
        print(f"\n🔍 Processing Entry {i+1}")

        try:
            entry_data = {"type": "structured_entry", "data": {}}

            # Check for substance administration (medications)
            sub_admin = entry.find(".//hl7:substanceAdministration", namespaces)
            print(f"   Substance administration found: {sub_admin is not None}")

            # Check for observation (allergies, lab results, etc.)
            obs_elem = entry.find(".//hl7:observation", namespaces)
            print(f"   Observation found: {obs_elem is not None}")

            if obs_elem is not None:
                print("   Extracting observation data...")

                # Manual extraction to see what happens
                data = {}

                # Get observation code
                code_elem = obs_elem.find("hl7:code", namespaces)
                if code_elem is not None:
                    data["code"] = code_elem.get("code", "")
                    data["display"] = code_elem.get(
                        "displayName", "Unknown Observation"
                    )
                    print(f"     Code: {data['code']} - {data['display']}")

                # Extract value
                value_elem = obs_elem.find("hl7:value", namespaces)
                if value_elem is not None:
                    data["value"] = value_elem.get(
                        "displayName", value_elem.get("value", "")
                    )

                    # Check xsi:type with proper namespace handling
                    xsi_type = value_elem.get(
                        "{http://www.w3.org/2001/XMLSchema-instance}type"
                    )
                    print(f"     XSI type: {xsi_type}")

                    # For problem observations, map value fields to condition fields
                    if xsi_type == "CD" or value_elem.get("xsi:type") == "CD":
                        data["condition_code"] = value_elem.get("code", "")
                        data["condition_display"] = value_elem.get(
                            "displayName", "Unknown Condition"
                        )
                        print(
                            f"     Condition: {data['condition_code']} - {data['condition_display']}"
                        )
                    else:
                        print(f"     Not a CD type, treating as generic value")

                # Extract status
                status_code = obs_elem.find("hl7:statusCode", namespaces)
                if status_code is not None:
                    data["status"] = status_code.get("code", "active")
                    print(f"     Status: {data['status']}")

                entry_data["data"] = data
                entry_data["section_type"] = "observation"

                print(f"     Extracted data: {data}")
                print(f"     Data has content: {bool(data)}")

                # Only add if we extracted meaningful data
                if entry_data["data"]:
                    structured_data.append(entry_data)
                    print("     ✅ Added to structured_data")
                else:
                    print("     ❌ Not added - empty data")

            # Check for procedure data
            procedure = entry.find(".//hl7:procedure", namespaces)
            print(f"   Procedure found: {procedure is not None}")

            # Check for act (general activities)
            act_elem = entry.find(".//hl7:act", namespaces)
            print(f"   Act found: {act_elem is not None}")

        except Exception as e:
            print(f"   ❌ Error processing entry: {e}")
            continue

    print(f"\n📊 Final Result: {len(structured_data)} structured data items")
    for i, item in enumerate(structured_data):
        print(f"   Item {i+1}: {item}")


if __name__ == "__main__":
    debug_extract_structured_data()
