#!/usr/bin/env python3
"""
Direct import test to find the issue
"""
import sys
import os

# Add project to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

print("Testing direct import of services.py content...")

try:
    # Read and execute the services.py content directly
    with open("patient_data/services.py", "r") as f:
        content = f.read()

    # Check if PatientSearchResult is in the file content
    if "class PatientSearchResult" in content:
        print("✓ PatientSearchResult class found in file content")
    else:
        print("✗ PatientSearchResult class NOT found in file content")

    # Try to execute just the class definition part
    exec_globals = {}
    exec_locals = {}

    # Import required modules for execution
    from dataclasses import dataclass
    from typing import Dict

    exec_globals.update({"dataclass": dataclass, "Dict": Dict})

    # Extract just the class definition
    class_def = """
@dataclass
class PatientSearchResult:
    file_path: str
    country_code: str
    confidence_score: float
    patient_data: Dict
    cda_content: str
"""

    exec(class_def, exec_globals, exec_locals)

    if "PatientSearchResult" in exec_locals:
        print("✓ PatientSearchResult class executes successfully")
        PSR = exec_locals["PatientSearchResult"]

        # Test the constructor
        test_obj = PSR(
            file_path="test",
            country_code="GB",
            confidence_score=0.9,
            patient_data={"test": "data"},
            cda_content="<test/>",
        )
        print(f"✓ Constructor works: {test_obj.file_path}")
    else:
        print("✗ PatientSearchResult class failed to execute")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
