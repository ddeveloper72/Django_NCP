#!/usr/bin/env python
"""Debug CDA language detection"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.eu_language_detection_service import detect_cda_language
import xml.etree.ElementTree as ET

sample_cda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xml:lang="fr">
    <realmCode code="FR"/>
    <languageCode code="fr-FR"/>
    <title>Synthèse Médicale du Patient</title>
</ClinicalDocument>"""

print("Sample CDA XML:")
print(sample_cda)
print()

root = ET.fromstring(sample_cda)
print("xml:lang attribute:", repr(root.get("xml:lang")))
print("Root tag:", root.tag)
print("Root attrib:", root.attrib)
print()

# Check for languageCode elements
for elem in root.iter():
    if "languageCode" in elem.tag.lower():
        print(f"Found languageCode element: {elem.tag}, code={elem.get('code')}")

print()
print("Detected language:", detect_cda_language(sample_cda))
