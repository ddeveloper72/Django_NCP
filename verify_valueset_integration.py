#!/usr/bin/env python3
"""
Basic Value Set Integration Verification
"""

import os
import sys
import json

print("Value Set Integration Verification")
print("=" * 40)

# Verify enhanced_cda_processor.py has our changes
processor_file = r"c:\Users\Duncan\VS_Code_Projects\django_ncp\patient_data\services\enhanced_cda_processor.py"
if os.path.exists(processor_file):
    with open(processor_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for key methods
    key_methods = [
        "_extract_structured_data_with_valusets",
        "_extract_field_with_valueset",
        "_lookup_valueset_term",
        "_determine_entry_type",
    ]

    all_methods_found = True
    for method in key_methods:
        if f"def {method}" in content:
            print(f"[OK] Method {method} found")
        else:
            print(f"[ERROR] Method {method} missing")
            all_methods_found = False

    # Check if method is called
    if "_extract_structured_data_with_valusets(" in content:
        print("[OK] Value set method is called in main processing")
    else:
        print("[ERROR] Value set method not called")
        all_methods_found = False

    # Check field mapper integration
    if "field_mapper.get_clinical_section_fields" in content:
        print("[OK] Field mapper integration found")
    else:
        print("[ERROR] Field mapper integration missing")
        all_methods_found = False

    if all_methods_found:
        print("\n[SUCCESS] All value set integration components are in place")
    else:
        print("\n[WARNING] Some integration components are missing")

else:
    print("[ERROR] Enhanced CDA processor file not found")

# Verify mapping file exists
mapping_file = r"c:\Users\Duncan\VS_Code_Projects\django_ncp\patient_data\services\cda_display_full_mapping.json"
if os.path.exists(mapping_file):
    with open(mapping_file, "r", encoding="utf-8") as f:
        mapping_data = json.load(f)

    # Check allergies section
    allergies_section = mapping_data.get("48765-2", {})
    if allergies_section:
        fields = allergies_section.get("fields", [])
        valueset_fields = [f for f in fields if f.get("valueSet") == "YES"]
        translation_fields = [f for f in fields if f.get("translation") == "YES"]

        print(f"[OK] Allergies section has {len(fields)} fields")
        print(f"[OK] Fields with valueSet=YES: {len(valueset_fields)}")
        print(f"[OK] Fields with translation=YES: {len(translation_fields)}")

        # Show key fields
        for field in fields[:5]:  # First 5 fields
            label = field.get("label", "Unknown")
            has_valueset = field.get("valueSet") == "YES"
            needs_translation = field.get("translation") == "YES"
            xpath = field.get("xpath", "No XPath")

            print(f"  Field: {label}")
            if has_valueset:
                print(f"    ValueSet: YES")
            if needs_translation:
                print(f"    Translation: YES")

    else:
        print("[ERROR] Allergies section not found in mapping")
else:
    print("[ERROR] CDA mapping file not found")

print("\nValue set integration is ready for testing with Django environment")
print(
    "Next step: Test with actual Malta PS document to verify clinical terminology translation"
)
