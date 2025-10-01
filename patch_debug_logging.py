#!/usr/bin/env python3
"""
Temporary debug patch for the Django view to add enhanced logging.
"""

import os
import sys

# Read the current views.py file
views_file = "c:/Users/Duncan/VS_Code_Projects/django_ncp/patient_data/views.py"

print("=== Patching Django View for Enhanced Debugging ===")

# Add debug logging around the enhanced allergies logic
debug_patch = """
                        # DEBUG: Log enhanced allergies processing
                        enhanced_allergies = match_data.get("enhanced_allergies", [])
                        print(f"[DEBUG] Enhanced allergies in match_data: {len(enhanced_allergies)} items")

                        is_allergies_section = any(
                            keyword in section_title.lower()
                            for keyword in ["allerg", "adverse", "reaction"]
                        )
                        print(f"[DEBUG] Section '{section_title}' is_allergies_section: {is_allergies_section}")

                        if is_allergies_section and enhanced_allergies:
                            print(f"[DEBUG] TRIGGERING enhanced allergies logic for {section_title}")
"""

# Read the file
with open(views_file, "r", encoding="utf-8") as f:
    content = f.read()

# Find the location to insert the debug code
target_line = '                        enhanced_allergies = match_data.get("enhanced_allergies", [])'

if target_line in content:
    # Replace the line with our debug version
    content = content.replace(
        "                        # Check if this is an allergies section and we have enhanced allergies data\n"
        + '                        enhanced_allergies = match_data.get("enhanced_allergies", [])',
        "                        # Check if this is an allergies section and we have enhanced allergies data\n"
        + debug_patch.strip(),
    )

    # Write back to file
    with open(views_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("✓ Debug patch applied to views.py")
    print("Enhanced logging added around enhanced allergies logic")
    print("\nNow reload the page to see debug output in Django logs")

else:
    print("❌ Could not find target line in views.py")
    print("Manual patching may be required")
