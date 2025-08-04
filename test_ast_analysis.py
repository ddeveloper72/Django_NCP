#!/usr/bin/env python3
"""
Check what classes are actually defined in services.py
"""
import sys
import os
import ast

# Add project to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

print("Analyzing services.py source code...")

# Parse the AST to see what classes are defined
try:
    with open("patient_data/services.py", "r") as f:
        source = f.read()

    tree = ast.parse(source)

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)

    print(f"Classes found in AST: {classes}")

    # Now try the actual import
    print("\nTrying actual import...")
    import patient_data.services as services

    actual_classes = [
        attr for attr in dir(services) if isinstance(getattr(services, attr), type)
    ]
    print(f"Classes available after import: {actual_classes}")

    if "PatientSearchResult" in classes and "PatientSearchResult" not in actual_classes:
        print("⚠️  PatientSearchResult is in the source but not available after import!")
        print("This suggests an execution error during module loading.")

        # Try to find where the error might be
        print("\nTrying to import with more verbose error handling...")
        try:
            import importlib

            importlib.reload(services)
        except Exception as e:
            print(f"Error during reload: {e}")
            import traceback

            traceback.print_exc()

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
