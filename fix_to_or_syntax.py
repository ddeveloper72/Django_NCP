#!/usr/bin/env python3
"""
Fix template_translations syntax using simple 'or' operator
"""

import re
import os


def fix_template_to_or_syntax(file_path):
    """Fix template_translations using simple 'or' operator"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Pattern to match: template_translations.field | default("default")
    # Replace with: template_translations.field or "default"
    pattern = r'template_translations\.(\w+)\s*\|\s*default\("([^"]*)"\)'

    def replacement(match):
        field = match.group(1)
        default = match.group(2)
        return f'template_translations.{field} or "{default}"'

    content = re.sub(pattern, replacement, content)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed template_translations syntax in {file_path}")

        # Count changes
        changes = len(re.findall(pattern, original_content))
        print(f"  - Fixed {changes} template_translations expressions")
    else:
        print(f"No changes needed in {file_path}")


def main():
    template_file = r"C:\Users\Duncan\VS_Code_Projects\django_ncp\templates\jinja2\patient_data\enhanced_patient_cda.html"

    if os.path.exists(template_file):
        print(f"Processing: {template_file}")
        fix_template_to_or_syntax(template_file)
        print("Template translations syntax fix completed!")
    else:
        print(f"Template file not found: {template_file}")


if __name__ == "__main__":
    main()
