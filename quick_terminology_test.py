#!/usr/bin/env python

"""
Quick test of terminology integration functionality
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")

# Add the project to Python path
sys.path.insert(0, "/c/Users/Duncan/VS_Code_Projects/django_ncp")

try:
    django.setup()
    print("✅ Django setup successful")

    from patient_data.services.ps_table_renderer import PSTableRenderer

    print("✅ PSTableRenderer imported successfully")

    from translation_services.terminology_translator import TerminologyTranslator

    print("✅ TerminologyTranslator imported successfully")

    # Initialize renderer
    renderer = PSTableRenderer(target_language="en")
    print("✅ PSTableRenderer initialized with terminology support")

    # Test basic LOINC lookup
    loinc_display = renderer._get_loinc_display_name("48765-2")
    print(f"✅ LOINC 48765-2 display: {loinc_display}")

    print("\n🎉 All functionality is working!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
