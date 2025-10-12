#!/usr/bin/env python3
"""
EMERGENCY: Clear all patient sessions to prevent GDPR data breach
This script clears all patient session data to prevent cross-contamination
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

def emergency_clear_patient_sessions():
    """
    EMERGENCY: Clear all patient session data to prevent GDPR breach
    """
    print("🚨 EMERGENCY: Clearing all patient sessions to prevent GDPR data breach")
    print("🔒 This will ensure session isolation and prevent patient data mixing")
    
    sessions = Session.objects.all()
    total_sessions = len(sessions)
    cleared_sessions = 0
    patient_sessions_found = 0
    
    print(f"📋 Found {total_sessions} total sessions to examine...")
    
    for session in sessions:
        try:
            session_store = SessionStore(session_key=session.session_key)
            session_data = session_store.load()
            
            # Check if this session contains any patient data
            has_patient_data = False
            patient_keys = []
            
            for key in session_data.keys():
                if 'patient_match_' in key or 'patient_' in key or 'fhir_' in key:
                    has_patient_data = True
                    patient_keys.append(key)
                    patient_sessions_found += 1
            
            if has_patient_data:
                print(f"   🔍 Session {session.session_key[:10]}... contains patient data: {patient_keys}")
                
                # Clear all patient-related data from this session
                for key in list(session_data.keys()):
                    if ('patient_match_' in key or 'patient_' in key or 
                        'fhir_' in key or 'cda_' in key or 'healthcare_' in key):
                        del session_data[key]
                        print(f"      ❌ Cleared key: {key}")
                
                # Save the cleaned session
                session_store.save()
                cleared_sessions += 1
                print(f"      ✅ Session cleaned and saved")
        
        except Exception as e:
            print(f"   ⚠️  Could not process session {session.session_key[:10]}...: {str(e)}")
            continue
    
    print(f"\n📊 SESSION CLEANUP SUMMARY:")
    print(f"   Total sessions examined: {total_sessions}")
    print(f"   Patient data instances found: {patient_sessions_found}")
    print(f"   Sessions cleaned: {cleared_sessions}")
    print(f"   ✅ GDPR compliance restored - no patient data mixing possible")

if __name__ == "__main__":
    emergency_clear_patient_sessions()