#!/usr/bin/env python3
"""
Debug the complete data flow from Enhanced CDA Processor to Template
"""

import os
import sys
import json
import django

print("🚀 Starting debug script...")

# Setup Django
sys.path.append(r"c:\Users\Duncan\VS_Code_Projects\django_ncp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

print("⚙️ Setting up Django...")
django.setup()

print("📦 Importing services...")
from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
from patient_data.enhanced_cda_display import EnhancedCDADisplayView

print("✅ All imports successful!")


def debug_complete_data_flow():
    """Debug the complete data flow"""

    print("=" * 80)
    print("DEBUGGING COMPLETE CDA PROCESSING DATA FLOW")
    print("=" * 80)

    try:
        # Step 1: Get mock CDA content
        view = EnhancedCDADisplayView()
        patient_id = "debug_test_123"

        print(f"\n📄 STEP 1: Getting mock CDA content")
        print("-" * 50)

        cda_content = view._get_patient_cda_content(patient_id)
        print(f"✅ CDA content length: {len(cda_content)} characters")
        print(f"📄 Content type: HTML CDA")

        # Check for section codes
        import re

        section_codes = re.findall(r'data-code="([^"]+)"', cda_content)
        print(f"🏷️  Section codes in content: {section_codes}")

        # Step 2: Process with Enhanced CDA Processor
        print(f"\n🔧 STEP 2: Processing with Enhanced CDA Processor")
        print("-" * 50)

        processor = EnhancedCDAProcessor(target_language="lv")

        result = processor.process_clinical_sections(
            cda_content=cda_content, source_language="fr"
        )

        print(f"✅ Processing completed")
        print(f"📊 Result keys: {list(result.keys())}")
        print(f"🏥 Success: {result.get('success', False)}")
        print(f"📋 Sections count: {result.get('sections_count', 0)}")
        print(f"🔬 Content type: {result.get('content_type', 'unknown')}")

        # Step 3: Analyze each section in detail
        print(f"\n🔍 STEP 3: Detailed Section Analysis")
        print("=" * 60)

        sections = result.get("sections", [])

        for i, section in enumerate(sections):
            section_code = section.get("section_code", "No code")
            title = section.get("title", {})
            has_ps_table = section.get("has_ps_table", False)
            table_data = section.get("table_data", [])

            if isinstance(title, dict):
                original_title = title.get("original", "No title")
            else:
                original_title = str(title)

            print(f"\n📋 SECTION {i+1}: {section_code}")
            print("-" * 40)
            print(f"   Title: '{original_title}'")
            print(f"   Has PS Table: {has_ps_table}")
            print(f"   Table Data Entries: {len(table_data)}")

            # Focus on sections with expected value sets
            if section_code in ["48765-2", "10160-0", "11450-4"]:
                print(f"\n   🧬 VALUE SET ANALYSIS:")

                if table_data:
                    for j, entry in enumerate(table_data[:2]):  # First 2 entries
                        entry_type = entry.get("type", "unknown")
                        fields = entry.get("fields", {})

                        print(f"\n   📊 Entry {j+1}:")
                        print(f"      Type: {entry_type}")
                        print(f"      Fields: {len(fields)}")

                        # Show field details
                        for field_name, field_info in fields.items():
                            value = field_info.get("value", "No value")
                            original = field_info.get("original_value", value)
                            has_valueset = field_info.get("has_valueset", False)
                            matched_header = field_info.get("matched_header", "None")

                            print(f"\n      🔬 {field_name}:")
                            print(f"         Value: '{value}'")
                            print(f"         Original: '{original}'")
                            print(f"         Has ValueSet: {has_valueset}")
                            print(f"         Matched Header: '{matched_header}'")

                            if has_valueset and original != value:
                                print(
                                    f"         ✅ VALUE SET SUCCESS: '{original}' -> '{value}'"
                                )
                            elif has_valueset:
                                print(f"         ⚠️  VALUE SET NO CHANGE: '{value}'")
                else:
                    print(f"   ❌ NO TABLE DATA - Check field mapping!")

                    # Check if PS table HTML exists
                    ps_table_html = section.get("ps_table_html", "")
                    if ps_table_html:
                        print(f"   📄 PS Table HTML exists: {len(ps_table_html)} chars")
                        if "Unknown" in ps_table_html:
                            print(
                                f"   ⚠️  PS Table contains 'Unknown' - value sets not applied"
                            )
            else:
                print(f"   ℹ️  Section {section_code} not configured for value sets")

        # Step 4: Check what template would receive
        print(f"\n📤 STEP 4: Template Context Analysis")
        print("=" * 60)

        # Simulate what gets passed to template
        sections_with_table_data = [s for s in sections if s.get("table_data")]
        sections_with_ps_table = [s for s in sections if s.get("has_ps_table")]

        print(f"   Sections with table_data: {len(sections_with_table_data)}")
        print(f"   Sections with has_ps_table: {len(sections_with_ps_table)}")

        # Show what template would see for allergies section
        allergy_section = None
        for section in sections:
            if section.get("section_code") == "48765-2":
                allergy_section = section
                break

        if allergy_section:
            print(f"\n   🔍 ALLERGIES SECTION TEMPLATE DATA:")
            print(f"      Section Code: {allergy_section.get('section_code')}")
            print(f"      Has PS Table: {allergy_section.get('has_ps_table')}")

            table_data = allergy_section.get("table_data", [])
            print(f"      Table Data: {len(table_data)} entries")

            if table_data:
                first_entry = table_data[0]
                fields = first_entry.get("fields", {})
                print(f"      First Entry Fields: {list(fields.keys())}")

                # Show what template lookups would find
                allergen_value = fields.get("Allergen DisplayName", {}).get(
                    "value", "NOT FOUND"
                )
                reaction_value = fields.get("Reaction DisplayName", {}).get(
                    "value", "NOT FOUND"
                )

                print(f"      Template would show:")
                print(f"         Allergen: '{allergen_value}'")
                print(f"         Reaction: '{reaction_value}'")
            else:
                print(f"      ❌ Template would show fallback PS HTML")

        # Step 5: Summary
        print(f"\n🏁 SUMMARY")
        print("=" * 60)

        total_value_set_entries = 0
        for section in sections:
            table_data = section.get("table_data", [])
            for entry in table_data:
                if entry.get("type") == "html_valueset_entry":
                    total_value_set_entries += 1

        print(f"   Total sections: {len(sections)}")
        print(f"   Value set entries: {total_value_set_entries}")

        if total_value_set_entries > 0:
            print(f"   ✅ VALUE SET INTEGRATION IS WORKING!")
            print(f"   📄 Template should now show translated medical terms")
        else:
            print(f"   ❌ VALUE SET INTEGRATION NOT WORKING")
            print(f"   📄 Template will show fallback 'Unknown' labels")

        # Save debug data to file for inspection
        debug_data = {
            "processing_result": result,
            "sections_summary": [
                {
                    "section_code": s.get("section_code"),
                    "title": s.get("title"),
                    "has_table_data": len(s.get("table_data", [])),
                    "table_data_sample": s.get("table_data", [])[:1],
                }
                for s in sections
            ],
        }

        with open("debug_cda_processing.json", "w") as f:
            json.dump(debug_data, f, indent=2, default=str)

        print(f"\n📄 Debug data saved to: debug_cda_processing.json")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_complete_data_flow()
