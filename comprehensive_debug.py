#!/usr/bin/env python3
"""
Comprehensive debug script to trace the Enhanced CDA Processor
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


def comprehensive_debug():
    """Comprehensive debug of the entire Enhanced CDA Processor workflow"""

    print("🔬 Comprehensive Enhanced CDA Processor Debug")
    print("=" * 60)

    # Import the processor
    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        print("✅ Enhanced CDA Processor imported")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return

    # Create processor
    processor = EnhancedCDAProcessor(target_language="en")
    print("✅ Processor initialized")

    # Test XML with both structured data and HTML table
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <component>
            <structuredBody>
                <component>
                    <section>
                        <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem list"/>
                        <title>Active Problems</title>
                        <text>
                            <table>
                                <thead>
                                    <tr><th>Problem</th><th>Status</th></tr>
                                </thead>
                                <tbody>
                                    <tr><td>Hypertension</td><td>Active</td></tr>
                                    <tr><td>Diabetes</td><td>Active</td></tr>
                                </tbody>
                            </table>
                        </text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                                <statusCode code="completed"/>
                                <value xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96" displayName="Hypertension"/>
                            </observation>
                        </entry>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                                <statusCode code="completed"/>
                                <value xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CD" code="44054006" codeSystem="2.16.840.1.113883.6.96" displayName="Type 2 diabetes mellitus"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>"""

    print("\n📋 Manual Structure Analysis:")
    root = ET.fromstring(test_xml)
    namespaces = {"hl7": "urn:hl7-org:v3"}

    sections = root.findall(".//hl7:section", namespaces)
    print(f"   Sections: {len(sections)}")

    for section in sections:
        entries = section.findall("hl7:entry", namespaces)
        print(f"   Entries: {len(entries)}")

        # Test _extract_structured_data manually
        structured_data = []
        for i, entry in enumerate(entries):
            entry_data = {"type": "structured_entry", "data": {}}

            obs_elem = entry.find(".//hl7:observation", namespaces)
            if obs_elem is not None:
                data = {}

                # Extract value
                value_elem = obs_elem.find("hl7:value", namespaces)
                if value_elem is not None:
                    data["value"] = value_elem.get("displayName", "")

                    # Check xsi:type
                    xsi_type = value_elem.get(
                        "{http://www.w3.org/2001/XMLSchema-instance}type"
                    )
                    if xsi_type == "CD":
                        data["condition_code"] = value_elem.get("code", "")
                        data["condition_display"] = value_elem.get("displayName", "")

                # Extract status
                status_code = obs_elem.find("hl7:statusCode", namespaces)
                if status_code is not None:
                    data["status"] = status_code.get("code", "")

                entry_data["data"] = data
                entry_data["section_type"] = "observation"

                print(f"     Entry {i+1} data: {data}")
                print(f"     Entry {i+1} has data: {bool(data)}")

                if entry_data["data"]:
                    structured_data.append(entry_data)

        print(f"   Manual structured data: {len(structured_data)} items")

    print("\n🧪 Testing Enhanced CDA Processor:")
    try:
        result = processor.process_clinical_sections(
            cda_content=test_xml, source_language="en"
        )

        print(f"✅ Processing result: {result.get('success', False)}")

        if result.get("success"):
            sections = result.get("sections", [])
            print(f"📝 Sections returned: {len(sections)}")

            for i, section in enumerate(sections):
                title = section.get("title", "Unknown")
                rows = section.get("table_rows", [])
                structured_data = section.get("structured_data", [])

                print(f"\n   Section {i+1}: {title}")
                print(f"   Table rows: {len(rows)}")
                print(f"   Structured data: {len(structured_data)}")

                # Show structured data details
                for j, item in enumerate(structured_data):
                    print(f"     Item {j+1}: {item}")

                # Show row content
                for j, row in enumerate(rows[:2]):  # Show first 2 rows
                    print(f"     Row {j+1}: {row[:100]}...")  # Show first 100 chars
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    comprehensive_debug()
