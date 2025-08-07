#!/usr/bin/env python3
"""
Quick test to verify the import works with new file location
"""

import os
import sys
import django

# Setup Django
sys.path.append(r"c:\Users\Duncan\VS_Code_Projects\django_ncp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

print("🧪 Testing import from new location...")

try:
    from patient_data.enhanced_cda_display import EnhancedCDADisplayView

    print(
        "✅ SUCCESS: EnhancedCDADisplayView imported from patient_data.enhanced_cda_display"
    )

    # Test creating an instance
    view = EnhancedCDADisplayView()
    print("✅ SUCCESS: Instance created successfully")

    print("🎉 Import path is working correctly!")

except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
except Exception as e:
    print(f"❌ OTHER ERROR: {e}")
