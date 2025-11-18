"""
Force delete Diana's patient session to clear cached data
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from patient_data.models import PatientSession, PatientDataCache
from django.contrib.sessions.models import Session

def main():
    print("\n=== CLEARING PATIENT SESSIONS ===\n")
    
    # Find all sessions
    patient_sessions = PatientSession.objects.all()
    print(f"Found {patient_sessions.count()} patient sessions")
    
    if patient_sessions.exists():
        for session in patient_sessions:
            session_id = session.session_id
            user = session.user.username if session.user else "Unknown"
            print(f"  - Session {session_id[:16]}... (User: {user})")
        
        # Delete all patient sessions
        count = patient_sessions.count()
        patient_sessions.delete()
        print(f"\nDeleted {count} patient session(s)")
    
    # Clear patient data cache
    cache_entries = PatientDataCache.objects.all()
    if cache_entries.exists():
        count = cache_entries.count()
        cache_entries.delete()
        print(f"Deleted {count} cached data entries")
    
    # Clear Django sessions
    django_sessions = Session.objects.all()
    if django_sessions.exists():
        count = django_sessions.count()
        django_sessions.delete()
        print(f"Deleted {count} Django session(s)")
    
    print("\n✅ All sessions and cached data cleared!")
    print("Please log in again and search for the patient.")

if __name__ == '__main__':
    main()
