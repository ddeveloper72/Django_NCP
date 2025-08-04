#!/usr/bin/env python3
"""
Test imports from services.py to find the failing import
"""
import sys
import os

# Add project to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

print("Testing imports from services.py...")

# Test each import individually
imports_to_test = [
    "import os",
    "import re",
    "import xml.etree.ElementTree as ET",
    "from typing import Dict, List, Optional, Tuple",
    "from dataclasses import dataclass",
    "from datetime import datetime",
    "import logging",
]

for import_line in imports_to_test:
    try:
        exec(import_line)
        print(f"✓ {import_line}")
    except Exception as e:
        print(f"✗ {import_line} - Error: {e}")

# Now try to import the full services module with verbose error handling
print("\nTrying full services.py import with error tracing...")

try:
    import patient_data.services

    print("✓ Full import successful")
except Exception as e:
    print(f"✗ Full import failed: {e}")
    import traceback

    traceback.print_exc()

# Try importing with sys.path manipulation
print("\nTrying with explicit sys.path...")
try:
    sys.path.insert(0, os.path.join(os.getcwd(), "patient_data"))
    import services

    print("✓ Direct services import successful")
    print(f"Available: {[attr for attr in dir(services) if not attr.startswith('_')]}")
except Exception as e:
    print(f"✗ Direct services import failed: {e}")
    import traceback

    traceback.print_exc()
