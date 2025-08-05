#!/usr/bin/env python3
"""
Compare Enhanced XML Parser vs JSON Bundle Parser
Test both approaches on Italian CDA document
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
from patient_data.services.cda_json_bundle_parser import CDAJSONBundleParser


def compare_parsers():
    """Compare both parsing approaches"""

    italian_cda_path = "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    print("🔬 PARSER COMPARISON: Enhanced XML vs JSON Bundle")
    print(f"📄 File: {italian_cda_path}")
    print("=" * 80)

    # Test Enhanced XML Parser
    print("\n🔧 ENHANCED XML PARSER:")
    print("-" * 40)
    try:
        xml_parser = EnhancedCDAXMLParser()
        xml_result = xml_parser.parse_cda_file(italian_cda_path)

        xml_sections = xml_result.get("sections", [])
        xml_total_codes = sum(
            len(
                section.get("clinical_codes", {}).all_codes
                if hasattr(section.get("clinical_codes", {}), "all_codes")
                else []
            )
            for section in xml_sections
        )

        print(f"✅ SUCCESS")
        print(f"📑 Sections: {len(xml_sections)}")
        print(f"🏷️  Total Codes: {xml_total_codes}")

        # Show sample codes
        for i, section in enumerate(xml_sections[:2]):
            clinical_codes = section.get("clinical_codes")
            if (
                clinical_codes
                and hasattr(clinical_codes, "all_codes")
                and clinical_codes.all_codes
            ):
                print(
                    f"   Section {i+1} - {section.get('title', 'No title')}: {len(clinical_codes.all_codes)} codes"
                )
                for code in clinical_codes.all_codes[:2]:
                    print(f"      • {code.system}: {code.code}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        xml_result = None
        xml_total_codes = 0

    # Test JSON Bundle Parser
    print("\n🌐 JSON BUNDLE PARSER:")
    print("-" * 40)
    try:
        json_parser = CDAJSONBundleParser()
        json_result = json_parser.parse_cda_file(italian_cda_path)

        json_sections = json_result.get("sections", [])
        json_total_codes = json_result.get("total_clinical_codes", 0)

        print(f"✅ SUCCESS")
        print(f"📑 Sections: {len(json_sections)}")
        print(f"🏷️  Total Codes: {json_total_codes}")

        # Show sample codes
        for i, section in enumerate(json_sections[:2]):
            clinical_codes = section.get("clinical_codes", [])
            if clinical_codes:
                print(
                    f"   Section {i+1} - {section.get('title', 'No title')}: {len(clinical_codes)} codes"
                )
                for code in clinical_codes[:2]:
                    print(
                        f"      • {code.get('system_name', '')}: {code.get('code', '')}"
                    )

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        print(f"🔥 Traceback: {traceback.format_exc()}")
        json_result = None
        json_total_codes = 0

    # Comparison Summary
    print("\n📊 COMPARISON SUMMARY:")
    print("=" * 80)
    print(f"Enhanced XML Parser: {xml_total_codes} codes")
    print(f"JSON Bundle Parser:  {json_total_codes} codes")

    if json_total_codes > xml_total_codes:
        print("🏆 JSON Bundle Parser found MORE codes!")
    elif xml_total_codes > json_total_codes:
        print("🏆 Enhanced XML Parser found MORE codes!")
    else:
        print("🤝 Both parsers found the same number of codes")

    # Architecture Benefits
    print("\n🏗️  ARCHITECTURE BENEFITS:")
    print("Enhanced XML Parser:")
    print("  ✅ Working with current system")
    print("  ⚠️  Country-specific XPath patterns")
    print("  ⚠️  XML namespace complexity")

    print("\nJSON Bundle Parser:")
    print("  ✅ Country-agnostic approach")
    print("  ✅ Future-proof for new EU countries")
    print("  ✅ JSON queries easier than XPath")
    print("  ✅ Better performance potential")
    print("  ✅ Modular architecture")

    return xml_result, json_result


if __name__ == "__main__":
    compare_parsers()
