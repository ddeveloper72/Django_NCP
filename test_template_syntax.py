#!/usr/bin/env python3
"""
Jinja2 Template Syntax Validator
Tests Django Jinja2 templates for syntax errors before rendering
"""

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
import os
import sys
import re


def check_block_structure(template_path):
    """Check for proper block tag structure"""
    print("\n🔍 Checking template block structure...")

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")

    # Track block tags
    block_stack = []
    issues_found = []

    # Define block pairs
    block_pairs = {
        "for": "endfor",
        "if": "endif",
        "block": "endblock",
        "macro": "endmacro",
        "call": "endcall",
        "filter": "endfilter",
        "set": "endset",
        "raw": "endraw",
    }

    for line_num, line in enumerate(lines, 1):
        # Find all Jinja2 tags in the line
        tags = re.findall(r"\{%\s*(\w+).*?%\}", line)

        for tag in tags:
            if tag in block_pairs:
                # Opening block tag
                block_stack.append((tag, line_num))
            elif tag.startswith("end"):
                # Closing block tag
                expected_start = tag[3:]  # Remove 'end' prefix

                if not block_stack:
                    issues_found.append(
                        f"Line {line_num}: Unexpected closing tag '{tag}' - no matching opening tag"
                    )
                else:
                    last_tag, last_line = block_stack[-1]
                    if last_tag == expected_start:
                        block_stack.pop()  # Correct match
                    else:
                        expected_end = block_pairs[last_tag]
                        issues_found.append(
                            f"Line {line_num}: Found '{tag}' but expected '{expected_end}' to close '{last_tag}' from line {last_line}"
                        )
            elif tag in ["else", "elif", "empty"]:
                # These must be inside appropriate blocks
                if not block_stack:
                    issues_found.append(
                        f"Line {line_num}: '{tag}' found outside of block structure"
                    )
                elif tag == "empty" and block_stack[-1][0] != "for":
                    issues_found.append(
                        f"Line {line_num}: 'empty' can only be used inside 'for' loops"
                    )

    # Check for unclosed blocks
    if block_stack:
        for tag, line_num in block_stack:
            expected_end = block_pairs[tag]
            issues_found.append(
                f"Unclosed '{tag}' block started on line {line_num} - missing '{expected_end}'"
            )

    if issues_found:
        print("❌ Block structure issues found:")
        for issue in issues_found:
            print(f"  {issue}")
        return False
    else:
        print("✅ Block structure is correct")
        return True


def check_common_django_jinja2_issues(template_path):
    """Check for common Django to Jinja2 conversion issues"""
    print("\n🔍 Checking for common Django/Jinja2 compatibility issues...")

    issues_found = []

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")

    # Check for Django-specific tags
    django_tags = [
        (
            r"{% load \w+ %}",
            "Django load tag found - remove or replace with Jinja2 equivalent",
        ),
        (
            r"{% url [^}]+ %}",
            "Django url tag found - replace with hardcoded URL or url_for()",
        ),
        (
            r"\|\s*default\([^)]+\)",
            "Django default filter with args - use explicit conditionals instead",
        ),
        (
            r"\{\{\s*[^}]+\s+or\s+\"[^\"]*\"\s*\}\}",
            'Potential "or" operator issue - use explicit conditionals for better compatibility',
        ),
    ]

    for line_num, line in enumerate(lines, 1):
        for pattern, message in django_tags:
            if re.search(pattern, line):
                issues_found.append(f"Line {line_num}: {message}")
                issues_found.append(f"  Content: {line.strip()}")

    if issues_found:
        print("⚠️  Potential issues found:")
        for issue in issues_found:
            print(f"  {issue}")
        return False
    else:
        print("✅ No common Django/Jinja2 issues detected")
        return True


def test_template_syntax(template_path):
    """Test a Jinja2 template for syntax errors"""
    try:
        # Get directory and filename
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)

        # Create Jinja2 environment
        env = Environment(loader=FileSystemLoader(template_dir))

        # Try to load and parse the template
        template = env.get_template(template_file)

        # Try to render with empty context to catch runtime errors
        try:
            # Create a minimal context to test rendering
            test_context = {
                "template_translations": {},
                "target_language": "en",
                "enhanced_sections": {"sections": [], "error": None},
                "section": {"section_code": "48765-2", "table_data": []},
                "entry": {"fields": {}},
                "field_name": "test",
                "field_info": {},
            }
            rendered = template.render(**test_context)
            print(f"✅ Template syntax is valid and renders successfully!")
            print(f"Template: {template_path}")
            return True

        except Exception as render_error:
            print(f"⚠️  Template syntax is valid but rendering failed:")
            print(f"File: {template_path}")
            print(f"Render Error: {render_error}")
            print(f"Error type: {type(render_error).__name__}")
            return False

    except TemplateSyntaxError as e:
        print(f"❌ Jinja2 Template Syntax Error:")
        print(f"File: {template_path}")
        print(f"Line: {e.lineno}")
        print(f"Error: {e.message}")
        return False

    except Exception as e:
        print(f"❌ General Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    # Test the enhanced patient CDA template
    template_path = os.path.join(
        "templates", "jinja2", "patient_data", "enhanced_patient_cda.html"
    )

    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        sys.exit(1)

    print("Testing Jinja2 Template Syntax...")
    print("=" * 50)

    # First check for block structure
    block_structure_ok = check_block_structure(template_path)

    # Then check for common issues
    issues_clean = check_common_django_jinja2_issues(template_path)

    # Finally test syntax
    syntax_valid = test_template_syntax(template_path)

    if syntax_valid and issues_clean and block_structure_ok:
        print("\n🎉 Template is ready for rendering!")
        sys.exit(0)
    else:
        print("\n💥 Fix syntax errors or compatibility issues before using template")
        sys.exit(1)
