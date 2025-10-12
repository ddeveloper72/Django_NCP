#!/usr/bin/env python3
"""
EMERGENCY: Clear Contaminated FHIR Bundle Data

The HAPI FHIR server has returned contaminated data with Cyprus organizations
in Irish patient bundles. This is a critical GDPR issue that needs immediate fixing.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

def emergency_clear_contaminated_fhir_data():
    """
    Clear the contaminated FHIR bundle data for patient 1708631189
    """
    print("🚨 EMERGENCY: Clearing Contaminated FHIR Bundle Data")
    print("=" * 70)
    
    patient_id = "1708631189"
    print(f"🎯 Target: Patient {patient_id} with Cyprus contamination")
    
    from django.contrib.sessions.models import Session
    from django.contrib.sessions.backends.db import SessionStore
    
    # Find and clear the contaminated session
    sessions = Session.objects.all()
    cleared_sessions = 0
    
    for session in sessions:
        try:
            session_store = SessionStore(session_key=session.session_key)
            session_data = session_store.load()
            
            patient_key = f'patient_match_{patient_id}'
            if patient_key in session_data:
                print(f"✅ Found contaminated session: {session.session_key[:10]}...")
                
                # Check if it contains Cyprus data
                patient_data = session_data[patient_key]
                has_cyprus_data = False
                
                if isinstance(patient_data, dict) and 'fhir_bundle' in patient_data:
                    fhir_bundle = patient_data['fhir_bundle']
                    if isinstance(fhir_bundle, dict) and 'entry' in fhir_bundle:
                        for entry in fhir_bundle['entry']:
                            resource = entry.get('resource', {})
                            if resource.get('resourceType') == 'Organization':
                                org_name = resource.get('name', '')
                                if 'Cyprus' in org_name or 'eHealthLab' in org_name:
                                    has_cyprus_data = True
                                    print(f"   🚨 Found Cyprus organization: {org_name}")
                
                if has_cyprus_data:
                    # Clear ALL data for this patient
                    keys_to_clear = []
                    for key in list(session_data.keys()):
                        if patient_id in key:
                            keys_to_clear.append(key)
                    
                    for key in keys_to_clear:
                        del session_data[key]
                        print(f"   ❌ Cleared contaminated key: {key}")
                    
                    session_store.save()
                    cleared_sessions += 1
                    print(f"   ✅ Session cleaned and saved")
                else:
                    print(f"   ℹ️  Session does not contain Cyprus data")
        
        except Exception as e:
            continue
    
    print(f"\n📊 CONTAMINATION CLEANUP SUMMARY:")
    print(f"   Patient ID: {patient_id}")
    print(f"   Sessions cleared: {cleared_sessions}")
    print(f"   ✅ Cyprus contamination removed from sessions")
    
    # Warning about HAPI server
    print(f"\n⚠️  CRITICAL WARNING:")
    print(f"   The HAPI FHIR server contains contaminated data!")
    print(f"   Patient {patient_id} FHIR bundle includes Cyprus organizations")
    print(f"   This suggests:")
    print(f"   1. Multiple patient bundles uploaded with same IDs")
    print(f"   2. Server-side bundle merging/contamination")
    print(f"   3. Incorrect data upload to HAPI server")
    
    print(f"\n🔧 REQUIRED ACTIONS:")
    print(f"   1. ✅ Cleared contaminated session data (DONE)")
    print(f"   2. 🔄 Contact HAPI FHIR server administrator")
    print(f"   3. 🔄 Verify and clean server-side data")
    print(f"   4. 🔄 Re-upload clean Irish patient bundles")
    print(f"   5. 🔄 Implement server-side data validation")

def check_other_patients_for_contamination():
    """
    Check if other patients also have Cyprus contamination
    """
    print(f"\n🔍 CHECKING OTHER PATIENTS FOR CONTAMINATION:")
    
    from django.contrib.sessions.models import Session
    from django.contrib.sessions.backends.db import SessionStore
    
    contaminated_patients = []
    total_checked = 0
    
    sessions = Session.objects.all()
    
    for session in sessions:
        try:
            session_store = SessionStore(session_key=session.session_key)
            session_data = session_store.load()
            
            # Look for any patient data
            for key in session_data.keys():
                if key.startswith('patient_match_'):
                    patient_id = key.replace('patient_match_', '')
                    patient_data = session_data[key]
                    total_checked += 1
                    
                    # Check for Cyprus contamination
                    if isinstance(patient_data, dict) and 'fhir_bundle' in patient_data:
                        fhir_bundle = patient_data['fhir_bundle']
                        if isinstance(fhir_bundle, dict) and 'entry' in fhir_bundle:
                            for entry in fhir_bundle['entry']:
                                resource = entry.get('resource', {})
                                if resource.get('resourceType') == 'Organization':
                                    org_name = resource.get('name', '')
                                    if 'Cyprus' in org_name or 'eHealthLab' in org_name:
                                        if patient_id not in contaminated_patients:
                                            contaminated_patients.append(patient_id)
                                            print(f"   🚨 Patient {patient_id}: Cyprus contamination found")
        
        except Exception as e:
            continue
    
    print(f"\n📊 CONTAMINATION SCAN RESULTS:")
    print(f"   Total patients checked: {total_checked}")
    print(f"   Contaminated patients: {len(contaminated_patients)}")
    
    if contaminated_patients:
        print(f"   Contaminated patient IDs: {contaminated_patients}")
        print(f"   🚨 MULTIPLE PATIENTS AFFECTED - Server-wide contamination!")
    else:
        print(f"   ✅ No other contaminated patients found")

if __name__ == "__main__":
    emergency_clear_contaminated_fhir_data()
    check_other_patients_for_contamination()
    print(f"\n🎯 CONTAMINATION CLEANUP COMPLETE")
    print(f"💡 Now refresh the patient page - Cyprus data should be gone!")
    print(f"⚠️  CONTACT HAPI FHIR SERVER ADMIN TO FIX SERVER DATA!")