#!/usr/bin/env python
"""
Clear Diana Ferreira session data to force re-parsing with updated parser
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from patient_data.models import PatientData

def clear_diana_sessions():
    """Clear all session data for Diana Ferreira patient"""
    
    print("\n" + "="*80)
    print("CLEARING DIANA FERREIRA SESSION DATA")
    print("="*80)
    
    # Find Diana Ferreira patient record
    try:
        diana = PatientData.objects.filter(
            given_name__icontains='Diana',
            family_name__icontains='Ferreira'
        ).first()
        
        if not diana:
            print("❌ Diana Ferreira patient record not found")
            return
        
        print(f"\n✅ Found Diana Ferreira: Patient ID {diana.id}")
        print(f"   Birth Date: {diana.birth_date}")
        print(f"   Gender: {diana.gender}")
        
    except Exception as e:
        print(f"❌ Error finding patient: {e}")
        return
    
    # Clear all sessions that might contain Diana's data
    cleared_count = 0
    session_keys_to_check = [
        f'patient_match_{diana.id}',
        f'patient_session_{diana.id}',
        f'fhir_bundle_{diana.id}',
        f'parsed_data_{diana.id}',
    ]
    
    print(f"\n🔍 Scanning all sessions for Diana's data...")
    
    for session in Session.objects.all():
        try:
            session_data = session.get_decoded()
            
            # Check if any Diana-related keys exist
            for key in session_keys_to_check:
                if key in session_data:
                    print(f"\n   Found session with key: {key}")
                    print(f"   Session Key: {session.session_key[:20]}...")
                    print(f"   Expiry: {session.expire_date}")
                    
                    # Delete this session
                    session.delete()
                    cleared_count += 1
                    print(f"   ✅ Session cleared!")
                    break
                    
        except Exception as e:
            # Skip invalid sessions
            continue
    
    if cleared_count == 0:
        print("\n   No active sessions found with Diana's data")
        print("   This means either:")
        print("   - Session expired naturally")
        print("   - No cached data exists")
        print("   - Fresh parse will happen on next visit")
    else:
        print(f"\n✅ Cleared {cleared_count} session(s)")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. ✅ Session data cleared - fresh parse will happen")
    print("2. 🔄 Restart Django server to load parser changes")
    print("3. 🌐 Navigate to Diana's patient page")
    print("4. 🔍 Healthcare Team tab should show new role/specialty")
    print("="*80 + "\n")

if __name__ == '__main__':
    clear_diana_sessions()
