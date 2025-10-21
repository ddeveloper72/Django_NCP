#!/usr/bin/env python3
"""
Find Active Session with Patient Data
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.insert(0, '/c/Users/Duncan/VS_Code_Projects/django_ncp')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
import json


def find_active_sessions():
    """Find sessions with patient data"""
    print("Finding Active Sessions with Patient Data")
    print("=========================================")
    
    sessions = Session.objects.all()
    print(f"Total sessions: {sessions.count()}")
    
    active_sessions = []
    
    for session in sessions:
        try:
            session_data = session.get_decoded()
            
            # Look for patient_match keys
            patient_matches = {k: v for k, v in session_data.items() if k.startswith('patient_match_')}
            
            if patient_matches:
                print(f"\nSession: {session.session_key}")
                print(f"  Patient matches: {list(patient_matches.keys())}")
                active_sessions.append((session.session_key, list(patient_matches.keys())))
                
                # Check if one has Diana (our target patient)
                for key, data in patient_matches.items():
                    if isinstance(data, dict) and 'patient_data' in data:
                        patient = data['patient_data']
                        patient_name = patient.get('name', {}).get('family', [''])[0] if isinstance(patient.get('name'), list) and patient.get('name') else ''
                        if not patient_name and isinstance(patient.get('name'), dict):
                            patient_name = patient.get('name', {}).get('family', '')
                        print(f"    {key}: {patient_name}")
                        
                        if 'diana' in patient_name.lower() or 'ferreira' in patient_name.lower():
                            print(f"    *** FOUND DIANA! Session: {session.session_key}, Key: {key}")
        except Exception as e:
            print(f"Error processing session {session.session_key}: {e}")
    
    return active_sessions


def check_specific_session():
    """Check the specific session from working scripts"""
    # Try the session ID that debug_context_building uses
    potential_session_keys = [
        "jadihambq3ncjf8dmk9fcwgknnxn60ik",  # From web interface
        "3112437329",  # From debug scripts
    ]
    
    print("\nChecking Specific Sessions:")
    print("==========================")
    
    for session_key in potential_session_keys:
        try:
            session = Session.objects.get(session_key=session_key)
            session_data = session.get_decoded()
            
            patient_matches = {k: v for k, v in session_data.items() if k.startswith('patient_match_')}
            
            print(f"\nSession {session_key}:")
            if patient_matches:
                print(f"  Patient matches: {list(patient_matches.keys())}")
            else:
                print("  No patient matches")
                
        except Session.DoesNotExist:
            print(f"\nSession {session_key}: Does not exist")


if __name__ == "__main__":
    active_sessions = find_active_sessions()
    check_specific_session()
    
    if active_sessions:
        print(f"\nFound {len(active_sessions)} sessions with patient data")
        print("Use any of these session keys for debugging:")
        for session_key, patient_keys in active_sessions:
            print(f"  Session: {session_key}")
            for patient_key in patient_keys:
                print(f"    - {patient_key}")
    else:
        print("\nNo sessions with patient data found")