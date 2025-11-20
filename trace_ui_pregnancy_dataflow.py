"""
Comprehensive trace: UI → View → Session → Parser → FHIR Resource
Simulates the exact path when viewing Diana's patient data
"""
import os
import sys
import django

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

import json
from django.contrib.sessions.backends.db import SessionStore
from patient_data.models import PatientSession

print("=" * 80)
print("TRACING UI → VIEW → SESSION → PARSER → FHIR")
print("=" * 80)

# Step 1: Find Diana's session
print("\n[STEP 1] Finding Diana's active sessions...")
print("-" * 80)

# Check PatientSession model
patient_sessions = PatientSession.objects.filter(
    country_code='PT',
    status='active'
).order_by('-created_at')

print(f"Found {patient_sessions.count()} active PatientSession records for Portugal")

for ps in patient_sessions:
    print(f"\n  Session ID: {ps.session_id}")
    print(f"  Created: {ps.created_at}")
    print(f"  User: {ps.user}")
    print(f"  Last Action: {ps.last_action}")
    
    # Try to decrypt patient data
    try:
        patient_data = ps.get_patient_data()
        if patient_data:
            print(f"  ✅ Successfully retrieved patient data")
            print(f"  Patient Name: {patient_data.get('patient_data', {}).get('name', 'Unknown')}")
            print(f"  Data Source: {patient_data.get('data_source', 'Unknown')}")
            print(f"  Has FHIR Bundle: {patient_data.get('fhir_bundle') is not None}")
            
            # THIS IS THE KEY: Check what's in the session
            if patient_data.get('fhir_bundle'):
                print(f"\n  [STEP 2] Session has FHIR bundle - parsing it...")
                print("-" * 80)
                
                from patient_data.services.fhir_bundle_parser import FHIRBundleParser
                
                parser = FHIRBundleParser()
                fhir_result = parser.parse_patient_summary_bundle(patient_data['fhir_bundle'])
                
                if fhir_result and isinstance(fhir_result, dict):
                    clinical_arrays = fhir_result.get('clinical_arrays', {})
                    pregnancy_history = clinical_arrays.get('pregnancy_history', [])
                    
                    print(f"\n  ✅ Parsed FHIR bundle successfully")
                    print(f"  Total pregnancy records: {len(pregnancy_history)}")
                    
                    past_pregnancies = [p for p in pregnancy_history if p.get('pregnancy_type') == 'past']
                    current_pregnancies = [p for p in pregnancy_history if p.get('pregnancy_type') == 'current']
                    
                    print(f"\n  📊 BREAKDOWN:")
                    print(f"     Past pregnancies: {len(past_pregnancies)}")
                    print(f"     Current pregnancies: {len(current_pregnancies)}")
                    
                    if past_pregnancies:
                        print(f"\n  📋 PAST PREGNANCY DETAILS:")
                        for i, preg in enumerate(past_pregnancies, 1):
                            print(f"\n     {i}. {preg.get('outcome', 'Unknown outcome')}")
                            print(f"        Delivery Date: {preg.get('delivery_date', 'Not specified')}")
                            print(f"        SNOMED Code: {preg.get('outcome_code', 'No code')}")
                            print(f"        Is Placeholder: {preg.get('_is_placeholder', False)}")
                            print(f"        Observation ID: {preg.get('observation_id', 'No ID')}")
                    
                    print(f"\n  🎯 THIS IS WHAT THE UI SHOULD DISPLAY!")
                    print(f"     Badge should show: '{len(past_pregnancies)} outcome(s)'")
                    
                else:
                    print("  ❌ Failed to parse FHIR bundle")
            
            elif patient_data.get('clinical_sections'):
                print(f"  ℹ️ Has clinical_sections (pre-parsed FHIR)")
                clinical_sections = patient_data.get('clinical_sections', [])
                pregnancy_section = next((s for s in clinical_sections if 'pregnancy' in s.get('code', '').lower()), None)
                if pregnancy_section:
                    print(f"  Found pregnancy section with {len(pregnancy_section.get('data', []))} records")
            else:
                print(f"  ⚠️ No FHIR bundle or clinical sections in session")
    except Exception as e:
        print(f"  ❌ Error retrieving patient data: {e}")
        import traceback
        print(f"  {traceback.format_exc()}")

# Step 3: Check Django sessions (fallback)
print(f"\n[STEP 3] Checking Django session storage...")
print("-" * 80)

from django.contrib.sessions.models import Session
from django.utils import timezone

active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
print(f"Found {active_sessions.count()} active Django sessions")

diana_sessions = []
for session in active_sessions:
    try:
        session_data = session.get_decoded()
        for key, value in session_data.items():
            if key.startswith('patient_match_'):
                if isinstance(value, dict):
                    patient_info = value.get('patient_data', {})
                    name = patient_info.get('name', '')
                    if 'Diana' in name or 'Ferreira' in name:
                        diana_sessions.append({
                            'session_id': key.replace('patient_match_', ''),
                            'session_key': session.session_key,
                            'data': value
                        })
                        print(f"\n  Found Diana's session: {key}")
                        print(f"  Session Key: {session.session_key}")
                        print(f"  Patient: {name}")
                        print(f"  Data Source: {value.get('data_source', 'CDA')}")
                        print(f"  Has FHIR Bundle: {value.get('fhir_bundle') is not None}")
    except Exception as e:
        continue

if diana_sessions:
    print(f"\n[STEP 4] Analyzing Diana's session data...")
    print("-" * 80)
    
    for ds in diana_sessions:
        session_data = ds['data']
        
        # Check if FHIR bundle exists
        if session_data.get('fhir_bundle'):
            print(f"\n  ✅ Session {ds['session_id']} has FHIR bundle")
            print(f"  Parsing it now...")
            
            from patient_data.services.fhir_bundle_parser import FHIRBundleParser
            
            parser = FHIRBundleParser()
            fhir_result = parser.parse_patient_summary_bundle(session_data['fhir_bundle'])
            
            if fhir_result and isinstance(fhir_result, dict):
                clinical_arrays = fhir_result.get('clinical_arrays', {})
                pregnancy_history = clinical_arrays.get('pregnancy_history', [])
                
                past_pregnancies = [p for p in pregnancy_history if p.get('pregnancy_type') == 'past']
                
                print(f"\n  📊 PARSING RESULT:")
                print(f"     Total pregnancy records: {len(pregnancy_history)}")
                print(f"     Past pregnancies: {len(past_pregnancies)}")
                print(f"     Current pregnancies: {len([p for p in pregnancy_history if p.get('pregnancy_type') == 'current'])}")
                
                if past_pregnancies:
                    print(f"\n  📋 PAST PREGNANCIES:")
                    for i, preg in enumerate(past_pregnancies, 1):
                        print(f"\n     {i}. {preg.get('outcome', 'Unknown')}")
                        print(f"        Date: {preg.get('delivery_date', 'Not specified')}")
                        print(f"        Code: {preg.get('outcome_code', 'No code')}")
                        print(f"        Placeholder: {preg.get('_is_placeholder', False)}")
        else:
            print(f"\n  ⚠️ Session {ds['session_id']} has NO FHIR bundle")
            print(f"     This session may be using CDA data")
else:
    print("\n  ❌ No Diana sessions found in Django session storage")

print("\n" + "=" * 80)
print("TRACE COMPLETE")
print("=" * 80)

print("\n💡 DIAGNOSIS:")
print("   1. Check if session has FHIR bundle")
print("   2. If yes, parser should create 3 past pregnancies")
print("   3. If UI shows 1, then:")
print("      a) Session is stale (has old data before code fix)")
print("      b) Django server needs restart to reload parser code")
print("      c) Browser is using cached session cookie")
print("\n   SOLUTION: Clear all sessions, restart Django, use incognito browser")
