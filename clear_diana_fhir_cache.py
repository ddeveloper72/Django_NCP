#!/usr/bin/env python
"""
Clear FHIR cache for Diana Ferreira to force refresh from Azure FHIR
This will ensure we get the latest composition (v6+) with medications section
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.core.cache import cache
from patient_data.models import PatientSession

def clear_diana_fhir_cache():
    """Clear all cached FHIR data for Diana Ferreira"""
    
    print("=" * 80)
    print("FHIR CACHE CLEAR - Diana Ferreira (Patient ID: 2-1234-W7)")
    print("=" * 80)
    
    # Diana's identifiers
    patient_id = "2-1234-W7"
    azure_patient_id = "dbca9120-c667-41c1-82bc-7f06d3cc709d"
    composition_id = "78f27b51-7da0-4249-aaf8-ba7d43fdf18f"
    
    print(f"\nTarget Patient:")
    print(f"  Business ID: {patient_id}")
    print(f"  Azure UUID: {azure_patient_id}")
    print(f"  Composition: {composition_id}")
    
    # 1. Clear Django cache keys
    cache_keys_to_clear = [
        f"fhir_patient_{patient_id}",
        f"fhir_patient_{azure_patient_id}",
        f"fhir_composition_{composition_id}",
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
    sessions = PatientSession.objects.filter(country_code='PT')
    session_count = sessions.count()
    
    if session_count > 0:
        print(f"   Found {session_count} PatientSession(s) for Portugal")
        for session in sessions:
            print(f"   - Session ID: {session.session_id}, Status: {session.status}")
            session.delete()
            print(f"     ✓ Deleted session {session.session_id}")
    else:
        print("   No PatientSession records found for Portugal")
    
    # 3. Clear any Django sessions containing Diana's data
    print("\n3. Clearing Django HTTP sessions...")
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    cleared_sessions = 0
    
    for session in active_sessions:
        try:
            session_data = session.get_decoded()
            # Check if session contains Diana's patient data
            if any(patient_id in str(key) for key in session_data.keys()):
                session.delete()
                cleared_sessions += 1
                print(f"   ✓ Cleared session with Diana's data")
        except Exception as e:
            # Skip sessions we can't decode
            pass
    
    print(f"   Total sessions cleared: {cleared_sessions}")
    
    # 4. Clear FHIR-related cache patterns
    print("\n4. Clearing wildcard cache patterns...")
    patterns = [
        "fhir_*",
        "patient_*",
        "composition_*",
    ]
    
    for pattern in patterns:
        try:
            cache.delete_pattern(pattern)
            print(f"   ✓ Cleared pattern: {pattern}")
        except AttributeError:
            print(f"   ℹ Cache backend doesn't support delete_pattern for: {pattern}")
        except Exception as e:
            print(f"   ✗ Failed to clear pattern {pattern}: {e}")
    
    print("\n" + "=" * 80)
    print("CACHE CLEAR COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Navigate to Diana's patient page in the browser")
    print("2. Django will fetch fresh data from Azure FHIR")
    print("3. Verify that Composition v6+ is loaded with medications section")
    print("4. Check Clinical Information tab for medication data")
    print("\nExpected Result:")
    print("✅ Composition versionId: 6 (or higher)")
    print("✅ Medications section present (LOINC: 10160-0)")
    print("✅ 5 MedicationStatement resources displayed")
    print("=" * 80)

if __name__ == "__main__":
    clear_diana_fhir_cache()
