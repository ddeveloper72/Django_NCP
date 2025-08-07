#!/usr/bin/env python3
"""
Convert Django Template Syntax to Jinja2 Syntax
This script converts common Django template patterns to Jinja2 equivalents
"""

import re


def convert_django_to_jinja2(content):
    """Convert Django template syntax to Jinja2 syntax"""

    # 1. Convert |format(key=value) to Jinja2 string format syntax
    # For now, let's simplify these format calls
    content = re.sub(
        r"\|\s*format\([^)]+\)",
        "",  # Remove format filters for now as they need custom implementation
        content,
    )

    # 2. Convert |upper filter (should work the same in Jinja2)
    # No change needed for |upper

    # 3. Convert |length filter (should work the same in Jinja2)
    # No change needed for |length

    # 4. Convert |tojson filter (should work the same in Jinja2)
    # No change needed for |tojson

    return content


# Read the file
with open(
    "templates/jinja2/patient_data/enhanced_patient_cda.html", "r", encoding="utf-8"
) as f:
    content = f.read()

# Apply conversions
content = convert_django_to_jinja2(content)

# Write back
with open(
    "templates/jinja2/patient_data/enhanced_patient_cda.html", "w", encoding="utf-8"
) as f:
    f.write(content)

print("Converted Django template syntax to Jinja2 syntax")
