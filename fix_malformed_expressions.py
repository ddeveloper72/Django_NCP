#!/usr/bin/env python3
"""
Fix malformed template expressions created by automatic script
"""

import re
import os


def fix_malformed_expressions(file_path):
    """Fix malformed expressions like {{{'variable'}}} to {{ variable }}"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Pattern to match: {{{'variable'}}}
    # Replace with: {{ variable }}
    pattern = r"\{\{\{\'([^\']+)\'\}\}\}"
    content = re.sub(pattern, r"{{ \1 }}", content)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed malformed expressions in {file_path}")

        # Count changes
        changes = len(re.findall(pattern, original_content))
        print(f"  - Fixed {changes} malformed expressions")
        return True
    return False


def main():
    template_file = r"C:\Users\Duncan\VS_Code_Projects\django_ncp\templates\jinja2\patient_data\enhanced_patient_cda.html"

    if os.path.exists(template_file):
        print(f"Processing: {template_file}")
        fixed = fix_malformed_expressions(template_file)

        if fixed:
            print("\n✅ Malformed expressions fixed!")
        else:
            print("\n✅ No malformed expressions found.")
    else:
        print(f"❌ Template file not found: {template_file}")


if __name__ == "__main__":
    main()
