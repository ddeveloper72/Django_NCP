#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientSession

def clear_session_cache():
    """Clear session cache to ensure updated service code is used"""
    
    # Get active sessions that might have cached data
    active_sessions = PatientSession.objects.filter(is_active=True)
    print(f"Found {active_sessions.count()} active sessions")
    
    # Force session data refresh by updating last_accessed
    updated_count = 0
    for session in active_sessions:
        # Touch the session to invalidate any cached comprehensive data
        session.save()  # This will update last_accessed
        updated_count += 1
        
    print(f"Refreshed {updated_count} sessions to clear cached data")
    print("✅ Session cache cleared - medication deduplication fix should now apply!")

if __name__ == "__main__":
    clear_session_cache()