#!/usr/bin/env python3
"""
Clear specific patient session to force fresh processing
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session

def clear_patient_session():
    """Clear patient session to force fresh processing"""
    
    # Clear all sessions containing our patient ID
    patient_id = "3056534594"
    sessions_cleared = 0
    
    for session in Session.objects.all():
        try:
            session_data = session.get_decoded()
            if f'patient_extended_data_{patient_id}' in session_data:
                print(f"🧹 Clearing session with patient data: {session.session_key}")
                session.delete()
                sessions_cleared += 1
        except Exception as e:
            print(f"⚠️  Error checking session {session.session_key}: {e}")
    
    if sessions_cleared > 0:
        print(f"✅ Cleared {sessions_cleared} sessions")
    else:
        print("ℹ️  No sessions found to clear")

if __name__ == "__main__":
    clear_patient_session()