#!/usr/bin/env python3
"""
Simple Clinical Codes Test
Check exactly what the Enhanced parser is returning
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


def simple_codes_test():
    """Simple test to see what clinical codes are returned"""

    print("🧪 SIMPLE CLINICAL CODES TEST")
    print("=" * 60)

    # Test with Italian L3 file
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    parser = EnhancedCDAXMLParser()
    result = parser.parse_cda_content(xml_content)

    print(f"📊 RESULT KEYS: {list(result.keys())}")

    sections = result.get("sections", [])
    print(f"\\n📋 SECTIONS: {len(sections)}")

    for i, section in enumerate(sections):
        print(f"\\n--- Section {i+1} ---")
        print(f"Title: {section.get('title', {}).get('coded', 'Unknown')}")

        # Check clinical_codes
        clinical_codes = section.get("clinical_codes")

        print(f"Clinical codes object: {clinical_codes}")
        print(f"Type: {type(clinical_codes)}")

        if clinical_codes:
            print(
                f"Dir: {[attr for attr in dir(clinical_codes) if not attr.startswith('_')]}"
            )

            if hasattr(clinical_codes, "all_codes"):
                codes = clinical_codes.all_codes
                print(f"All codes length: {len(codes)}")

                for j, code in enumerate(codes[:3]):
                    print(
                        f"  Code {j+1}: {code.code} | {code.system_name} | {code.display_name}"
                    )

            if hasattr(clinical_codes, "codes"):
                codes = clinical_codes.codes
                print(f"Codes attribute length: {len(codes)}")

                for j, code in enumerate(codes[:3]):
                    print(
                        f"  Code {j+1}: {code.code} | {code.system_name} | {code.display_name}"
                    )


if __name__ == "__main__":
    simple_codes_test()
