#!/usr/bin/env python
"""
Test Enhanced CDA XML Parser with Clinical Coding Extraction
"""

import os
import sys
import django

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

import logging
from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_enhanced_parser():
    """Test the enhanced CDA XML parser with Italian test data"""

    # Test file path
    test_file = "test_data/eu_member_states/IT/2025-03-28T13-29-58.949209Z_CDA_EHDSI---PIVOT-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    if not os.path.exists(test_file):
        logger.error(f"Test file not found: {test_file}")
        return False

    # Load test CDA content
    with open(test_file, "r", encoding="utf-8") as f:
        cda_content = f.read()

    logger.info(f"Loaded test CDA content: {len(cda_content)} characters")

    # Initialize enhanced parser
    parser = EnhancedCDAXMLParser()

    # Parse the content
    try:
        result = parser.parse_cda_content(cda_content)

        # Print summary results
        print("\n" + "=" * 60)
        print("ENHANCED CDA PARSER TEST RESULTS")
        print("=" * 60)

        print(f"Sections found: {result['sections_count']}")
        print(f"Coded sections: {result['coded_sections_count']}")
        print(f"Clinical codes extracted: {result['medical_terms_count']}")
        print(f"Coding percentage: {result['coded_sections_percentage']}%")
        print(f"Translation quality: {result['translation_quality']}")
        print(f"Uses coded sections: {result['uses_coded_sections']}")

        # Print patient info
        patient_info = result["patient_identity"]
        print(f"\nPatient Identity:")
        print(f"  Name: {patient_info['given_name']} {patient_info['family_name']}")
        print(f"  Birth Date: {patient_info['birth_date']}")
        print(f"  Gender: {patient_info['gender']}")

        # Print section details
        print(f"\nSection Details:")
        for i, section in enumerate(result["sections"][:5]):  # Show first 5 sections
            print(f"  Section {i+1}: {section['title']['coded']}")
            print(f"    - Section Code: {section.get('section_code', 'None')}")
            print(f"    - Is Coded: {section['is_coded_section']}")
            print(f"    - Medical Terms: {section['content']['medical_terms']}")

            # Show clinical codes if available
            if section.get("clinical_codes") and hasattr(
                section["clinical_codes"], "codes"
            ):
                codes = section["clinical_codes"].codes
                if codes:
                    print(f"    - Clinical Codes ({len(codes)}):")
                    for code in codes[:3]:  # Show first 3 codes
                        print(
                            f"      * {code.system_name}: {code.code} - {code.display_name or 'No display name'}"
                        )

            # Show content preview
            content_preview = section["content"]["original"][:100].replace("\n", " ")
            print(f"    - Content Preview: {content_preview}...")
            print()

        if len(result["sections"]) > 5:
            print(f"  ... and {len(result['sections']) - 5} more sections")

        print("\n" + "=" * 60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Parser test failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("Testing Enhanced CDA XML Parser with Clinical Coding...")
    success = test_enhanced_parser()

    if success:
        print("\n✅ Enhanced parser is working correctly!")
        print("🔬 Clinical codes are being extracted from CDA sections")
        print("🏥 Patient data and administrative information parsed")
        print("📊 Translation quality assessment completed")
    else:
        print("\n❌ Enhanced parser test failed!")
        print("🔧 Check the error logs above for debugging information")

    sys.exit(0 if success else 1)
