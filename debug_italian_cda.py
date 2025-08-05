#!/usr/bin/env python3
"""
Debug script to test enhanced CDA parser on Italian test document
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


def debug_italian_cda():
    """Test the enhanced parser on the Italian CDA document"""

    # Path to the Italian CDA test file
    italian_cda_path = "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    print("🔍 DEBUG: Testing Enhanced CDA Parser on Italian Document")
    print(f"📄 File: {italian_cda_path}")
    print("=" * 80)

    try:
        # Initialize parser
        parser = EnhancedCDAXMLParser()

        # Read and parse the document
        with open(italian_cda_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        result = parser.parse_cda_content(xml_content)

        print("✅ Parser executed successfully!")
        print(f"📊 Result type: {type(result)}")
        print(
            f"📋 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
        )

        # Check sections
        sections = result.get("sections", [])
        print(f"\n📑 Sections found: {len(sections)}")

        if sections:
            for i, section in enumerate(sections):
                print(f"\n🔸 Section {i+1}:")
                print(f"   Title: {section.get('title', 'No title')}")
                print(f"   Code: {section.get('section_code', 'No code')}")
                print(f"   Is Coded: {section.get('is_coded_section', False)}")

                # Check for clinical codes
                clinical_codes = section.get("clinical_codes")
                if clinical_codes:
                    if hasattr(clinical_codes, "all_codes"):
                        print(
                            f"   Clinical Codes: {len(clinical_codes.all_codes)} codes"
                        )
                        for code in clinical_codes.all_codes[:3]:  # Show first 3
                            print(
                                f"      - {code.system}: {code.code} ({code.display})"
                            )
                    else:
                        print(f"   Clinical Codes: {clinical_codes}")
                else:
                    print(f"   Clinical Codes: None")
        else:
            print("❌ No sections found!")

        # Check patient identity
        patient_identity = result.get("patient_identity", {})
        print(f"\n👤 Patient Identity:")
        print(
            f"   Raw patient_identity keys: {list(patient_identity.keys()) if patient_identity else 'None'}"
        )
        print(f"   Given Name: {patient_identity.get('given_name', 'N/A')}")
        print(f"   Family Name: {patient_identity.get('family_name', 'N/A')}")
        print(f"   Birth Date: {patient_identity.get('birth_date', 'N/A')}")
        print(f"   Gender: {patient_identity.get('gender', 'N/A')}")
        print(f"   Patient ID: {patient_identity.get('patient_id', 'N/A')}")

        # Check administrative data
        admin_data = result.get("administrative_data", {})
        print(f"\n📋 Administrative Data:")
        print(
            f"   Raw admin_data keys: {list(admin_data.keys()) if admin_data else 'None'}"
        )
        print(
            f"   Has Administrative Data: {result.get('has_administrative_data', False)}"
        )
        print(f"   Document Title: {admin_data.get('document_title', 'N/A')}")
        print(f"   Creation Date: {admin_data.get('creation_date', 'N/A')}")
        print(f"   Document Type: {admin_data.get('document_type', 'N/A')}")

        # Debug: Let's see ALL keys in the result
        print(f"\n🔍 ALL RESULT KEYS:")
        for key in result.keys():
            print(f"   {key}: {type(result[key])}")

        return result

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        print(f"🔥 Traceback:\n{traceback.format_exc()}")
        return None


if __name__ == "__main__":
    debug_italian_cda()
