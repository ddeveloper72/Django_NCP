#!/usr/bin/env python3
"""
Simple test of JSON Bundle Parser concept
"""

import json
import xmltodict
from pathlib import Path


def test_json_conversion():
    """Test XML to JSON conversion on Italian CDA"""

    italian_cda_path = "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    print("🧪 Testing XML → JSON Bundle Conversion")
    print(f"📄 File: {italian_cda_path}")
    print("=" * 60)

    try:
        # Load XML
        with open(italian_cda_path, "r", encoding="utf-8") as file:
            xml_content = file.read()

        print(f"📄 XML loaded: {len(xml_content)} characters")

        # Convert to JSON
        json_bundle = xmltodict.parse(
            xml_content, process_namespaces=True, namespace_separator="__"
        )

        print(f"✅ JSON conversion successful!")
        print(f"📊 Top-level keys: {list(json_bundle.keys())}")

        # Look for clinical document
        clinical_doc = None
        for key, value in json_bundle.items():
            if "ClinicalDocument" in key:
                clinical_doc = value
                print(f"🏥 Found ClinicalDocument: {key}")
                break

        if clinical_doc:
            print(f"📋 ClinicalDocument keys: {list(clinical_doc.keys())[:10]}...")

            # Look for sections
            if "component" in clinical_doc:
                component = clinical_doc["component"]
                print(f"🔗 Component type: {type(component)}")

                if isinstance(component, dict) and "structuredBody" in component:
                    structured_body = component["structuredBody"]
                    if "component" in structured_body:
                        sections = structured_body["component"]
                        print(
                            f"📑 Found {len(sections) if isinstance(sections, list) else 1} sections"
                        )

                        # Sample first section
                        if isinstance(sections, list) and sections:
                            first_section = sections[0]
                        else:
                            first_section = sections

                        if (
                            isinstance(first_section, dict)
                            and "section" in first_section
                        ):
                            section = first_section["section"]
                            print(f"🔍 Sample section keys: {list(section.keys())}")

                            # Look for codes
                            if "entry" in section:
                                entries = section["entry"]
                                print(
                                    f"📝 Found {len(entries) if isinstance(entries, list) else 1} entries"
                                )

                                # Count coded elements
                                coded_count = 0

                                def count_codes(data, path=""):
                                    nonlocal coded_count
                                    if isinstance(data, dict):
                                        if "@code" in data or "@codeSystem" in data:
                                            coded_count += 1
                                            print(
                                                f"   🏷️  Code found at {path}: {data.get('@code', 'N/A')}"
                                            )
                                        for key, value in data.items():
                                            count_codes(value, f"{path}.{key}")
                                    elif isinstance(data, list):
                                        for i, item in enumerate(data):
                                            count_codes(item, f"{path}[{i}]")

                                count_codes(entries)
                                print(f"🎯 Total coded elements found: {coded_count}")

        # Test JSONPath-like access
        print("\n🛣️  Testing JSON Path Access:")

        # Try to find patient name using different paths
        patient_paths = [
            ["ClinicalDocument", "recordTarget", "patientRole", "patient", "name"],
            ["ClinicalDocument", "recordTarget", 0, "patientRole", "patient", "name"],
        ]

        for path in patient_paths:
            try:
                current = json_bundle
                for step in path:
                    if isinstance(current, dict):
                        current = current.get(step)
                    elif isinstance(current, list) and isinstance(step, int):
                        current = current[step] if step < len(current) else None
                    else:
                        current = None
                        break

                if current:
                    print(f"✅ Found patient name via {path}: {current}")
                    break
            except:
                continue

        print("\n🎉 JSON Bundle approach is viable!")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        print(f"🔥 Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    test_json_conversion()
