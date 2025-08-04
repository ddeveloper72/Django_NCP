#!/usr/bin/env python3
"""
Minimal test to check services.py import
"""
import sys
import os

# Add project to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

try:
    print("Trying to import patient_data.services...")
    import patient_data.services as services

    print(f"Import successful!")
    print(
        f"Available attributes: {[attr for attr in dir(services) if not attr.startswith('_')]}"
    )

    # Try to access PatientSearchResult
    if hasattr(services, "PatientSearchResult"):
        print("✓ PatientSearchResult found!")
        PSR = services.PatientSearchResult
        print(f"PatientSearchResult type: {type(PSR)}")
    else:
        print("✗ PatientSearchResult NOT found!")

    # Check if there are any syntax errors by trying to compile the file
    import py_compile

    py_compile.compile("patient_data/services.py", doraise=True)
    print("✓ services.py compiles without errors")

except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback

    traceback.print_exc()
