#!/usr/bin/env python3
"""
Comprehensive template fix script
1. Fix all remaining 'or' expressions
2. Fix block structure issues
"""

import re
import os


def fix_multiline_or_expressions(file_path):
    """Fix 'or' expressions that span multiple lines"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Pattern for multiline expressions with 'or'
    # This matches: {{ template_translations.original or\n"Original" }}
    pattern = r'\{\{\s*([^}]+?)\s+or\s*\n\s*"([^"]*)"([^}]*?)\}\}'

    def replacement(match):
        variable = match.group(1).strip()
        default = match.group(2)
        rest = match.group(3)  # Any additional content after the default
        return f"{{% if {variable} %}}{{{{{ {variable} }}}}}{{% else %}}{default}{{% endif %}}{rest}"

    content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

    # Also handle single line cases
    def single_line_replacement(match):
        variable = match.group(1).strip()
        default = match.group(2)
        return f"{{% if {variable} %}}{{{{{ {variable} }}}}}{{% else %}}{default}{{% endif %}}"

    pattern2 = r'\{\{\s*([^}]+?)\s+or\s+"([^"]*)"\s*\}\}'
    content = re.sub(pattern2, single_line_replacement, content)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed 'or' expressions in {file_path}")
        return True
    return False


def fix_block_structure(file_path):
    """Fix block structure issues"""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Based on the error, we need to find mismatched endif/endfor
    # Let's track the blocks properly
    fixed_lines = []
    block_stack = []

    for line_num, line in enumerate(lines, 1):
        current_line = line

        # Track block tags
        for_matches = re.findall(r"\{% for [^%]*%\}", line)
        if_matches = re.findall(r"\{% if [^%]*%\}", line)
        endif_matches = re.findall(r"\{% endif %\}", line)
        endfor_matches = re.findall(r"\{% endfor %\}", line)

        # Add opening blocks to stack
        for match in for_matches:
            block_stack.append(("for", line_num))
        for match in if_matches:
            block_stack.append(("if", line_num))

        # Handle closing blocks
        for match in endif_matches:
            if block_stack and block_stack[-1][0] == "for":
                # This endif should be endfor
                current_line = current_line.replace("{% endif %}", "{% endfor %}")
                print(f"Line {line_num}: Fixed 'endif' to 'endfor'")
                block_stack.pop()
            elif block_stack and block_stack[-1][0] == "if":
                block_stack.pop()

        for match in endfor_matches:
            if block_stack and block_stack[-1][0] == "for":
                block_stack.pop()

        fixed_lines.append(current_line)

    # Write back the fixed content
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(fixed_lines)

    print(f"Fixed block structure in {file_path}")
    return True


def main():
    template_file = r"C:\Users\Duncan\VS_Code_Projects\django_ncp\templates\jinja2\patient_data\enhanced_patient_cda.html"

    if os.path.exists(template_file):
        print(f"Processing: {template_file}")

        # Fix remaining 'or' expressions
        or_fixed = fix_multiline_or_expressions(template_file)

        # Fix block structure
        block_fixed = fix_block_structure(template_file)

        if or_fixed or block_fixed:
            print("\n✅ Template fixes completed!")
        else:
            print("\n✅ No fixes needed.")
    else:
        print(f"❌ Template file not found: {template_file}")


if __name__ == "__main__":
    main()
