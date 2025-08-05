#!/usr/bin/env python3
"""
Test Enhanced Parser Django Integration
Verify that the enhanced parser works through the full Django workflow
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

from patient_data.services.cda_translation_manager import CDATranslationManager


def test_django_integration():
    """Test the enhanced parser integration through Django CDA Translation Manager"""

    print("🚀 TESTING ENHANCED PARSER DJANGO INTEGRATION")
    print("=" * 70)

    # Test with Italian L3 file
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    print(f"📄 Testing: {test_file.name}")

    # Read the CDA content
    with open(test_file, "r", encoding="utf-8") as f:
        cda_content = f.read()

    print(f"📊 CDA Content Length: {len(cda_content)} characters")

    # Initialize the translation manager (this is what Django uses)
    translation_manager = CDATranslationManager(target_language="en")

    print("\\n🔄 Processing through CDA Translation Manager...")

    # Process the CDA content (this is the main Django workflow)
    result = translation_manager.process_cda_for_viewer(
        cda_content, source_language="it"
    )

    print(f"\\n✅ PROCESSING RESULTS:")
    print("-" * 70)

    if result.get("success"):
        print("✅ Processing successful!")
        print(f"📁 Content type: {result.get('content_type')}")
        print(f"🌍 Source language: {result.get('source_language')}")
        print(f"🎯 Target language: {result.get('target_language')}")

        # Check translation result
        translation_result = result.get("translation_result", {})
        print(f"\\n📊 TRANSLATION METRICS:")
        print(f"   📋 Total sections: {translation_result.get('sections_count', 0)}")
        print(
            f"   🏷️  Coded sections: {translation_result.get('coded_sections_count', 0)}"
        )
        print(
            f"   🧬 Medical terms: {translation_result.get('medical_terms_count', 0)}"
        )
        print(
            f"   📈 Translation quality: {translation_result.get('translation_quality', 'Unknown')}"
        )
        print(
            f"   ✨ Uses coded sections: {translation_result.get('uses_coded_sections', False)}"
        )

        # Check patient identity
        patient_identity = result.get("patient_identity", {})
        if patient_identity:
            print(f"\\n👤 PATIENT IDENTITY:")
            print(
                f"   Name: {patient_identity.get('given_name', 'N/A')} {patient_identity.get('family_name', 'N/A')}"
            )
            print(f"   Birth Date: {patient_identity.get('birth_date', 'N/A')}")
            print(f"   Gender: {patient_identity.get('gender', 'N/A')}")

        # Check sections in detail
        sections = translation_result.get("sections", [])
        if sections:
            print(f"\\n📋 SECTIONS DETAIL (showing first 3):")
            for i, section in enumerate(sections[:3]):
                title = section.get("title", {})
                section_title = (
                    title.get("coded", "Unknown")
                    if isinstance(title, dict)
                    else str(title)
                )

                print(f"   {i+1}. {section_title}")
                print(f"      ID: {section.get('section_id', 'N/A')}")

                # Check clinical codes
                clinical_codes = section.get("clinical_codes")
                if clinical_codes and hasattr(clinical_codes, "codes"):
                    print(f"      Clinical codes: {len(clinical_codes.codes)} codes")

                    # Show first few codes
                    for j, code in enumerate(clinical_codes.codes[:2]):
                        print(f"         - {code.system_name}: {code.code}")
                        if code.display_name:
                            print(f'           "{code.display_name}"')
                else:
                    print(f"      Clinical codes: None")

        # Final assessment
        print(f"\\n🎯 DJANGO INTEGRATION ASSESSMENT:")
        print("-" * 70)

        sections_count = translation_result.get("sections_count", 0)
        medical_terms = translation_result.get("medical_terms_count", 0)

        if sections_count > 0 and medical_terms > 0:
            print("🎉 EXCELLENT: Enhanced parser fully integrated with Django!")
            print(f"   ✅ Extracting {sections_count} clinical sections")
            print(f"   ✅ Extracting {medical_terms} clinical codes")
            print("   ✅ Ready for production use in Django app")
            print("   ✅ Can now view enhanced CDA documents with clinical codes")
        elif sections_count > 0:
            print("⚠️  GOOD: Sections extracted, but limited clinical codes")
        else:
            print("❌ NEEDS WORK: No sections extracted")

    else:
        print("❌ Processing failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

    return result


if __name__ == "__main__":
    test_django_integration()
