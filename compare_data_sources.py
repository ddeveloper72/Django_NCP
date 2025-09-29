#!/usr/bin/env python
"""Compare data sources: session vs direct patient access"""
import os
import sys

import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.contrib.sessions.models import Session

from patient_data.simplified_clinical_view import SimplifiedDataExtractor

print("=== AVAILABLE SESSIONS ===")
sessions = Session.objects.all()[:5]  # Show first 5 sessions
for session in sessions:
    session_data = session.get_decoded()
    patient_id = session_data.get("patient_id", "Unknown")
    print(
        f"Session: {session.session_key} -> Patient: {patient_id} (expires: {session.expire_date})"
    )

print(f"\nTotal sessions: {Session.objects.count()}")

print("\n=== DIRECT PATIENT DATA ACCESS ===")
# Test our working patient 117302
try:
    extractor = SimplifiedDataExtractor()
    data = extractor.extract_for_patient("117302")

    if data:
        personal_info = data.get("personal_info", {})
        name = personal_info.get("name", "Unknown")
        print(f"✅ Direct access to patient 117302: {name}")

        clinical_sections = data.get("clinical_sections", {})
        if clinical_sections:
            print(f"🏥 Clinical sections: {len(clinical_sections)}")
            for section_name, section_data in clinical_sections.items():
                if section_data and isinstance(section_data, list):
                    print(f"   - {section_name}: {len(section_data)} items")

        print("\n📊 Data comparison:")
        print(
            f"   Session-based URL: /patients/cda/SESSION_ID/L3/ (requires valid session)"
        )
        print(
            f"   Direct patient URL: /patients/cda/enhanced_display/117302/ (works directly)"
        )
        print(
            f"   Both should show the same patient data if session contains patient 117302"
        )

    else:
        print("❌ No data found for patient 117302")

except Exception as e:
    print(f"❌ Error accessing patient data: {e}")
    import traceback

    traceback.print_exc()
