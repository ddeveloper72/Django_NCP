#!/usr/bin/env python3
"""
Clear Diana's session data to force fresh medication extraction with updated active ingredient mappings
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone

print("=== CLEAR DIANA SESSION FOR FRESH EXTRACTION ===")
print()

# Find active sessions
now = timezone.now()
active_sessions = Session.objects.filter(expire_date__gt=now)

print(f"✅ Active sessions found: {len(active_sessions)}")
print()

sessions_cleared = 0
for session in active_sessions:
    try:
        session_data = session.get_decoded()
        
        # Look for Diana's session data
        patient_match_keys = [k for k in session_data.keys() if k.startswith('patient_match_2482633793')]
        
        if patient_match_keys:
            print(f"🎯 Found Diana's session: {session.session_key}")
            print(f"   Patient match keys: {patient_match_keys}")
            
            # Clear session data for fresh extraction
            for key in patient_match_keys:
                del session_data[key]
                print(f"   ✅ Cleared key: {key}")
            
            # Also clear any medication-related cache
            med_keys = [k for k in session_data.keys() if 'med' in k.lower()]
            for key in med_keys:
                del session_data[key]
                print(f"   ✅ Cleared medication key: {key}")
            
            # Save updated session
            for key, value in session_data.items():
                session.__setattr__(key, value)
            session.save()
            
            sessions_cleared += 1
            print(f"   ✅ Session cleared and saved")
            print()
            
    except Exception as e:
        print(f"❌ Error processing session {session.session_key}: {e}")
        print()

print(f"🎯 SUMMARY:")
print(f"   Sessions cleared: {sessions_cleared}")
print(f"   This will force fresh medication extraction with updated active ingredient mappings")
print()
print("=== READY FOR FRESH EXTRACTION ===")