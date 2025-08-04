#!/usr/bin/env python3
"""
Test the patient details view loading
"""
import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

print("Testing views.py import...")

try:
    import patient_data.views

    print("✓ Views module imported successfully")

    # Test if the patient_details_view function exists
    if hasattr(patient_data.views, "patient_details_view"):
        print("✓ patient_details_view function found")
    else:
        print("✗ patient_details_view function not found")

    # Check for any obvious syntax issues
    import py_compile

    py_compile.compile("patient_data/views.py", doraise=True)
    print("✓ views.py compiles without syntax errors")

except Exception as e:
    print(f"✗ Error importing views: {e}")
    import traceback

    traceback.print_exc()
