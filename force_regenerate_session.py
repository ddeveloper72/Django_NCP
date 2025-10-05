#!/usr/bin/env python3

import sys
import os

# Add the Django project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')

import django
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
import json

def force_regenerate_session_data():
    """Force regeneration of session data for Diana Ferreira"""
    print("🔄 FORCING SESSION DATA REGENERATION")
    print("=" * 80)
    
    patient_id = "3056534594"
    session_key = f'patient_extended_data_{patient_id}'
    
    # Find the session
    sessions = Session.objects.all()
    target_session = None
    
    for session in sessions:
        try:
            session_data = session.get_decoded()
            if session_key in session_data:
                target_session = session
                break
        except:
            continue
    
    if not target_session:
        print("❌ No session found for Diana Ferreira")
        return
    
    print(f"✅ Found session: {target_session.session_key}")
    
    # Delete the extended data to force regeneration
    session_data = target_session.get_decoded()
    if session_key in session_data:
        print(f"🗑️ Deleting existing extended data...")
        del session_data[session_key]
        
        # Save the modified session
        session_store = SessionStore(session_key=target_session.session_key)
        session_store.update(session_data)
        session_store.save()
        
        print("✅ Session data cleared - will regenerate on next request")
    else:
        print("❌ No extended data found in session")

if __name__ == "__main__":
    force_regenerate_session_data()