#!/usr/bin/env python3
"""
Comprehensive Jinja2 Template 'or' Operator Fix
Converts all 'variable or "default"' expressions to explicit conditionals
"""

import re
import os


def fix_or_expressions_to_conditionals(file_path):
    """Convert all 'variable or "default"' to explicit if-else conditionals"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Pattern to match: {{ variable or "default" }}
    # Replace with: {% if variable %}{{ variable }}{% else %}default{% endif %}
    pattern = r'\{\{\s*([^}]+?)\s+or\s+"([^"]*)"\s*\}\}'

    def replacement(match):
        variable = match.group(1).strip()
        default = match.group(2)
        return f"{{% if {variable} %}}{{{{{ {variable} }}}}}{{% else %}}{default}{{% endif %}}"

    content = re.sub(pattern, replacement, content)

    # Also handle cases inside JavaScript strings: '{{ variable or "default" }}'
    js_pattern = r"'\{\{\s*([^}]+?)\s+or\s+\"([^\"]*)\"\s*\}\}'"

    def js_replacement(match):
        variable = match.group(1).strip()
        default = match.group(2)
        return f"'{{% if {variable} %}}{{{{{ {variable} }}}}}{{% else %}}{default}{{% endif %}}'"

    content = re.sub(js_pattern, js_replacement, content)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed 'or' expressions in {file_path}")

        # Count changes
        changes_html = len(re.findall(pattern, original_content))
        changes_js = len(re.findall(js_pattern, original_content))
        print(f"  - Fixed {changes_html} HTML expressions")
        print(f"  - Fixed {changes_js} JavaScript expressions")
        print(f"  - Total: {changes_html + changes_js} expressions converted")
        return True
    else:
        print(f"No 'or' expressions found in {file_path}")
        return False


def main():
    template_file = r"C:\Users\Duncan\VS_Code_Projects\django_ncp\templates\jinja2\patient_data\enhanced_patient_cda.html"

    if os.path.exists(template_file):
        print(f"Processing: {template_file}")
        changes_made = fix_or_expressions_to_conditionals(template_file)

        if changes_made:
            print(
                "\n✅ Template 'or' expressions successfully converted to conditionals!"
            )
            print(
                "This ensures compatibility with Django-Jinja2 setups that have issues with 'or' operator."
            )
        else:
            print("\n✅ No 'or' expressions found to convert.")
    else:
        print(f"❌ Template file not found: {template_file}")


if __name__ == "__main__":
    main()
