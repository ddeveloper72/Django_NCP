#!/usr/bin/env python3
"""
Simple test for the dual language function
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

# Import the function
from patient_data.views import _create_dual_language_sections

# Test data
original_result = {
    "success": True,
    "sections": [
        {
            "title": "Medicamentos",
            "content": "Este é um exemplo em português",
            "ps_table_content": "Tabela de medicamentos em português",
        }
    ],
}

translated_result = {
    "success": True,
    "sections": [
        {
            "title": "Medications",
            "content": "This is an example in English",
            "ps_table_content": "Medication table in English",
        }
    ],
}

print("Testing dual language sections...")
result = _create_dual_language_sections(original_result, translated_result, "pt")

if result and result.get("sections"):
    print("✅ SUCCESS: Dual language sections created")
    section = result["sections"][0]
    print(f"Title: {section['title']}")
    if "content" in section and isinstance(section["content"], dict):
        print(f"Original: {section['content'].get('original', 'N/A')}")
        print(f"Translated: {section['content'].get('translated', 'N/A')}")
    else:
        print(f"Content: {section.get('content', 'N/A')}")
else:
    print("❌ FAILED: Could not create dual language sections")
    print(f"Result: {result}")
