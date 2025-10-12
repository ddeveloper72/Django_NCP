#!/usr/bin/env python3

import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session

def list_all_sessions():
    """List all available sessions with patient info"""
    
    print("=== Available Sessions ===\n")
    
    active_sessions = Session.objects.all()
    print(f"Total sessions: {active_sessions.count()}")
    
    for i, session in enumerate(active_sessions, 1):
        session_data = session.get_decoded()
        print(f"\nSession {i}: {session.session_key}")
        
        # Check patient identity
        patient_identity = session_data.get('patient_identity', {})
        if patient_identity:
            given_name = patient_identity.get('given_name', '')
            family_name = patient_identity.get('family_name', '')
            print(f"  Patient: {given_name} {family_name}")
        
        # Check if FHIR bundle exists
        has_fhir = 'fhir_bundle_data' in session_data
        print(f"  FHIR Bundle: {'Yes' if has_fhir else 'No'}")
        
        if has_fhir:
            print(f"  ✅ Can test this session")
        else:
            print(f"  ❌ No FHIR data")

if __name__ == "__main__":
    list_all_sessions()