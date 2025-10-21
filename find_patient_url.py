#!/usr/bin/env python
"""
Find Diana Ferreira's patient URL
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.contrib.sessions.models import Session

print("🔍 FINDING DIANA FERREIRA'S PATIENT URL")
print("=" * 50)

# Get session data
sessions = Session.objects.all().order_by('-expire_date')[:5]
for session in sessions:
    try:
        session_data = session.get_decoded()
        patient_matches = {k: v for k, v in session_data.items() if k.startswith('patient_match_')}
        
        for key, data in patient_matches.items():
            if isinstance(data, dict) and 'patient_id' in data:
                patient_id = data['patient_id']
                patient_url = f"http://127.0.0.1:8000/patient_data/{patient_id}/"
                print(f"✅ Patient URL: {patient_url}")
                
                # Also check if this has Diana's data
                if 'cda_content' in data:
                    print(f"   Session key: {session.session_key}")
                    print(f"   Data available: CDA content exists")
                    
    except Exception as e:
        print(f"Error: {e}")
        continue