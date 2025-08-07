#!/usr/bin/env python3
"""
Quick test to verify Enhanced CDA Field Mapper is working
"""

import os
import sys

# Test field mapper without Django to see if it loads the mappings
sys.path.append(r"c:\Users\Duncan\VS_Code_Projects\django_ncp")

try:
    from patient_data.services.enhanced_cda_field_mapper import EnhancedCDAFieldMapper

    print("Testing Enhanced CDA Field Mapper")
    print("=" * 40)

    # Create field mapper
    field_mapper = EnhancedCDAFieldMapper()

    print(f"✅ Field mapper created")
    print(f"📋 Total field mappings loaded: {len(field_mapper.field_mappings)}")
    print(f"🗂️  Section mappings indexed: {len(field_mapper.section_mappings)}")

    # Test specific sections
    test_sections = ["48765-2", "10160-0", "11450-4"]

    for section_code in test_sections:
        print(f"\n🔍 Testing section {section_code}:")

        # Get section mapping
        section_mapping = field_mapper.get_section_mapping(section_code)
        if section_mapping:
            section_name = section_mapping.get("section", "Unknown")
            print(f"   Section name: {section_name}")

            # Get clinical fields
            clinical_fields = field_mapper.get_clinical_section_fields(section_code)
            print(f"   Clinical fields: {len(clinical_fields)}")

            for i, field in enumerate(clinical_fields[:3]):  # Show first 3 fields
                label = field.get("label", "No label")
                xpath = field.get("xpath", "No xpath")
                has_valueset = field.get("valueSet", "NO")
                needs_translation = field.get("translation", "NO")

                print(f"      Field {i+1}: {label}")
                print(f"         XPath: {xpath}")
                print(f"         ValueSet: {has_valueset}")
                print(f"         Translation: {needs_translation}")
        else:
            print(f"   ❌ No mapping found for section {section_code}")

    # Show available section codes
    print(f"\n📊 All available section codes:")
    for code, mapping in field_mapper.section_mappings.items():
        section_name = mapping.get("section", "Unknown")
        field_count = len(mapping.get("fields", []))
        print(f"   {code}: {section_name} ({field_count} fields)")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
