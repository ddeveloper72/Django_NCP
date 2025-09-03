#!/usr/bin/env python3
"""
Print detailed logs for Enhanced CDA Clinical Sections processing
"""

import os
import sys
import django

# Add the Django project directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

# Configure logging to show all output
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Set specific loggers to DEBUG level
logging.getLogger("patient_data.services.enhanced_cda_processor").setLevel(
    logging.DEBUG
)
logging.getLogger("patient_data.views.enhanced_cda_display").setLevel(logging.DEBUG)

django.setup()

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
from patient_data.views.enhanced_cda_display import EnhancedCDADisplayView


def print_clinical_sections_log():
    """Run the enhanced CDA processor and print detailed logs for each section"""

    print("=" * 80)
    print("ENHANCED CDA CLINICAL SECTIONS PROCESSING LOG")
    print("=" * 80)

    try:
        # Create view and get test patient data
        view = EnhancedCDADisplayView()
        patient_id = "test_patient_123"

        print(f"\n🔍 STEP 1: Getting CDA content for patient {patient_id}")
        print("-" * 60)

        cda_content = view._get_patient_cda_content(patient_id)
        if not cda_content:
            print("❌ ERROR: No CDA content found")
            return

        print(f"✅ CDA content retrieved: {len(cda_content)} characters")

        # Detect content type
        if "<?xml" in cda_content or "<ClinicalDocument" in cda_content:
            content_type = "XML CDA"
        elif "<html" in cda_content or "<body" in cda_content:
            content_type = "HTML CDA"
        else:
            content_type = "Unknown"

        print(f"📄 Content type: {content_type}")

        # Find section codes in HTML
        import re

        section_codes = re.findall(r'data-code="([^"]+)"', cda_content)
        print(f"🏷️  Section codes found: {section_codes}")

        print(f"\n🔧 STEP 2: Initializing Enhanced CDA Processor")
        print("-" * 60)

        # Initialize processor
        processor = EnhancedCDAProcessor(target_language="lv")

        print(f"\n🚀 STEP 3: Processing Clinical Sections")
        print("-" * 60)

        # Process sections
        result = processor.process_clinical_sections(
            cda_content=cda_content, source_language="fr"
        )

        print(f"\n📊 STEP 4: Processing Results Summary")
        print("-" * 60)

        print(f"✅ Processing success: {result.get('success', False)}")
        print(f"📋 Total sections: {result.get('sections_count', 0)}")
        print(f"🏥 Content type detected: {result.get('content_type', 'unknown')}")
        print(f"🔬 Medical terms count: {result.get('medical_terms_count', 0)}")
        print(f"📈 Coded sections: {result.get('coded_sections_count', 0)}")

        print(f"\n🔍 STEP 5: Detailed Section Analysis")
        print("=" * 80)

        sections = result.get("sections", [])

        for i, section in enumerate(sections):
            print(f"\n📋 SECTION {i+1} DETAILED LOG")
            print("-" * 50)

            # Basic section info
            section_id = section.get("section_id", "No ID")
            section_code = section.get("section_code", "No code")
            title_info = section.get("title", {})

            if isinstance(title_info, dict):
                original_title = title_info.get("original", "No title")
                translated_title = title_info.get("translated", original_title)
            else:
                original_title = str(title_info)
                translated_title = original_title

            has_ps_table = section.get("has_ps_table", False)
            is_coded_section = section.get("is_coded_section", False)

            print(f"   🆔 Section ID: {section_id}")
            print(f"   🏷️  Section Code: {section_code}")
            print(f"   📝 Original Title: '{original_title}'")
            print(f"   🌐 Translated Title: '{translated_title}'")
            print(f"   📊 Has PS Table: {has_ps_table}")
            print(f"   💻 Is Coded Section: {is_coded_section}")

            # Clinical codes info
            clinical_codes = section.get("clinical_codes", {})
            print(f"   🔬 Clinical Codes:")
            for key, value in clinical_codes.items():
                print(f"      {key}: {value}")

            # Content analysis
            content_info = section.get("content", {})
            if content_info:
                medical_terms = content_info.get("medical_terms", 0)
                print(f"   🏥 Medical terms found: {medical_terms}")

            # VALUE SET INTEGRATION ANALYSIS
            print(f"\n   🧬 VALUE SET INTEGRATION ANALYSIS:")
            print(f"   " + "-" * 40)

            table_data = section.get("table_data", [])
            print(f"   📋 Table data entries: {len(table_data)}")

            if table_data:
                for j, entry in enumerate(table_data):
                    entry_type = entry.get("type", "unknown")
                    section_type = entry.get("section_type", "unknown")

                    print(f"\n   📊 ENTRY {j+1}:")
                    print(f"      🏷️  Type: {entry_type}")
                    print(f"      🔬 Section Type: {section_type}")

                    # Value set fields analysis
                    fields = entry.get("fields", {})
                    print(f"      🧬 Value Set Fields: {len(fields)}")

                    for field_name, field_info in fields.items():
                        value = field_info.get("value", "No value")
                        original_value = field_info.get("original_value", value)
                        has_valueset = field_info.get("has_valueset", False)
                        needs_translation = field_info.get("needs_translation", False)
                        matched_header = field_info.get("matched_header", "None")

                        print(f"\n      🔬 Field: {field_name}")
                        print(f"         💊 Value: '{value}'")
                        if original_value != value:
                            print(f"         📝 Original: '{original_value}'")
                        print(f"         🧬 Has ValueSet: {has_valueset}")
                        print(f"         🌐 Needs Translation: {needs_translation}")
                        print(f"         🏷️  Matched Header: '{matched_header}'")

                        # Value set lookup result
                        if has_valueset and original_value != value:
                            print(
                                f"         ✅ VALUE SET LOOKUP SUCCESS: '{original_value}' -> '{value}'"
                            )
                        elif has_valueset and original_value == value:
                            print(
                                f"         ⚠️  VALUE SET LOOKUP: No translation found for '{value}'"
                            )
                        else:
                            print(f"         ℹ️  No value set lookup required")

            else:
                print(f"   ❌ NO TABLE DATA - Value set integration not applied")

                # Check for PS table HTML as fallback
                ps_table_html = section.get("ps_table_html", "")
                if ps_table_html:
                    print(
                        f"   📄 PS Table HTML length: {len(ps_table_html)} characters"
                    )
                    # Look for "Unknown" indicators
                    if "Unknown" in ps_table_html:
                        print(
                            f"   ⚠️  PS Table contains 'Unknown' labels - value sets not applied"
                        )
                    else:
                        print(f"   ✅ PS Table appears to have proper content")
                else:
                    print(f"   ❌ No PS Table HTML generated")

            print(f"\n" + "-" * 50)

        print(f"\n🏁 PROCESSING COMPLETE")
        print("=" * 80)

        # Final assessment
        total_entries_with_valuesets = 0
        successful_valueset_lookups = 0

        for section in sections:
            table_data = section.get("table_data", [])
            for entry in table_data:
                if entry.get("type") == "html_valueset_entry":
                    total_entries_with_valuesets += 1
                    fields = entry.get("fields", {})
                    for field_info in fields.values():
                        if field_info.get("has_valueset") and field_info.get(
                            "original_value"
                        ) != field_info.get("value"):
                            successful_valueset_lookups += 1

        print(f"\n📈 VALUE SET INTEGRATION SUMMARY:")
        print(f"   Total sections processed: {len(sections)}")
        print(
            f"   Sections with section codes: {len([s for s in sections if s.get('section_code') and s.get('section_code') != 'No code'])}"
        )
        print(f"   Entries with value set support: {total_entries_with_valuesets}")
        print(f"   Successful value set lookups: {successful_valueset_lookups}")

        if total_entries_with_valuesets > 0:
            print(f"   ✅ Value set integration is ACTIVE")
        else:
            print(f"   ❌ Value set integration is NOT WORKING")

    except Exception as e:
        print(f"❌ ERROR during processing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print_clinical_sections_log()
