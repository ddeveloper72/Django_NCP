#!/usr/bin/env python3
"""
Quick test to check what coded entries are found in Italian CDA
"""

import xml.etree.ElementTree as ET


def test_italian_cda_codes():
    """Test what coded entries exist in the Italian CDA"""

    file_path = "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    print("🔍 Testing Italian CDA for coded entries")
    print("=" * 60)

    try:
        # Parse XML
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Find all sections
        sections = root.findall(".//{urn:hl7-org:v3}section")
        print(f"📑 Found {len(sections)} sections")

        for i, section in enumerate(sections):
            # Get section title
            title_elem = section.find("{urn:hl7-org:v3}title")
            title = title_elem.text if title_elem is not None else f"Section {i+1}"
            print(f"\n🔸 {title}")

            # Find entries in this section
            entries = section.findall("{urn:hl7-org:v3}entry")
            print(f"   📝 Entries: {len(entries)}")

            # Look for coded elements in entries
            coded_count = 0
            for entry in entries:
                for elem in entry.iter():
                    if elem.get("code") and elem.get("codeSystem"):
                        coded_count += 1
                        code = elem.get("code")
                        system = elem.get("codeSystem")
                        system_name = elem.get("codeSystemName", "")
                        display = elem.get("displayName", "")

                        print(
                            f"      🏷️  {system_name or 'Unknown'}: {code} - {display}"
                        )

            if coded_count == 0:
                print(f"      ❌ No coded elements found in entries")
            else:
                print(f"      ✅ Found {coded_count} coded elements")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    test_italian_cda_codes()
