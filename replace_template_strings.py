#!/usr/bin/env python
"""
Complete Template Hardcoded String Replacement
Replaces all remaining hardcoded strings with template_translations
"""

import re
import os


def replace_hardcoded_strings():
    template_file = "templates/jinja2/patient_data/patient_cda.html"

    with open(template_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Define replacement patterns
    replacements = [
        # Basic UI labels with context
        (
            r'<div class="admin-label">Name</div>',
            '<div class="admin-label">{{ template_translations.name if template_translations else "Name" }}</div>',
        ),
        (
            r'<div class="admin-label">Address</div>',
            '<div class="admin-label">{{ template_translations.address if template_translations else "Address" }}</div>',
        ),
        (
            r'<i class="fas fa-envelope"></i> Email:',
            '<i class="fas fa-envelope"></i> {{ template_translations.email if template_translations else "Email" }}:',
        ),
        (
            r'<i class="fas fa-phone"></i> Phone:',
            '<i class="fas fa-phone"></i> {{ template_translations.phone if template_translations else "Phone" }}:',
        ),
        # Header text replacements
        (
            r">Contact<",
            '>{{ template_translations.contact if template_translations else "Contact" }}<',
        ),
        (
            r">Organization<",
            '>{{ template_translations.organization if template_translations else "Organization" }}<',
        ),
        (
            r">Information<",
            '>{{ template_translations.information if template_translations else "Information" }}<',
        ),
        (
            r">Details<",
            '>{{ template_translations.details if template_translations else "Details" }}<',
        ),
    ]

    # Apply replacements
    modified = False
    for pattern, replacement in replacements:
        if pattern in content:
            content = content.replace(pattern, replacement)
            modified = True
            print(f"Replaced: {pattern[:30]}...")

    if modified:
        # Backup original
        import shutil

        shutil.copy(template_file, template_file + ".backup")

        # Write updated content
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Template updated: {template_file}")
        print("Backup created: {}.backup".format(template_file))
    else:
        print("No hardcoded strings found to replace")

    return modified


if __name__ == "__main__":
    print("=== TEMPLATE HARDCODED STRING REPLACEMENT ===")
    replace_hardcoded_strings()
    print("=== COMPLETE ===")
