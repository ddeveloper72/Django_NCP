import re

# Read the file
with open(
    "templates/jinja2/patient_data/enhanced_patient_cda.html", "r", encoding="utf-8"
) as f:
    content = f.read()

# Replace all instances of | default("...") with or "..."
content = re.sub(r'\|\s*default\("([^"]+)"\)', r'or "\1"', content, flags=re.MULTILINE)

# Write back
with open(
    "templates/jinja2/patient_data/enhanced_patient_cda.html", "w", encoding="utf-8"
) as f:
    f.write(content)

print('Fixed all | default("...") to use or "..." syntax')
