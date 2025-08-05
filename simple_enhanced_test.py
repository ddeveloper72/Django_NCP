#!/usr/bin/env python3
"""
Simple test script to check Enhanced CDA Processor
"""

import os
import sys

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


def test_enhanced_processor():
    """Test basic functionality of Enhanced CDA Processor"""

    print("🧪 Testing Enhanced CDA Processor Import")

    try:
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        print("✅ Enhanced CDA Processor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Enhanced CDA Processor: {e}")
        return False

    # Test initialization
    try:
        processor = EnhancedCDAProcessor(target_language="en")
        print("✅ Enhanced CDA Processor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return False

    # Test with simple XML
    simple_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>"""

    # Test the XML parsing manually first
    print("\n🔍 Manual XML Analysis:")
    try:
        import xml.etree.ElementTree as ET

        root = ET.fromstring(simple_xml)
        namespaces = {"hl7": "urn:hl7-org:v3"}

        sections = root.findall(".//hl7:section", namespaces)
        print(f"   Sections found: {len(sections)}")

        for section in sections:
            entries = section.findall("hl7:entry", namespaces)
            print(f"   Entries in section: {len(entries)}")

            for i, entry in enumerate(entries):
                obs = entry.find(".//hl7:observation", namespaces)
                if obs is not None:
                    value_elem = obs.find("hl7:value", namespaces)
                    if value_elem is not None:
                        print(
                            f"   Entry {i+1} observation value: {value_elem.get('displayName', 'No display')}"
                        )
                        print(
                            f"   Entry {i+1} observation code: {value_elem.get('code', 'No code')}"
                        )
                    else:
                        print(f"   Entry {i+1}: No value element found")
                else:
                    print(f"   Entry {i+1}: No observation found")

    except Exception as e:
        print(f"   Manual analysis failed: {e}")

    try:
        result = processor.process_clinical_sections(
            cda_content=simple_xml, source_language="en"
        )

        print(f"✅ Processing completed: {result.get('success', False)}")

        if result.get("success"):
            sections = result.get("sections", [])
            print(f"📝 Found {len(sections)} sections")

            for section in sections:
                print(f"   Section: {section.get('title', 'Unknown')}")
                print(f"   Code: {section.get('code', 'No Code')}")
                print(f"   Rows: {len(section.get('table_rows', []))}")

                # Print actual row content to see what's happening
                for i, row in enumerate(section.get("table_rows", [])):
                    print(f"   Row {i+1}: {row}")

                # Check if there's structured data
                structured_data = section.get("structured_data", [])
                print(f"   Structured Data: {len(structured_data)} items")
                for i, item in enumerate(structured_data):
                    print(f"   Item {i+1}: {item}")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")

        return True

    except Exception as e:
        print(f"❌ Processing failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_enhanced_processor()
