#!/usr/bin/env python3
"""
Debug Clinical Codes Extraction
Why are we getting sections but no codes?
"""

import os
import sys
import django
from pathlib import Path

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def debug_codes_extraction():
    """Debug why no clinical codes are being extracted"""

    print("🔍 DEBUG CLINICAL CODES EXTRACTION")
    print("=" * 60)

    # Test with a known good file (Italian L3)
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    print(f"📄 Testing: {test_file.name}")

    # Parse the file
    parser = EnhancedCDAXMLParser()

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    result = parser.parse_cda_content(xml_content)

    print(f"\\n📊 PARSING RESULTS:")
    print("-" * 60)

    sections = result.get("sections", [])
    print(f"Sections found: {len(sections)}")

    for i, section in enumerate(sections, 1):
        print(f"\\n📋 Section {i}: {section.get('title', 'Unknown')}")
        print(f"   Code: {section.get('code', 'N/A')}")
        print(f"   Text length: {len(section.get('text', ''))}")

        # Check clinical codes
        clinical_codes = section.get("clinical_codes")
        if clinical_codes:
            print(f"   Clinical codes object: {type(clinical_codes)}")
            if hasattr(clinical_codes, "all_codes"):
                print(f"   Total codes: {len(clinical_codes.all_codes)}")

                # Show first few codes
                for j, code in enumerate(clinical_codes.all_codes[:3]):
                    print(f"      Code {j+1}: {code.code} ({code.system_name})")
            else:
                print(f"   ❌ No all_codes attribute!")
        else:
            print(f"   ❌ No clinical_codes object!")

    # Let's also check the raw XML to see if codes are present
    print(f"\\n🔍 RAW XML ANALYSIS:")
    print("-" * 60)

    # Count coded elements in XML
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_content)

        # Look for common coded elements
        coded_elements = []

        # Find all elements with code attributes
        for elem in root.iter():
            if elem.get("code"):
                coded_elements.append(
                    {
                        "tag": elem.tag,
                        "code": elem.get("code"),
                        "codeSystem": elem.get("codeSystem"),
                        "displayName": elem.get("displayName"),
                    }
                )

        print(f"Elements with code attributes: {len(coded_elements)}")

        # Show first few
        for i, elem in enumerate(coded_elements[:5]):
            print(
                f"   {i+1}. {elem['tag']}: {elem['code']} ({elem.get('displayName', 'No display')})"
            )
            print(f"      System: {elem.get('codeSystem', 'No system')}")

        if coded_elements:
            print(f"\\n✅ XML contains {len(coded_elements)} coded elements!")
            print("The parser should be finding these codes...")
        else:
            print("\\n❌ No coded elements found in XML")

    except Exception as e:
        print(f"❌ Error parsing XML: {e}")

    return result


if __name__ == "__main__":
    debug_codes_extraction()
