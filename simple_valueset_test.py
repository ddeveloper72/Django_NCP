#!/usr/bin/env python3
"""
Simple test for Enhanced CDA Processor value set integration
"""

print("Testing Enhanced CDA Processor Value Set Integration")
print("=" * 55)

# Test 1: Check if our new methods exist
try:
    import sys

    sys.path.append(r"c:\Users\Duncan\VS_Code_Projects\django_ncp")

    # Import without Django setup for syntax check
    with open(
        r"c:\Users\Duncan\VS_Code_Projects\django_ncp\patient_data\services\enhanced_cda_processor.py",
        "r",
    ) as f:
        content = f.read()

    # Check for our new methods
    methods_to_check = [
        "_extract_structured_data_with_valusets",
        "_extract_field_with_valueset",
        "_determine_entry_type",
        "_lookup_valueset_term",
    ]

    for method in methods_to_check:
        if f"def {method}" in content:
            print(f"✅ Method {method} found in code")
        else:
            print(f"❌ Method {method} NOT found in code")

    # Check for field mapper integration
    if "field_mapper.get_clinical_section_fields" in content:
        print("✅ Field mapper integration found")
    else:
        print("❌ Field mapper integration NOT found")

    # Check for value set calls
    if "_extract_structured_data_with_valusets" in content:
        print("✅ Value set extraction method is called")
    else:
        print("❌ Value set extraction method is NOT called")

    print("\n🔍 Key Value Set Integration Points:")

    # Count method calls
    valueset_calls = content.count("_extract_structured_data_with_valusets")
    field_mapper_calls = content.count("field_mapper.get_clinical_section_fields")

    print(f"📊 Value set method calls: {valueset_calls}")
    print(f"📊 Field mapper calls: {field_mapper_calls}")

    # Check mapping file exists
    import os

    mapping_file = r"c:\Users\Duncan\VS_Code_Projects\django_ncp\patient_data\services\cda_display_full_mapping.json"
    if os.path.exists(mapping_file):
        print("✅ CDA display mapping file exists")

        # Check mapping content
        import json

        with open(mapping_file, "r") as f:
            mapping_data = json.load(f)

        allergies_section = mapping_data.get("48765-2", {})
        if allergies_section:
            print("✅ Allergies section mapping found")
            fields = allergies_section.get("fields", [])
            valueset_fields = [f for f in fields if f.get("valueSet") == "YES"]
            print(f"📊 Fields with valueSet=YES: {len(valueset_fields)}")
        else:
            print("❌ Allergies section mapping NOT found")
    else:
        print("❌ CDA display mapping file NOT found")

except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 55)
print("Value Set Integration Test Complete")
