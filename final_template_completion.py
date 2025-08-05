#!/usr/bin/env python
"""
Complete Template Hardcoded String Replacement - Final Pass
Replaces ALL remaining hardcoded strings with template_translations
"""

import re
import os


def apply_final_template_replacements():
    template_file = "templates/jinja2/patient_data/patient_cda.html"

    with open(template_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Define all remaining replacement patterns with exact context
    replacements = [
        # Simple label replacements for remaining Name/Address instances
        (
            'class="admin-label">Name</div>',
            'class="admin-label">{{ template_translations.name if template_translations else "Name" }}</div>',
        ),
        (
            'class="admin-label">Address</div>',
            'class="admin-label">{{ template_translations.address if template_translations else "Address" }}</div>',
        ),
        # Complex multi-line administrative headers
        (
            ">\n            Administrative Information\n        <",
            '>{{ template_translations.administrative_information if template_translations else "Administrative Information" }}<',
        ),
        (
            "> Legal Authenticator\n                            <",
            '>{{ template_translations.legal_authenticator if template_translations else "Legal Authenticator" }}<',
        ),
        # Medical section headers
        (
            ">\n                                Cabinet Medicale\n                            <",
            '>{{ template_translations.cabinet_medicale if template_translations else "Cabinet Medicale" }}<',
        ),
        (
            ">Free Text\n                            <",
            '>{{ template_translations.free_text if template_translations else "Free Text" }}<',
        ),
        (
            ">Coded Sections\n                            <",
            '>{{ template_translations.coded_sections if template_translations else "Coded Sections" }}<',
        ),
        # Handle any remaining simple patterns
        (
            ">Information<",
            '>{{ template_translations.information if template_translations else "Information" }}<',
        ),
        (
            ">Details<",
            '>{{ template_translations.details if template_translations else "Details" }}<',
        ),
        # Contact information patterns that might remain
        (
            "Email:",
            '{{ template_translations.email if template_translations else "Email" }}:',
        ),
        (
            "Phone:",
            '{{ template_translations.phone if template_translations else "Phone" }}:',
        ),
    ]

    # Apply replacements with detailed logging
    modified = False
    replacement_count = 0

    for pattern, replacement in replacements:
        if pattern in content:
            content = content.replace(pattern, replacement)
            modified = True
            replacement_count += 1
            print(f"✅ Replaced: {pattern[:50]}...")
        else:
            print(f"⚠️  Not found: {pattern[:50]}...")

    # Additional regex-based replacements for complex patterns
    regex_replacements = [
        # Match any remaining hardcoded labels in admin contexts
        (
            r'<div class="admin-label">\s*(Name|Address|Email|Phone|Contact)\s*</div>',
            r'<div class="admin-label">{{ template_translations.\1.lower() if template_translations else "\1" }}</div>',
        ),
    ]

    for pattern, replacement in regex_replacements:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            modified = True
            replacement_count += len(matches)
            print(f"✅ Regex replaced {len(matches)} instances of: {pattern[:30]}...")

    if modified:
        # Create backup
        import shutil

        shutil.copy(template_file, template_file + ".final_backup")

        # Write updated content
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\n🎯 FINAL TEMPLATE UPDATE COMPLETE")
        print(f"📁 Template updated: {template_file}")
        print(f"💾 Backup created: {template_file}.final_backup")
        print(f"🔄 Total replacements made: {replacement_count}")
    else:
        print("ℹ️  No additional hardcoded strings found to replace")

    return modified, replacement_count


def validate_results():
    """Run a quick validation to check remaining hardcoded strings"""
    print("\n🔍 VALIDATION: Checking for remaining hardcoded strings...")

    with open(
        "templates/jinja2/patient_data/patient_cda.html", "r", encoding="utf-8"
    ) as f:
        content = f.read()

    # Check for common hardcoded patterns
    patterns = [
        r'\b(Name|Address|Email|Phone)\b(?!["\']|\s*[|}])',
        r">\s*[A-Z][a-z]+\s+[A-Z][a-z]+\s*<",
        r">\s*(Information|Details|Contact|Organization)\s*<",
    ]

    total_violations = 0
    for pattern in patterns:
        matches = re.finditer(pattern, content)
        violations = []
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.end())
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end].strip()

            # Skip if already wrapped in template translation
            if "template_translations" not in line:
                violations.append((line_num, match.group().strip()))

        if violations:
            print(f"⚠️  Pattern '{pattern[:30]}...' found {len(violations)} violations")
            for line_num, text in violations[:3]:  # Show first 3
                print(f"   Line {line_num}: '{text}'")
            total_violations += len(violations)

    if total_violations == 0:
        print("🎉 SUCCESS: No hardcoded strings detected!")
    else:
        print(f"📊 Found {total_violations} remaining violations")

    return total_violations


if __name__ == "__main__":
    print("=== FINAL TEMPLATE HARDCODED STRING ELIMINATION ===")
    print("🎯 Target: Complete elimination of remaining 13 hardcoded strings")
    print()

    modified, count = apply_final_template_replacements()

    if modified:
        violations = validate_results()

        print(f"\n📈 PROGRESS SUMMARY:")
        print(f"   Replacements made: {count}")
        print(f"   Remaining violations: {violations}")
        print(f"   Success rate: {((13 - violations) / 13) * 100:.1f}%")

    print("\n=== FINAL PASS COMPLETE ===")
