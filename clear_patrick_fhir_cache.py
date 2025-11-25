#!/usr/bin/env python
"""
Clear FHIR cache for Patrick Murphy to force refresh from Azure FHIR
Run this after FHIR team fixes the medication data
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.core.cache import cache
from patient_data.models import PatientSession

def clear_patrick_fhir_cache():
    """Clear all cached FHIR data for Patrick Murphy"""
    
    print("=" * 80)
    print("FHIR CACHE CLEAR - Patrick Murphy (Patient ID: IE)")
    print("=" * 80)
    
    # Patrick's identifiers
    patient_id = "539305455995368085"  # From Azure FHIR
    azure_patient_id = "9955eb80-a5f9-4c02-aa6c-d1853c76377c"
    
    print(f"\nTarget Patient:")
    print(f"  Business ID: {patient_id}")
    print(f"  Azure UUID: {azure_patient_id}")
    print(f"  Country: Ireland (IE)")
    
    # 1. Clear Django cache keys
    cache_keys_to_clear = [
        f"fhir_patient_{patient_id}",
        f"fhir_patient_{azure_patient_id}",
        f"fhir_bundle_{patient_id}",
        f"fhir_bundle_{azure_patient_id}",
        f"patient_summary_{patient_id}",
        f"patient_summary_{azure_patient_id}",
    ]
    
    print("\n1. Clearing Django cache keys...")
    cleared_count = 0
    for key in cache_keys_to_clear:
        try:
            cache.delete(key)
            cleared_count += 1
            print(f"   ✓ Cleared: {key}")
        except Exception as e:
            print(f"   ✗ Failed to clear {key}: {e}")
    
    print(f"\n   Total cleared: {cleared_count}/{len(cache_keys_to_clear)}")
    
    # 2. Clear PatientSession records
    print("\n2. Clearing PatientSession records...")
    sessions = PatientSession.objects.filter(country_code='IE')
    session_count = sessions.count()
    
    if session_count > 0:
        print(f"   Found {session_count} PatientSession(s) for Ireland")
        for session in sessions:
            print(f"   - Session ID: {session.session_id}, Status: {session.status}")
            session.delete()
            print(f"     ✓ Deleted session {session.session_id}")
    else:
        print("   No PatientSession records found for Ireland")
    
    # 3. Clear any Django sessions containing Patrick's data
    print("\n3. Clearing Django HTTP sessions...")
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    cleared_sessions = 0
    
    for session in active_sessions:
        try:
            session_data = session.get_decoded()
            # Check if session contains Patrick's patient data
            if any(azure_patient_id in str(key) for key in session_data.keys()):
                session.delete()
                cleared_sessions += 1
                print(f"   ✓ Cleared session with Patrick's data")
        except Exception:
            # Skip sessions we can't decode
            pass
    
    print(f"   Total sessions cleared: {cleared_sessions}")
    
    print("\n" + "=" * 80)
    print("CACHE CLEAR COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Wait for FHIR team to fix Patrick's MedicationStatement")
    print("2. Navigate to Patrick's patient page in the browser")
    print("3. Django will fetch fresh data from Azure FHIR")
    print("4. Verify medication displays with proper name and details")
    print("\nExpected Result:")
    print("✅ Medication name displays (e.g., 'Enalapril')")
    print("✅ ATC code resolved via CTS agent")
    print("✅ Dosage information displays (strength, route, schedule)")
    print("✅ All fields populated (no 'Not specified')")
    print("=" * 80)

if __name__ == "__main__":
    clear_patrick_fhir_cache()
