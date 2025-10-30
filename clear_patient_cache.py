#!/usr/bin/env python
"""
Clear cached data for a patient session to force re-processing with updated pipeline.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientDataCache, PatientSession
from django.contrib.sessions.models import Session

patient_id = '8985103851'

print(f"=== CLEARING CACHE FOR PATIENT {patient_id} ===\n")

# Clear PatientDataCache
cache_count = PatientDataCache.objects.filter(session__session_id=patient_id).delete()[0]
print(f"✅ Deleted {cache_count} PatientDataCache records")

# Find and clear session data (but keep the session itself)
from django.utils import timezone
sessions = Session.objects.filter(expire_date__gt=timezone.now())

for session in sessions:
    session_data = session.get_decoded()
    session_key_name = f'patient_match_{patient_id}'
    
    if session_key_name in session_data:
        # Clear enhanced data but keep basic patient info
        patient_data = session_data[session_key_name]
        
        # Remove cached clinical data
        keys_to_clear = [
            'enhanced_procedures',
            'enhanced_medications', 
            'enhanced_allergies',
            'enhanced_problems',
            'enhanced_vital_signs',
            'enhanced_immunizations',
            'enhanced_clinical_data'
        ]
        
        cleared = []
        for key in keys_to_clear:
            if key in patient_data:
                del patient_data[key]
                cleared.append(key)
        
        if cleared:
            session_data[session_key_name] = patient_data
            session.session_data = session.encode(session_data)
            session.save()
            print(f"✅ Cleared session data: {', '.join(cleared)}")

print(f"\n🔄 Cache cleared! Now refresh the page: http://127.0.0.1:8000/patients/cda/{patient_id}/L3/")
print("   The pipeline will re-process the CDA with the fixed code.")
