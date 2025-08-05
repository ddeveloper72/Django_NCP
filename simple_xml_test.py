#!/usr/bin/env python3
"""Simple test to check if sections are found"""

import xml.etree.ElementTree as ET

# Test namespaces
namespaces = {"cda": "urn:hl7-org:v3", "pharm": "urn:hl7-org:pharm"}

# Load the Italian CDA file
file_path = "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

print("🔍 Testing XML parsing...")
try:
    tree = ET.parse(file_path)
    root = tree.getroot()
    print(f"✅ XML loaded. Root tag: {root.tag}")

    # Test both searches
    sections_without_ns = root.findall(".//section")
    sections_with_full_ns = root.findall(".//{urn:hl7-org:v3}section")

    print(f"📋 Sections found without namespace: {len(sections_without_ns)}")
    print(f"📋 Sections found with full namespace: {len(sections_with_full_ns)}")

    if sections_with_full_ns:
        for i, section in enumerate(sections_with_full_ns[:2]):  # Show first 2
            title_elem = section.find("{urn:hl7-org:v3}title")
            title = title_elem.text if title_elem is not None else "No title"
            print(f"   Section {i+1}: {title}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
