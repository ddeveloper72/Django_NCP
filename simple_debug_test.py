#!/usr/bin/env python3
"""
Simple debug test to check CDA processing
"""

import os
import sys
import django

# Setup Django
sys.path.append(r"c:\Users\Duncan\VS_Code_Projects\django_ncp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

print("🚀 Django setup complete")

try:
    from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

    print("✅ Enhanced CDA Processor imported")

    from patient_data.enhanced_cda_display import EnhancedCDADisplayView

    print("✅ Enhanced CDA Display View imported")

    # Test creating instances
    processor = EnhancedCDAProcessor(target_language="lv")
    print("✅ Enhanced CDA Processor instance created")

    view = EnhancedCDADisplayView()
    print("✅ Enhanced CDA Display View instance created")

    # Test getting CDA content
    print("\n🧪 Testing CDA content generation...")
    patient_id = "debug_test_123"

    cda_content = view._get_patient_cda_content(patient_id)
    print(f"✅ CDA content retrieved: {len(cda_content)} characters")

    # Check for section codes
    import re

    section_codes = re.findall(r'data-code="([^"]+)"', cda_content)
    print(f"🏷️  Section codes found: {section_codes}")

    print("\n🎯 Basic functionality test PASSED!")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback

    traceback.print_exc()
