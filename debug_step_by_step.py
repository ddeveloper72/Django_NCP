#!/usr/bin/env python
"""Debug CDA language detection step by step"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.eu_language_detection_service import (
    EULanguageDetectionService,
)
import xml.etree.ElementTree as ET

sample_cda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xml:lang="fr">
    <realmCode code="FR"/>
    <languageCode code="fr-FR"/>
    <title>Synthèse Médicale du Patient</title>
</ClinicalDocument>"""

print("=== Manual step-by-step debugging ===")
service = EULanguageDetectionService()

root = ET.fromstring(sample_cda)
print("All attributes:", root.attrib)

xml_lang_attrs = [
    "xml:lang",
    "language",
    "lang",
    "{http://www.w3.org/XML/1998/namespace}lang",
]

for attr in xml_lang_attrs:
    value = root.get(attr)
    print(f"Checking {attr}: {repr(value)}")
    if value:
        normalized = service._normalize_language_code(value)
        print(f"  Normalized to: {normalized}")
        break

print()
print("=== Checking languageCode elements ===")
for elem in root.iter():
    print(f"Element: {elem.tag}")
    if "languageCode" in elem.tag.lower():
        code = elem.get("code")
        print(f"  Found languageCode element with code: {repr(code)}")
        if code:
            normalized = service._normalize_language_code(code)
            print(f"  Normalized to: {normalized}")

print()
print("Final detection result:", service.detect_from_cda_metadata(sample_cda))
