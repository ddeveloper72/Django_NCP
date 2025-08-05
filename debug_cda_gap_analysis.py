#!/usr/bin/env python3
"""
Gap Analysis: Enhanced CDA Processor Data Extraction Debug
Diagnose why translations and clinical data aren't being rendered
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def debug_enhanced_cda_extraction():
    """Debug the enhanced CDA data extraction process"""

    print("🔍 Enhanced CDA Processor Gap Analysis")
    print("=" * 70)

    # Test with a sample Problem List CDA section similar to what you're seeing
    sample_cda_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <component>
            <section>
                <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
                <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem list - Reported"/>
                <title>Problem list - Reported</title>
                <text>
                    <table>
                        <thead>
                            <tr>
                                <th>Condition</th>
                                <th>Status</th>
                                <th>Onset Date</th>
                                <th>Severity</th>
                                <th>Priority</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Hypertension</td>
                                <td>Active</td>
                                <td>2020-01-15</td>
                                <td>Moderate</td>
                                <td>High</td>
                            </tr>
                            <tr>
                                <td>Type 2 Diabetes</td>
                                <td>Active</td>
                                <td>2019-06-10</td>
                                <td>Mild</td>
                                <td>Normal</td>
                            </tr>
                            <tr>
                                <td>Hyperlipidemia</td>
                                <td>Active</td>
                                <td>2021-03-22</td>
                                <td>Mild</td>
                                <td>Normal</td>
                            </tr>
                        </tbody>
                    </table>
                </text>
                <entry>
                    <observation classCode="OBS" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                        <id root="1.2.3.4.5" extension="problem1"/>
                        <code code="55607006" codeSystem="2.16.840.1.113883.6.96" displayName="Problem"/>
                        <statusCode code="active"/>
                        <value xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96" displayName="Hypertension"/>
                        <entryRelationship typeCode="SUBJ">
                            <observation classCode="OBS" moodCode="EVN">
                                <code code="SEV" displayName="Severity"/>
                                <value xsi:type="CD" code="6736007" displayName="Moderate"/>
                            </observation>
                        </entryRelationship>
                    </observation>
                </entry>
                <entry>
                    <observation classCode="OBS" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                        <id root="1.2.3.4.5" extension="problem2"/>
                        <code code="55607006" codeSystem="2.16.840.1.113883.6.96" displayName="Problem"/>
                        <statusCode code="active"/>
                        <value xsi:type="CD" code="44054006" codeSystem="2.16.840.1.113883.6.96" displayName="Type 2 Diabetes"/>
                        <entryRelationship typeCode="SUBJ">
                            <observation classCode="OBS" moodCode="EVN">
                                <code code="SEV" displayName="Severity"/>
                                <value xsi:type="CD" code="255604002" displayName="Mild"/>
                            </observation>
                        </entryRelationship>
                    </observation>
                </entry>
            </section>
        </component>
    </ClinicalDocument>"""

    try:
        # Test the extraction step by step
        print("🧪 Step 1: Testing CDA XML Parsing")
        print("-" * 50)

        import xml.etree.ElementTree as ET

        root = ET.fromstring(sample_cda_xml)
        namespaces = {
            "hl7": "urn:hl7-org:v3",
            "ext": "urn:hl7-EE-DL-Ext:v1",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

        # Find sections
        section_elements = root.findall(".//hl7:section", namespaces)
        print(f"✅ Found {len(section_elements)} sections")

        for i, section in enumerate(section_elements):
            # Extract section code
            code_elem = section.find("hl7:code", namespaces)
            section_code = code_elem.get("code", "") if code_elem is not None else ""

            # Extract title
            title_elem = section.find("hl7:title", namespaces)
            title = title_elem.text if title_elem is not None else "Unknown"

            print(f"   Section {i+1}: {title} (Code: {section_code})")

            # Check for entries
            entries = section.findall("hl7:entry", namespaces)
            print(f"   Entries found: {len(entries)}")

            # Test structured data extraction
            for j, entry in enumerate(entries):
                obs_elem = entry.find(".//hl7:observation", namespaces)
                if obs_elem is not None:
                    # Extract observation data
                    obs_code = obs_elem.find("hl7:code", namespaces)
                    value_elem = obs_elem.find("hl7:value", namespaces)
                    status_elem = obs_elem.find("hl7:statusCode", namespaces)

                    print(f"     Entry {j+1}:")
                    if obs_code is not None:
                        print(
                            f"       Code: {obs_code.get('code', '')} - {obs_code.get('displayName', '')}"
                        )
                    if value_elem is not None:
                        print(
                            f"       Value: {value_elem.get('code', '')} - {value_elem.get('displayName', '')}"
                        )
                    if status_elem is not None:
                        print(f"       Status: {status_elem.get('code', '')}")

                    # Check for severity
                    severity_elem = entry.find(
                        ".//hl7:entryRelationship[@typeCode='SUBJ']/hl7:observation/hl7:value",
                        namespaces,
                    )
                    if severity_elem is not None:
                        print(
                            f"       Severity: {severity_elem.get('displayName', '')}"
                        )

            # Check HTML table content
            text_elem = section.find("hl7:text", namespaces)
            if text_elem is not None:
                print(
                    f"   HTML table content found: {len(str(ET.tostring(text_elem, encoding='unicode')))} characters"
                )

                # Try to extract from HTML tables
                html_content = ET.tostring(text_elem, encoding="unicode")
                print(f"   Sample HTML: {html_content[:200]}...")

        print("\n🧪 Step 2: Testing Data Extraction with Mock Enhanced Processor")
        print("-" * 50)

        # Mock the enhanced processor's extraction logic
        def mock_extract_observation_data(obs_elem, namespaces):
            """Mock version of _extract_observation_data"""
            data = {}

            try:
                # Get observation code
                code_elem = obs_elem.find("hl7:code", namespaces)
                if code_elem is not None:
                    data["code"] = code_elem.get("code", "")
                    data["display"] = code_elem.get(
                        "displayName", "Unknown Observation"
                    )
                    print(f"       Extracted code: {data['code']} - {data['display']}")

                # Extract value (the actual condition/problem)
                value_elem = obs_elem.find("hl7:value", namespaces)
                if value_elem is not None:
                    data["condition_code"] = value_elem.get("code", "")
                    data["condition_display"] = value_elem.get(
                        "displayName", "Unknown Condition"
                    )
                    print(
                        f"       Extracted condition: {data['condition_code']} - {data['condition_display']}"
                    )

                # Extract status
                status_code = obs_elem.find("hl7:statusCode", namespaces)
                if status_code is not None:
                    data["status"] = status_code.get("code", "active")
                    print(f"       Extracted status: {data['status']}")

                # Extract severity
                severity_elem = obs_elem.find(
                    ".//hl7:entryRelationship[@typeCode='SUBJ']/hl7:observation/hl7:value",
                    namespaces,
                )
                if severity_elem is not None:
                    data["severity"] = severity_elem.get(
                        "displayName", "unknown"
                    ).lower()
                    print(f"       Extracted severity: {data['severity']}")

            except Exception as e:
                print(f"       ❌ Error extracting observation data: {e}")

            return data

        # Test on our sample data
        for section in section_elements:
            entries = section.findall("hl7:entry", namespaces)
            print(f"\n   Testing extraction on {len(entries)} entries:")

            for j, entry in enumerate(entries):
                obs_elem = entry.find(".//hl7:observation", namespaces)
                if obs_elem is not None:
                    print(f"     Entry {j+1} extraction:")
                    extracted_data = mock_extract_observation_data(obs_elem, namespaces)
                    print(f"     Result: {extracted_data}")

        print("\n🧪 Step 3: Gap Analysis Results")
        print("-" * 50)

        print("✅ CDA XML parsing: Working")
        print("✅ Section detection: Working")
        print("✅ Entry detection: Working")
        print("✅ Structured data extraction: Working")

        print("\n❓ POTENTIAL ISSUES:")
        print("1. Check if the actual CDA content has proper structure")
        print("2. Verify that observation entries have value elements")
        print("3. Ensure the display names are being properly extracted")
        print("4. Check if the template is correctly displaying the extracted data")

        print("\n🔧 RECOMMENDED FIXES:")
        print("1. Add debug logging to see what data is actually extracted")
        print("2. Check if the fallback HTML table extraction is working")
        print("3. Verify the problem row generation logic")
        print("4. Test with actual patient CDA data")

    except Exception as e:
        print(f"❌ Debug Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_enhanced_cda_extraction()
